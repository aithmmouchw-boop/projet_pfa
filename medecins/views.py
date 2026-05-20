from datetime import date, timedelta

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from clinic_common.audit import log_activity
from clinic_common.models import SystemActivity
from consultations.models import Consultation, Ordonnance
from facturation.models import Facture, LigneFacture
from facturation.utils import next_facture_numero
from medecins.forms import ConsultationMedecinForm, LigneOrdonnanceFormSet
from medecins.mixins import MedecinAccountMixin
from rendez_vous.models import RendezVous


def _nav_med(active: str) -> list[dict]:
    return [
        {
            "label": "Vue d'ensemble",
            "url_name": "medecins:medecin_dashboard",
            "fragment": None,
            "active": active == "Vue d'ensemble",
        },
    ]


def _shell(request, intro: str) -> dict:
    from types import SimpleNamespace

    u = request.user
    return {
        "clinic": SimpleNamespace(name="CLINOVA"),
        "user_display": (u.get_full_name() or "").strip() or u.email,
        "dashboard_intro": intro,
    }


def _creer_facture_consultation(consultation: Consultation):
    facture = Facture.objects.filter(consultation=consultation).first()
    if facture:
        return facture, False
    med = consultation.medecin
    facture = Facture.objects.create(
        consultation=consultation,
        patient=consultation.patient,
        numero=next_facture_numero(),
        statut=Facture.Statut.BROUILLON,
    )
    LigneFacture.objects.create(
        facture=facture,
        libelle=f"Consultation - Dr. {med.user.get_full_name() or med.user.email}",
        quantite=1,
        prix_unitaire=med.tarif_consultation,
    )
    facture.calculer_total()
    return facture, True


class MedecinDashboardView(MedecinAccountMixin, TemplateView):
    template_name = "medecin/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        med = self.request.medecin_profile  # type: ignore[attr-defined]
        consultations = (
            Consultation.objects.filter(
                medecin=med,
                termine=False,
            )
            .select_related("patient__user", "rendez_vous")
            .order_by("rendez_vous__date_heure")
        )
        historique_patients = (
            Consultation.objects.filter(medecin=med, termine=True)
            .select_related("patient__user", "rendez_vous")
            .order_by("-updated_at", "-date")[:12]
        )
        ctx.update(
            {
                "role_key": "medecin",
                "role_title": "Medecin",
                "dashboard_nav": _nav_med("Vue d'ensemble"),
                "consultations_today": consultations,
                "consultations_waiting_count": consultations.count(),
                "historique_patients": historique_patients,
            }
        )
        ctx.update(_shell(self.request, "File des patients et consultations ouvertes."))
        return ctx


class ConsultationTerminerRapideView(MedecinAccountMixin, View):
    def post(self, request, pk):
        consultation = get_object_or_404(
            Consultation.objects.select_related(
                "patient__user", "medecin__user", "rendez_vous"
            ),
            pk=pk,
            medecin=request.medecin_profile,
            termine=False,
        )
        with transaction.atomic():
            consultation.termine = True
            consultation.save(update_fields=["termine"])
            rdv = consultation.rendez_vous
            rdv.statut = RendezVous.Statut.TERMINE
            rdv.save(update_fields=["statut"])
            facture, created = _creer_facture_consultation(consultation)
        log_activity(
            action=SystemActivity.Action.CONSULTATION_FINISHED,
            description="Consultation terminee depuis le dashboard medecin",
            request=request,
            metadata={
                "consultation_id": consultation.pk,
                "facture_id": facture.pk,
                "facture_created": created,
            },
        )
        messages.success(request, "Consultation terminee et facture ajoutee chez le caissier.")
        return redirect(reverse("medecins:medecin_dashboard"))


class ConsultationDetailView(MedecinAccountMixin, TemplateView):
    template_name = "medecin/consultation.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or getattr(request.user, "role", None) != "medecin":
            return super().dispatch(request, *args, **kwargs)
        try:
            request.medecin_profile = request.user.medecin_profile
        except Exception:
            return super().dispatch(request, *args, **kwargs)
        self.consultation = get_object_or_404(
            Consultation.objects.select_related(
                "patient__user", "dossier", "rendez_vous", "medecin__user"
            ),
            pk=kwargs["pk"],
            medecin=request.medecin_profile,
        )
        self.ordonnance, _ = Ordonnance.objects.get_or_create(
            consultation=self.consultation,
            defaults={"valide_jusqu": date.today() + timedelta(days=90)},
        )
        return super(MedecinAccountMixin, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        patient = self.consultation.patient
        form = kwargs.get("form") or ConsultationMedecinForm(
            instance=self.consultation,
            specialite=self.consultation.medecin.specialite,
        )
        formset = kwargs.get("formset") or LigneOrdonnanceFormSet(
            instance=self.ordonnance
        )
        ctx.update(
            {
                "role_key": "medecin",
                "role_title": "Medecin",
                "dashboard_nav": _nav_med("Vue d'ensemble"),
                "consultation": self.consultation,
                "patient": patient,
                "dossier": patient.dossier,
                "ordonnance": self.ordonnance,
                "form": form,
                "formset": formset,
                "historique": patient.consultations.filter(
                    medecin=self.request.medecin_profile,
                    termine=True,
                )
                .exclude(pk=self.consultation.pk)
                .select_related("medecin__user")
                .order_by("-updated_at", "-date")[:10],
            }
        )
        ctx.update(_shell(self.request, "Saisie clinique et ordonnance."))
        return ctx

    def post(self, request, *args, **kwargs):
        form = ConsultationMedecinForm(
            request.POST,
            instance=self.consultation,
            specialite=self.consultation.medecin.specialite,
        )
        formset = LigneOrdonnanceFormSet(request.POST, instance=self.ordonnance)
        if not form.is_valid() or not formset.is_valid():
            ctx = self.get_context_data(form=form, formset=formset)
            return render(request, self.template_name, ctx)
        with transaction.atomic():
            form.save()
            formset.instance = self.ordonnance
            formset.save()
            self.consultation.termine = True
            self.consultation.save(update_fields=["termine"])
            rdv = self.consultation.rendez_vous
            rdv.statut = RendezVous.Statut.TERMINE
            rdv.save(update_fields=["statut"])
            facture, created = _creer_facture_consultation(self.consultation)
        log_activity(
            action=SystemActivity.Action.CONSULTATION_FINISHED,
            description="Consultation terminee depuis la fiche medecin",
            request=request,
            metadata={
                "consultation_id": self.consultation.pk,
                "facture_id": facture.pk,
                "facture_created": created,
            },
        )
        messages.success(
            self.request, "Consultation terminee et facture brouillon creee."
        )
        return redirect(reverse("medecins:medecin_dashboard"))
