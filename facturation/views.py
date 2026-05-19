from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from clinic_common.audit import log_activity
from clinic_common.mixins import RoleRequiredMixin
from clinic_common.models import SystemActivity
from facturation.forms import LigneFactureAjoutForm, PaiementForm
from facturation.models import Facture, Paiement


def _nav_caissier(active: str) -> list[dict]:
    return [
        {
            "label": "Vue d'ensemble",
            "url_name": "facturation:caissier_dashboard",
            "fragment": None,
            "active": active == "Vue d'ensemble",
        },
    ]


def _shell(request, intro: str) -> dict:
    from types import SimpleNamespace

    u = request.user
    return {
        "clinic": SimpleNamespace(name="AESCULIA"),
        "user_display": (u.get_full_name() or "").strip() or u.email,
        "dashboard_intro": intro,
    }


def _money_total(queryset) -> Decimal:
    return queryset.aggregate(total=Sum("montant"))["total"] or Decimal("0.00")


def _finance_stats() -> dict:
    today = timezone.localdate()
    month_start = today.replace(day=1)
    valid_payments = Paiement.objects.filter(valide=True)
    return {
        "revenue_today": _money_total(valid_payments.filter(date__date=today)),
        "revenue_month": _money_total(valid_payments.filter(date__date__gte=month_start)),
        "paid_consultations": Facture.objects.filter(statut=Facture.Statut.PAYEE).count(),
        "unpaid_consultations": Facture.objects.filter(
            statut__in=[Facture.Statut.BROUILLON, Facture.Statut.EMISE]
        ).count(),
    }


class CaissierDashboardView(RoleRequiredMixin, ListView):
    required_role = "caissier"
    template_name = "caissier/dashboard.html"
    context_object_name = "factures"

    def get_queryset(self):
        return (
            Facture.objects.filter(consultation__termine=True)
            .exclude(statut=Facture.Statut.ANNULEE)
            .select_related("patient__user", "consultation__medecin__user")
            .order_by("-created_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "role_key": "caissier",
                "role_title": "Caissier",
                "dashboard_nav": _nav_caissier("Vue d'ensemble"),
                "finance_stats": _finance_stats(),
            }
        )
        ctx.update(_shell(self.request, "Consultations terminees, paiements et revenus."))
        return ctx


class FactureDetailView(RoleRequiredMixin, TemplateView):
    required_role = "caissier"
    template_name = "caissier/facture_detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        facture = get_object_or_404(
            Facture.objects.select_related(
                "patient__user", "consultation__medecin__user"
            ),
            pk=self.kwargs["pk"],
        )
        paye = facture.total_paye_valide()
        reste = facture.total_ttc - paye
        if reste < Decimal("0"):
            reste = Decimal("0")
        ctx.update(
            {
                "role_key": "caissier",
                "role_title": "Caissier",
                "dashboard_nav": _nav_caissier("Vue d'ensemble"),
                "facture": facture,
                "total_paye": paye,
                "reste": reste,
                "ligne_form": LigneFactureAjoutForm(),
                "paiement_form": PaiementForm(
                    initial={"montant": reste, "mode": Paiement.Mode.ESPECES}
                ),
                "latest_payment": facture.paiements.filter(valide=True).first(),
            }
        )
        ctx.update(_shell(self.request, "Dossier de consultation terminee et paiement."))
        return ctx

    def post(self, request, *args, **kwargs):
        facture = get_object_or_404(Facture, pk=self.kwargs["pk"])
        if "valider" in request.POST:
            if facture.statut == Facture.Statut.BROUILLON:
                facture.statut = Facture.Statut.EMISE
                facture.save(update_fields=["statut"])
                messages.success(request, "Facture emise.")
            return redirect(reverse("facturation:facture_detail", kwargs={"pk": facture.pk}))
        if "add_ligne" in request.POST:
            form = LigneFactureAjoutForm(request.POST)
            if form.is_valid():
                ligne = form.save(commit=False)
                ligne.facture = facture
                ligne.save()
                facture.calculer_total()
                messages.success(request, "Ligne ajoutee.")
            else:
                messages.error(request, "Ligne invalide.")
            return redirect(reverse("facturation:facture_detail", kwargs={"pk": facture.pk}))
        if "encaisser" in request.POST:
            form = PaiementForm(request.POST)
            if form.is_valid():
                paiement = form.save(commit=False)
                paiement.facture = facture
                paiement.valide = True
                paiement.save()
                facture.refresh_from_db()
                log_activity(
                    action=SystemActivity.Action.PAYMENT_CREATED,
                    description="Paiement facture enregistre",
                    request=request,
                    metadata={
                        "facture_id": facture.pk,
                        "paiement_id": paiement.pk,
                        "montant": str(paiement.montant),
                        "mode": paiement.mode,
                    },
                )
                if facture.total_paye_valide() >= facture.total_ttc:
                    facture.statut = Facture.Statut.PAYEE
                    facture.save(update_fields=["statut"])
                    messages.success(request, "Paiement enregistre - facture soldee.")
                    return redirect(reverse("facturation:facture_recu", kwargs={"pk": facture.pk}))
                messages.success(request, "Paiement enregistre.")
            else:
                messages.error(request, "Montant ou mode invalide.")
            return redirect(reverse("facturation:facture_detail", kwargs={"pk": facture.pk}))
        return redirect(reverse("facturation:facture_detail", kwargs={"pk": facture.pk}))


class FactureRecuView(RoleRequiredMixin, TemplateView):
    required_role = "caissier"
    template_name = "caissier/recu.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        facture = get_object_or_404(
            Facture.objects.select_related(
                "patient__user", "consultation__medecin__user"
            ),
            pk=self.kwargs["pk"],
        )
        ctx.update(
            {
                "role_key": "caissier",
                "role_title": "Caissier",
                "dashboard_nav": _nav_caissier("Vue d'ensemble"),
                "facture": facture,
                "latest_payment": facture.paiements.filter(valide=True).first(),
            }
        )
        ctx.update(_shell(self.request, "Facture de paiement."))
        return ctx
