from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import FormView, TemplateView

from clinic_common.mixins import RoleRequiredMixin
from consultations.models import Consultation
from medecins.models import Medecin
from rendez_vous.models import RendezVous
from rendez_vous.services import ensure_consultation_for_rdv
from secretaire.forms import ConstantesForm


def _nav_sec(active: str) -> list[dict]:
    items = [
        ("secretaire:secretaire_dashboard", "Vue d'ensemble"),
    ]
    return [
        {"label": lab, "url_name": u, "fragment": None, "active": lab == active}
        for u, lab in items
    ]


def _shell(request, intro: str) -> dict:
    from types import SimpleNamespace

    u = request.user
    return {
        "clinic": SimpleNamespace(name="CLINOVA"),
        "user_display": (u.get_full_name() or "").strip() or u.email,
        "dashboard_intro": intro,
    }


def _dashboard_url(medecin_id: str | int | None = None) -> str:
    url = reverse("secretaire:secretaire_dashboard")
    return f"{url}?medecin={medecin_id}" if medecin_id else url


class SecretaireDashboardView(RoleRequiredMixin, TemplateView):
    required_role = "infirmier"
    template_name = "secretaire/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        selected_medecin_id = (self.request.GET.get("medecin") or "").strip()
        medecins = list(
            Medecin.objects.filter(actif=True)
            .select_related("user")
            .annotate(
                rdv_total=Count("rendez_vous", distinct=True),
                rdv_a_preparer=Count(
                    "rendez_vous",
                    filter=Q(
                        rendez_vous__statut__in=[
                            RendezVous.Statut.PLANIFIE,
                            RendezVous.Statut.CONFIRME,
                            RendezVous.Statut.ARRIVE,
                            RendezVous.Statut.EN_COURS,
                        ]
                    ),
                    distinct=True,
                ),
            )
            .order_by("specialite", "user__last_name", "user__first_name")
        )

        selected_medecin = None
        rdvs_query = RendezVous.objects.select_related(
            "patient__user",
            "medecin__user",
            "consultation",
        )
        if selected_medecin_id:
            selected_medecin = get_object_or_404(
                Medecin.objects.select_related("user"),
                pk=selected_medecin_id,
                actif=True,
            )
            rdvs_query = rdvs_query.filter(medecin=selected_medecin)

        rdvs = list(rdvs_query.order_by("-date_heure")[:80])
        for rdv in rdvs:
            try:
                rdv.consultation_obj = rdv.consultation
            except Consultation.DoesNotExist:
                rdv.consultation_obj = None
            rdv.can_mark_arrived = rdv.statut in (
                RendezVous.Statut.PLANIFIE,
                RendezVous.Statut.CONFIRME,
            )
            rdv.can_saisir_constantes = rdv.statut in (
                RendezVous.Statut.ARRIVE,
                RendezVous.Statut.EN_COURS,
            )

        ctx.update(
            {
                "role_key": "secretaire",
                "role_title": "Secretaire",
                "dashboard_nav": _nav_sec("Vue d'ensemble"),
                "medecins": medecins,
                "selected_medecin": selected_medecin,
                "selected_medecin_id": selected_medecin_id,
                "rdvs_today": rdvs,
            }
        )
        ctx.update(_shell(self.request, "Choix du medecin, arrivees et saisie des constantes."))
        return ctx


class RdvMarquerArriveView(RoleRequiredMixin, View):
    required_role = "infirmier"

    def post(self, request, pk):
        rdv = get_object_or_404(RendezVous, pk=pk)
        if rdv.statut in (
            RendezVous.Statut.PLANIFIE,
            RendezVous.Statut.CONFIRME,
        ):
            rdv.statut = RendezVous.Statut.ARRIVE
            rdv.save(update_fields=["statut"])
            ensure_consultation_for_rdv(rdv)
            messages.success(request, "Patient marque comme arrive.")
        else:
            messages.warning(request, "Statut incompatible pour cette action.")
        return redirect(_dashboard_url(request.GET.get("medecin") or rdv.medecin_id))


class RdvConstantesView(RoleRequiredMixin, FormView):
    required_role = "infirmier"
    form_class = ConstantesForm
    template_name = "secretaire/constantes.html"

    def dispatch(self, request, *args, **kwargs):
        self.rdv = get_object_or_404(RendezVous, pk=kwargs["pk"])
        self.consultation, _ = ensure_consultation_for_rdv(self.rdv)
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["instance"] = self.consultation
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        selected_medecin_id = self.request.GET.get("medecin") or self.rdv.medecin_id
        ctx.update(
            {
                "role_key": "secretaire",
                "role_title": "Secretaire",
                "dashboard_nav": _nav_sec("Vue d'ensemble"),
                "rdv": self.rdv,
                "dashboard_return_url": _dashboard_url(selected_medecin_id),
            }
        )
        ctx.update(_shell(self.request, "Saisie des constantes avant consultation."))
        return ctx

    def form_valid(self, form):
        if self.rdv.statut not in (RendezVous.Statut.ARRIVE, RendezVous.Statut.EN_COURS):
            messages.error(self.request, "Le patient doit d'abord etre marque arrive.")
            return redirect(_dashboard_url(self.request.GET.get("medecin") or self.rdv.medecin_id))
        form.save()
        if self.rdv.statut == RendezVous.Statut.ARRIVE:
            self.rdv.statut = RendezVous.Statut.EN_COURS
            self.rdv.save(update_fields=["statut"])
        messages.success(self.request, "Constantes enregistrees, consultation en cours.")
        return redirect(_dashboard_url(self.request.GET.get("medecin") or self.rdv.medecin_id))
