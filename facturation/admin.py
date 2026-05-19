from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Facture, LigneFacture, Paiement


class LigneFactureInline(admin.TabularInline):
    model = LigneFacture
    extra = 1
    can_delete = False


class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 1
    can_delete = False


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "patient_link",
        "consultation_link",
        "total_ttc",
        "total_paye",
        "statut",
        "created_at",
    )
    list_filter = ("statut", "created_at")
    search_fields = (
        "numero",
        "patient__num_dossier",
        "patient__user__email",
        "patient__user__first_name",
        "patient__user__last_name",
    )
    autocomplete_fields = ("consultation", "patient")
    readonly_fields = ("total_paye",)
    date_hierarchy = "created_at"
    inlines = [LigneFactureInline, PaiementInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient__user", "consultation")

    @admin.display(description="Patient")
    def patient_link(self, obj):
        url = reverse("admin:patients_patient_change", args=[obj.patient_id])
        return format_html('<a href="{}">{}</a>', url, obj.patient)

    @admin.display(description="Consultation")
    def consultation_link(self, obj):
        url = reverse("admin:consultations_consultation_change", args=[obj.consultation_id])
        return format_html('<a href="{}">Ouvrir</a>', url)

    @admin.display(description="Total paye")
    def total_paye(self, obj):
        if not obj.pk:
            return "0.00"
        return obj.total_paye_valide()

    def has_delete_permission(self, request, obj=None):
        return False
