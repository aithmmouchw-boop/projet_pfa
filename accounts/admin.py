from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import CaissierAccount, InfirmierAccount, User


admin.site.site_header = "Aesculia Administration"
admin.site.site_title = "Aesculia Admin"
admin.site.index_title = "Gestion de la clinique"

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "role", "is_staff", "is_superuser")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Informations personnelles"), {"fields": ("first_name", "last_name", "role")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Dates importantes"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "role", "is_staff", "is_superuser"),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")

    def has_module_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StaffRoleAdmin(DjangoUserAdmin):
    role_value: str = ""
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "is_active", "last_login")
    list_filter = ("is_active",)
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            _("Informations personnelles"),
            {"fields": ("first_name", "last_name", "is_active")},
        ),
        (_("Dates importantes"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "first_name", "last_name", "is_active"),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(role=self.role_value)

    def get_changeform_initial_data(self, request):
        initial = super().get_changeform_initial_data(request)
        initial["is_active"] = True
        return initial

    def save_model(self, request, obj, form, change):
        obj.role = self.role_value
        obj.is_staff = False
        obj.is_superuser = False
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(InfirmierAccount)
class InfirmierAccountAdmin(StaffRoleAdmin):
    role_value = "infirmier"


@admin.register(CaissierAccount)
class CaissierAccountAdmin(StaffRoleAdmin):
    role_value = "caissier"
