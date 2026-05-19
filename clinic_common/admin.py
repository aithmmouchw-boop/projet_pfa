from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.html import format_html

from clinic_common.backup import create_database_backup
from clinic_common.models import DatabaseBackup, SystemActivity, SystemSetting


@admin.register(SystemActivity)
class SystemActivityAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "ip_address", "path", "description")
    list_filter = ("action", "created_at")
    search_fields = ("description", "actor__email", "path", "ip_address")
    readonly_fields = (
        "actor",
        "action",
        "description",
        "ip_address",
        "user_agent",
        "path",
        "metadata",
        "created_at",
    )
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DatabaseBackup)
class DatabaseBackupAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "created_by",
        "status",
        "size_label",
        "file_link",
        "completed_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("file_path", "notes", "error_message", "created_by__email")
    readonly_fields = (
        "created_by",
        "file_path",
        "status",
        "size_bytes",
        "notes",
        "error_message",
        "created_at",
        "completed_at",
    )
    date_hierarchy = "created_at"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "create-now/",
                self.admin_site.admin_view(self.create_now),
                name="clinic_common_databasebackup_create",
            )
        ]
        return custom + urls

    def create_now(self, request):
        try:
            backup = create_database_backup(created_by=request.user, notes="Sauvegarde lancee depuis admin.")
        except Exception as exc:
            messages.error(request, f"Sauvegarde echouee: {exc}")
        else:
            messages.success(request, f"Sauvegarde creee: {backup.file_path}")
        return redirect(reverse("admin:clinic_common_databasebackup_changelist"))

    @admin.display(description="Taille")
    def size_label(self, obj):
        if not obj.size_bytes:
            return "-"
        return f"{obj.size_bytes / 1024:.1f} KB"

    @admin.display(description="Fichier")
    def file_link(self, obj):
        if not obj.file_path:
            return "-"
        return format_html("<code>{}</code>", obj.file_path)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "label", "is_sensitive", "updated_by", "updated_at")
    list_filter = ("is_sensitive", "updated_at")
    search_fields = ("key", "label")
    readonly_fields = ("updated_at",)

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
