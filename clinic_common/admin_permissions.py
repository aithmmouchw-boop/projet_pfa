class ClinicDeletePermissionMixin:
    """Let the clinic admin account approve cascaded deletes in Django admin."""

    def has_delete_permission(self, request, obj=None):
        user = request.user
        if getattr(user, "is_superuser", False):
            return True
        if getattr(user, "is_staff", False) and getattr(user, "role", None) == "admin":
            return True
        return super().has_delete_permission(request, obj)
