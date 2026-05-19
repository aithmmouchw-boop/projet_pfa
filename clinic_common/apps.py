from django.apps import AppConfig


class ClinicCommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "clinic_common"

    def ready(self) -> None:
        import clinic_common.audit  # noqa: F401
