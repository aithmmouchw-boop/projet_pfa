"""Vues espace patient."""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, ListView, TemplateView

from clinic_common.visual_assets import attach_medecin_visuals
from facturation.models import Facture
from medecins.models import Medecin
from patients.forms import PatientOnboardingForm, RdvMotifForm
from patients.mixins import PatientAccountMixin
from patients.models import Patient
from patients.utils import generer_num_dossier
from rendez_vous.models import RendezVous
from rendez_vous.services import creneau_est_occupe, creneaux_jour, prochains_jours


def _normalise_slot_iso(slot_raw: str | None) -> str | None:
    if not slot_raw:
        return None
    slot = slot_raw.strip()
    if (
        len(slot) >= 6
        and slot[-6] == " "
        and slot[-5:-3].isdigit()
        and slot[-3] == ":"
        and slot[-2:].isdigit()
    ):
        return f"{slot[:-6]}+{slot[-5:]}"
    return slot


def _rdv_booking_url(
    medecin_id: str | int | None = None,
    slot_iso: str | None = None,
) -> str:
    query = {}
    if medecin_id:
        query["medecin"] = medecin_id
    slot_iso = _normalise_slot_iso(slot_iso)
    if slot_iso:
        query["slot"] = slot_iso
    base_url = reverse("patients:rdv_nouveau")
    return f"{base_url}?{urlencode(query)}" if query else base_url


def _shell(request, intro: str) -> dict[str, Any]:
    u = request.user
    return {
        "clinic": SimpleNamespace(name="CLINOVA"),
        "user_display": (u.get_full_name() or "").strip() or u.email,
        "dashboard_intro": intro,
    }


def _patient_nav() -> list[tuple[str, str | None, str]]:
    return [
        ("patients:patient_dashboard", None, "Vue d'ensemble"),
        ("patients:rdv_list", None, "Mes rendez-vous"),
        ("patients:rdv_nouveau", None, "Prendre un RDV"),
        ("patients:dossier", None, "Mon dossier"),
        ("patients:factures", None, "Mes factures"),
    ]


def _nav(active_label: str) -> list[dict[str, Any]]:
    out = []
    for name, frag, label in _patient_nav():
        out.append(
            {
                "label": label,
                "url_name": name,
                "fragment": frag,
                "active": label == active_label,
            }
        )
    return out


class PatientOnboardingView(LoginRequiredMixin, FormView):
    template_name = "patient/onboarding.html"
    form_class = PatientOnboardingForm
    success_url = reverse_lazy("patients:patient_dashboard")

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if getattr(request.user, "role", None) != "patient":
            return redirect(reverse("landing"))
        if Patient.objects.filter(user=request.user).exists():
            return redirect(reverse("patients:patient_dashboard"))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        Patient.objects.create(
            user=self.request.user,
            num_dossier=generer_num_dossier(),
            date_naissance=form.cleaned_data["date_naissance"],
            telephone=form.cleaned_data.get("telephone", ""),
            adresse=form.cleaned_data.get("adresse", ""),
        )
        messages.success(self.request, "Votre profil patient a été créé.")
        return super().form_valid(form)


class PatientDashboardView(PatientAccountMixin, TemplateView):
    template_name = "patient/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patient: Patient = self.request.patient_profile  # type: ignore[attr-defined]
        consultations = patient.consultations.select_related(
            "medecin__user"
        ).prefetch_related("ordonnance__lignes").order_by("-updated_at", "-date")
        risk_stats = {
            "faible": consultations.filter(risk_level="faible").count(),
            "moyen": consultations.filter(risk_level="moyen").count(),
            "eleve": consultations.filter(risk_level="eleve").count(),
            "latest": consultations.first(),
        }
        now = timezone.now()
        next_rdv = (
            patient.rendez_vous.filter(
                statut__in=[
                    RendezVous.Statut.PLANIFIE,
                    RendezVous.Statut.CONFIRME,
                ],
                date_heure__gte=now,
            )
            .select_related("medecin__user")
            .order_by("date_heure")
            .first()
        )
        impayees = patient.factures.filter(statut=Facture.Statut.EMISE).count()
        ctx.update(
            {
                "role_key": "patient",
                "role_title": "Patient",
                "dashboard_nav": _nav("Vue d'ensemble"),
                "patient": patient,
                "next_rdv": next_rdv,
                "now": now,
                "stats": {
                    "rdv_total": patient.rendez_vous.count(),
                    "consultations": patient.consultations.count(),
                    "factures_impayees": impayees,
                },
                "recent_consultations": patient.consultations.select_related(
                    "medecin__user"
                ).order_by("-updated_at", "-date")[:3],
            }
        )
        ctx.update(
            _shell(
                self.request,
                "Votre espace patient : rendez-vous, dossier et factures.",
            )
        )
        return ctx


class RdvListView(PatientAccountMixin, ListView):
    template_name = "patient/rdv_list.html"
    context_object_name = "rendez_vous"

    def get_queryset(self):
        return self.request.patient_profile.rendez_vous.select_related("medecin__user").order_by(  # type: ignore[attr-defined]
            "-date_heure"
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["role_key"] = "patient"
        ctx["role_title"] = "Patient"
        ctx["clinic"] = None
        ctx["dashboard_nav"] = _nav("Mes rendez-vous")
        ctx.update(_shell(self.request, "Vos rendez-vous planifiés et passés."))
        return ctx


class RdvBookingView(PatientAccountMixin, TemplateView):
    template_name = "patient/rdv_nouveau.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        medecin_id = self.request.GET.get("medecin") or self.request.GET.get("doctor")
        slot_iso = _normalise_slot_iso(self.request.GET.get("slot"))
        search_query = (self.request.GET.get("q") or "").strip()
        selected_specialite = (self.request.GET.get("specialite") or "").strip()
        medecins = Medecin.objects.filter(actif=True).select_related("user")
        if selected_specialite:
            medecins = medecins.filter(specialite__iexact=selected_specialite)
        if search_query:
            medecins = medecins.filter(
                Q(specialite__icontains=search_query)
                | Q(user__first_name__icontains=search_query)
                | Q(user__last_name__icontains=search_query)
                | Q(user__email__icontains=search_query)
            )
        medecins = medecins.order_by("specialite", "user__last_name", "user__first_name")
        medecins = attach_medecin_visuals(medecins)
        medecin = None
        jours: list[dict[str, Any]] = []
        if medecin_id:
            medecin = get_object_or_404(Medecin, pk=medecin_id, actif=True)
            attach_medecin_visuals([medecin])
            for jour in prochains_jours(14):
                jours.append(
                    {
                        "date": jour,
                        "slots": creneaux_jour(medecin, jour),
                    }
                )
        ctx.update(
            {
                "role_key": "patient",
                "role_title": "Patient",
                "dashboard_nav": _nav("Prendre un RDV"),
                "medecins": medecins,
                "specialites": Medecin.objects.filter(actif=True)
                .order_by("specialite")
                .values_list("specialite", flat=True)
                .distinct(),
                "search_query": search_query,
                "selected_specialite": selected_specialite,
                "medecin": medecin,
                "jours": jours,
                "slot_iso": slot_iso,
                "motif_form": RdvMotifForm(),
            }
        )
        ctx.update(_shell(self.request, "Choisissez un praticien, un créneau, puis confirmez."))
        return ctx

    def post(self, request, *args, **kwargs):
        if "medecin_id" in request.POST and "slot_iso" not in request.POST:
            mid = request.POST.get("medecin_id")
            return redirect(_rdv_booking_url(mid))
        if "slot_iso" in request.POST and "motif" not in request.POST:
            mid = request.POST.get("medecin_id")
            slot = request.POST.get("slot_iso")
            return redirect(_rdv_booking_url(mid, slot))
        form = RdvMotifForm(request.POST)
        if not form.is_valid():
            messages.error(request, "Vérifiez le motif de consultation.")
            mid = request.POST.get("medecin_id")
            slot = request.POST.get("slot_iso")
            return redirect(_rdv_booking_url(mid, slot))
        patient = request.patient_profile  # type: ignore[attr-defined]
        medecin = get_object_or_404(
            Medecin, pk=request.POST.get("medecin_id"), actif=True
        )
        slot_raw = _normalise_slot_iso(request.POST.get("slot_iso"))
        try:
            dt = datetime.fromisoformat(slot_raw or "")
        except ValueError:
            messages.error(request, "Le creneau choisi est invalide. Merci de le choisir a nouveau.")
            return redirect(_rdv_booking_url(medecin.pk))
        if timezone.is_naive(dt):
            dt = timezone.make_aware(dt, timezone.get_current_timezone())
        if creneau_est_occupe(medecin, dt):
            messages.error(
                request,
                "Ce creneau est deja pris. Choisissez un autre horaire.",
            )
            return redirect(_rdv_booking_url(medecin.pk))
        rdv = RendezVous.objects.create(
            patient=patient,
            medecin=medecin,
            date_heure=dt,
            motif=form.cleaned_data["motif"],
            statut=RendezVous.Statut.PLANIFIE,
        )
        messages.success(request, "Votre rendez-vous a été enregistré.")
        return redirect("patients:rdv_success", pk=rdv.pk)


class RdvSuccessView(PatientAccountMixin, TemplateView):
    template_name = "patient/rdv_success.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rdv = get_object_or_404(
            RendezVous,
            pk=self.kwargs["pk"],
            patient=self.request.patient_profile,  # type: ignore[attr-defined]
        )
        ctx.update(
            {
                "role_key": "patient",
                "role_title": "Patient",
                "dashboard_nav": _nav("Mes rendez-vous"),
                "rdv": rdv,
            }
        )
        ctx.update(_shell(self.request, "Confirmation de votre demande."))
        return ctx


class RdvAnnulerView(PatientAccountMixin, View):
    def post(self, request, pk):
        rdv = get_object_or_404(
            RendezVous,
            pk=pk,
            patient=request.patient_profile,  # type: ignore[attr-defined]
        )
        if rdv.statut in (
            RendezVous.Statut.PLANIFIE,
            RendezVous.Statut.CONFIRME,
        ):
            rdv.statut = RendezVous.Statut.ANNULE
            rdv.save()
            messages.success(request, "Le rendez-vous a été annulé.")
        else:
            messages.warning(
                request,
                "Ce rendez-vous ne peut plus être annulé depuis l’espace patient.",
            )
        return redirect(reverse("patients:rdv_list"))


class DossierView(PatientAccountMixin, TemplateView):
    template_name = "patient/dossier.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patient: Patient = self.request.patient_profile  # type: ignore[attr-defined]
        consultations = patient.consultations.select_related(
            "medecin__user"
        ).prefetch_related("ordonnance__lignes").order_by("-updated_at", "-date")
        risk_stats = {
            "faible": consultations.filter(risk_level="faible").count(),
            "moyen": consultations.filter(risk_level="moyen").count(),
            "eleve": consultations.filter(risk_level="eleve").count(),
            "latest": consultations.first(),
        }
        ctx.update(
            {
                "role_key": "patient",
                "role_title": "Patient",
                "dashboard_nav": _nav("Mon dossier"),
                "dossier": patient.dossier,
                "patient": patient,
                "risk_stats": risk_stats,
                "consultations_passees": consultations[:20],
            }
        )
        ctx.update(_shell(self.request, "Consultation securisee de votre dossier medical."))
        return ctx


class FacturesListView(PatientAccountMixin, ListView):
    template_name = "patient/factures.html"
    context_object_name = "factures"

    def get_queryset(self):
        return self.request.patient_profile.factures.select_related(  # type: ignore[attr-defined]
            "consultation__medecin__user"
        ).order_by("-created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["role_key"] = "patient"
        ctx["role_title"] = "Patient"
        ctx["dashboard_nav"] = _nav("Mes factures")
        ctx.update(_shell(self.request, "Vos factures et leur statut."))
        return ctx


class PatientFactureDetailView(PatientAccountMixin, TemplateView):
    template_name = "patient/facture_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        facture = get_object_or_404(
            self.request.patient_profile.factures.select_related(  # type: ignore[attr-defined]
                "patient__user",
                "consultation__medecin__user",
            ).prefetch_related("lignes", "paiements"),
            pk=self.kwargs["pk"],
        )
        ctx.update(
            {
                "role_key": "patient",
                "role_title": "Patient",
                "dashboard_nav": _nav("Mes factures"),
                "facture": facture,
                "latest_payment": facture.paiements.filter(valide=True).first(),
                "print_now": self.request.GET.get("print") == "1",
            }
        )
        ctx.update(_shell(self.request, "Consultation et impression securisees de votre facture."))
        return ctx
