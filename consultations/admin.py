from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from facturation.models import Facture
from .models import Consultation, DossierPatient, LigneOrdonnance, Ordonnance


class NoDeleteAdminMixin:
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DossierPatient)
class DossierPatientAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("num_dossier", "patient_link", "consultations_total", "created_at")
    search_fields = (
        "num_dossier",
        "patient__num_dossier",
        "patient__user__email",
        "patient__user__first_name",
        "patient__user__last_name",
    )
    autocomplete_fields = ("patient",)
    readonly_fields = ("consultations_total",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient__user")

    @admin.display(description="Patient")
    def patient_link(self, obj):
        url = reverse("admin:patients_patient_change", args=[obj.patient_id])
        return format_html('<a href="{}">{}</a>', url, obj.patient)

    @admin.display(description="Consultations")
    def consultations_total(self, obj):
        if not obj.pk:
            return 0
        return obj.consultations.count()


@admin.register(Consultation)
class ConsultationAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    list_display = (
        "patient_link",
        "medecin_link",
        "date",
        "termine",
        "ordonnance_link",
        "facture_link",
    )
    list_filter = ("termine", "date")
    search_fields = (
        "patient__num_dossier",
        "patient__user__email",
        "patient__user__first_name",
        "patient__user__last_name",
        "medecin__user__email",
        "medecin__user__first_name",
        "medecin__user__last_name",
        "diagnostic",
        "compte_rendu",
    )
    autocomplete_fields = ("rendez_vous", "medecin", "patient", "dossier")
    date_hierarchy = "date"
    readonly_fields = ("ordonnance_link", "facture_link")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "patient__user",
            "medecin__user",
            "dossier",
        )

    @admin.display(description="Patient")
    def patient_link(self, obj):
        url = reverse("admin:patients_patient_change", args=[obj.patient_id])
        return format_html('<a href="{}">{}</a>', url, obj.patient)

    @admin.display(description="Medecin")
    def medecin_link(self, obj):
        url = reverse("admin:medecins_medecin_change", args=[obj.medecin_id])
        return format_html('<a href="{}">{}</a>', url, obj.medecin)

    @admin.display(description="Ordonnance")
    def ordonnance_link(self, obj):
        if not obj.pk:
            return "-"
        ordonnance = Ordonnance.objects.filter(consultation=obj).first()
        if not ordonnance:
            return "Aucune"
        url = reverse("admin:consultations_ordonnance_change", args=[ordonnance.pk])
        return format_html('<a href="{}">Ouvrir</a>', url)

    @admin.display(description="Facture")
    def facture_link(self, obj):
        if not obj.pk:
            return "-"
        facture = Facture.objects.filter(consultation=obj).first()
        if not facture:
            return "Aucune"
        url = reverse("admin:facturation_facture_change", args=[facture.pk])
        return format_html('<a href="{}">{}</a>', url, facture.numero)


class LigneOrdonnanceInline(admin.TabularInline):
    model = LigneOrdonnance
    extra = 1
    can_delete = False


@admin.register(Ordonnance)
class OrdonnanceAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("consultation_link", "patient_name", "date", "valide_jusqu")
    search_fields = (
        "consultation__patient__num_dossier",
        "consultation__patient__user__email",
        "consultation__patient__user__first_name",
        "consultation__patient__user__last_name",
    )
    autocomplete_fields = ("consultation",)
    inlines = [LigneOrdonnanceInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("consultation__patient__user")

    @admin.display(description="Consultation")
    def consultation_link(self, obj):
        url = reverse("admin:consultations_consultation_change", args=[obj.consultation_id])
        return format_html('<a href="{}">{}</a>', url, obj.consultation)

    @admin.display(description="Patient")
    def patient_name(self, obj):
        return obj.consultation.patient


@admin.register(LigneOrdonnance)
class LigneOrdonnanceAdmin(NoDeleteAdminMixin, admin.ModelAdmin):
    list_display = ("ordonnance", "medicament", "dosage")
    search_fields = ("medicament", "dosage", "ordonnance__consultation__patient__num_dossier")
    autocomplete_fields = ("ordonnance",)
