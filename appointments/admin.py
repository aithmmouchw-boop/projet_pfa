from django.contrib import admin

from .models import AppointmentRequest


@admin.register(AppointmentRequest)
class AppointmentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "email",
        "status",
        "user",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email", "message", "doctor_ref", "service_ref")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    def has_delete_permission(self, request, obj=None):
        return False
