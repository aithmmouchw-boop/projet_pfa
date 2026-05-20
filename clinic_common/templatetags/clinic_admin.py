from decimal import Decimal

from django import template
from django.db.models import Sum
from django.utils import timezone

register = template.Library()


def money_total(queryset) -> Decimal:
    return queryset.aggregate(total=Sum("montant"))["total"] or Decimal("0.00")


@register.simple_tag
def admin_overview_stats():
    try:
        from accounts.models import User
        from clinic_common.models import DatabaseBackup, SystemActivity, SystemSetting
        from consultations.models import Consultation
        from facturation.models import Facture, Paiement
        from medecins.models import Medecin
        from patients.models import Patient
        from rendez_vous.models import RendezVous

        today = timezone.localdate()
        month_start = today.replace(day=1)
        valid_payments = Paiement.objects.filter(valide=True)
        return {
            "patients_count": Patient.objects.count(),
            "appointments_count": RendezVous.objects.count(),
            "consultations_done_count": Consultation.objects.filter(termine=True).count(),
            "payments_count": valid_payments.count(),
            "users_count": User.objects.count(),
            "doctors_count": Medecin.objects.count(),
            "factures_count": Facture.objects.count(),
            "paid_consultations_count": Facture.objects.filter(statut=Facture.Statut.PAYEE).count(),
            "unpaid_consultations_count": Facture.objects.filter(
                statut__in=[Facture.Statut.BROUILLON, Facture.Statut.EMISE]
            ).count(),
            "revenue_today": money_total(valid_payments.filter(date__date=today)),
            "revenue_month": money_total(valid_payments.filter(date__date__gte=month_start)),
            "failed_logins_today": SystemActivity.objects.filter(
                action=SystemActivity.Action.LOGIN_FAILED,
                created_at__date=today,
            ).count(),
            "sensitive_access_today": SystemActivity.objects.filter(
                action=SystemActivity.Action.SENSITIVE_ACCESS,
                created_at__date=today,
            ).count(),
            "settings_count": SystemSetting.objects.count(),
            "backups_count": DatabaseBackup.objects.count(),
            "last_backup": DatabaseBackup.objects.order_by("-created_at").first(),
            "recent_activities": SystemActivity.objects.select_related("actor").order_by("-created_at")[:6],
        }
    except Exception:
        return {
            "patients_count": 0,
            "appointments_count": 0,
            "consultations_done_count": 0,
            "payments_count": 0,
            "users_count": 0,
            "doctors_count": 0,
            "factures_count": 0,
            "paid_consultations_count": 0,
            "unpaid_consultations_count": 0,
            "revenue_today": Decimal("0.00"),
            "revenue_month": Decimal("0.00"),
            "failed_logins_today": 0,
            "sensitive_access_today": 0,
            "settings_count": 0,
            "backups_count": 0,
            "last_backup": None,
            "recent_activities": [],
        }
