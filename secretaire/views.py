from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import FormView, TemplateView

from clinic_common.mixins import RoleRequiredMixin
from consultations.models import Consultation
from secretaire.forms import ConstantesForm
from rendez_vous.models import RendezVous


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
        "clinic": SimpleNamespace(name="AESCULIA"),
        "user_display": (u.get_full_name() or "").strip() or u.email,
        "dashboard_intro": intro,
    }


class SecretaireDashboardView(RoleRequiredMixin, TemplateView):
    required_role = "infirmier"
    template_name = "secretaire/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        today = timezone.localdate()
        rdvs = (
            RendezVous.objects.filter(
                date_heure__date=today,
                statut__in=[
                    RendezVous.Statut.PLANIFIE,
                    RendezVous.Statut.CONFIRME,
                    RendezVous.Statut.ARRIVE,
                ],
            )
            .select_related("patient__user", "medecin__user")
            .order_by("date_heure")
        )
        ctx.update(
            {
                "role_key": "secretaire",
                "role_title": "Secretaire",
                "dashboard_nav": _nav_sec("Vue d'ensemble"),
                "rdvs_today": rdvs,
            }
        )
        ctx.update(_shell(self.request, "Arrivées et constantes du jour."))
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
            Consultation.objects.get_or_create(
                rendez_vous=rdv,
                defaults={
                    "medecin": rdv.medecin,
                    "patient": rdv.patient,
                    "dossier": rdv.patient.dossier,
                },
            )
            messages.success(request, "Patient marqué comme arrivé.")
        else:
            messages.warning(request, "Statut incompatible pour cette action.")
        return redirect(reverse("secretaire:secretaire_dashboard"))


class RdvConstantesView(RoleRequiredMixin, FormView):
    required_role = "infirmier"
    form_class = ConstantesForm
    template_name = "secretaire/constantes.html"

    def dispatch(self, request, *args, **kwargs):
        self.rdv = get_object_or_404(RendezVous, pk=kwargs["pk"])
        self.consultation = get_object_or_404(
            Consultation, rendez_vous=self.rdv
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kw = super().get_form_kwargs()
        kw["instance"] = self.consultation
        return kw

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "role_key": "secretaire",
                "role_title": "Secretaire",
                "dashboard_nav": _nav_sec("Vue d'ensemble"),
                "rdv": self.rdv,
            }
        )
        ctx.update(_shell(self.request, "Saisie des constantes avant consultation."))
        return ctx

    def form_valid(self, form):
        if self.rdv.statut != RendezVous.Statut.ARRIVE:
            messages.error(self.request, "Le patient doit d’abord être marqué arrivé.")
            return redirect(reverse("secretaire:secretaire_dashboard"))
        form.save()
        self.rdv.statut = RendezVous.Statut.EN_COURS
        self.rdv.save(update_fields=["statut"])
        messages.success(self.request, "Constantes enregistrées, consultation en cours.")
        return redirect(reverse("secretaire:secretaire_dashboard"))
