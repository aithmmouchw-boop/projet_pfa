from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from clinic_common.admin_permissions import ClinicDeletePermissionMixin
from consultations.models import Consultation
from rendez_vous.services import ensure_consultation_for_rdv
from .models import RendezVous


@admin.register(RendezVous)
class RendezVousAdmin(ClinicDeletePermissionMixin, admin.ModelAdmin):
    list_display = ("patient_link", "medecin_link", "date_heure", "statut", "motif", "consultation_link")
    list_filter = ("statut", "date_heure")
    search_fields = (
        "motif",
        "patient__num_dossier",
        "patient__user__email",
        "patient__user__first_name",
        "patient__user__last_name",
        "medecin__user__email",
        "medecin__user__first_name",
        "medecin__user__last_name",
    )
    autocomplete_fields = ("patient", "medecin")
    date_hierarchy = "date_heure"
    readonly_fields = ("consultation_link",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("patient__user", "medecin__user")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.statut in (
            RendezVous.Statut.ARRIVE,
            RendezVous.Statut.EN_COURS,
            RendezVous.Statut.TERMINE,
        ):
            ensure_consultation_for_rdv(obj)

    @admin.display(description="Patient")
    def patient_link(self, obj):
        url = reverse("admin:patients_patient_change", args=[obj.patient_id])
        return format_html('<a href="{}">{}</a>', url, obj.patient)

    @admin.display(description="Medecin")
    def medecin_link(self, obj):
        url = reverse("admin:medecins_medecin_change", args=[obj.medecin_id])
        return format_html('<a href="{}">{}</a>', url, obj.medecin)

    @admin.display(description="Consultation")
    def consultation_link(self, obj):
        if not obj.pk:
            return "-"
        consultation = Consultation.objects.filter(rendez_vous=obj).first()
        if not consultation:
            return "Aucune"
        url = reverse("admin:consultations_consultation_change", args=[consultation.pk])
        return format_html('<a href="{}">Ouvrir</a>', url)
