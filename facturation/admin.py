from decimal import Decimal

from django.contrib import admin
from django.db.models import DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.html import format_html

from clinic_common.admin_permissions import ClinicDeletePermissionMixin
from facturation.utils import refresh_facture_totals_and_status
from .models import Facture, LigneFacture, Paiement


class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 1
    can_delete = True


class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 1
    can_delete = True


@admin.register(Facture)
class FactureAdmin(ClinicDeletePermissionMixin, admin.ModelAdmin):
    list_display = (
        "numero",
        "patient_link",
        "medecin_link",
        "specialite",
        "consultation_date",
        "consultation_link",
        "total_ttc",
        "total_paye",
        "reste_a_payer",
        "statut",
        "created_at",
    )
    list_filter = ("statut", "consultation__medecin__specialite", "created_at")
    search_fields = (
        "numero",
        "patient__num_dossier",
        "patient__user__email",
        "patient__user__first_name",
        "patient__user__last_name",
        "consultation__medecin__user__email",
        "consultation__medecin__user__first_name",
        "consultation__medecin__user__last_name",
        "consultation__medecin__specialite",
    )
    autocomplete_fields = ("consultation", "patient")
    readonly_fields = ("medecin_link", "consultation_date", "total_paye", "reste_a_payer")
    date_hierarchy = "created_at"
    inlines = [LigneFactureInline, PaiementInline]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "patient__user",
                "consultation",
                "consultation__medecin__user",
            )
            .annotate(
                total_paye_admin=Coalesce(
                    Sum("paiements__montant", filter=Q(paiements__valide=True)),
                    Value(
                        Decimal("0.00"),
                        output_field=DecimalField(max_digits=10, decimal_places=2),
                    ),
                )
            )
        )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        refresh_facture_totals_and_status(form.instance)

    @admin.display(description="Patient")
    def patient_link(self, obj):
        url = reverse("admin:patients_patient_change", args=[obj.patient_id])
        return format_html('<a href="{}">{}</a>', url, obj.patient)

    @admin.display(description="Consultation")
    def consultation_link(self, obj):
        url = reverse("admin:consultations_consultation_change", args=[obj.consultation_id])
        return format_html('<a href="{}">Ouvrir</a>', url)

    @admin.display(description="Medecin", ordering="consultation__medecin__user__last_name")
    def medecin_link(self, obj):
        if not obj or not getattr(obj, "consultation_id", None):
            return "-"
        medecin = obj.consultation.medecin
        url = reverse("admin:medecins_medecin_change", args=[medecin.pk])
        return format_html('<a href="{}">{}</a>', url, medecin)

    @admin.display(description="Specialite", ordering="consultation__medecin__specialite")
    def specialite(self, obj):
        return obj.consultation.medecin.specialite

    @admin.display(description="Date consultation", ordering="consultation__date")
    def consultation_date(self, obj):
        if not obj or not getattr(obj, "consultation_id", None):
            return "-"
        return obj.consultation.date

    @admin.display(description="Total paye")
    def total_paye(self, obj):
        if not obj.pk:
            return "0.00"
        return getattr(obj, "total_paye_admin", None) or obj.total_paye_valide()

    @admin.display(description="Reste a payer")
    def reste_a_payer(self, obj):
        if not obj or not obj.pk:
            return "0.00"
        total_paye = getattr(obj, "total_paye_admin", None) or obj.total_paye_valide()
        reste = obj.total_ttc - total_paye
        return max(reste, Decimal("0.00"))
