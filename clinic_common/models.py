from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class SystemActivity(models.Model):
    class Action(models.TextChoices):
        LOGIN = "login", _("Connexion")
        LOGOUT = "logout", _("Deconnexion")
        LOGIN_FAILED = "login_failed", _("Tentative echouee")
        SENSITIVE_ACCESS = "sensitive_access", _("Acces donnees sensibles")
        CONSULTATION_FINISHED = "consultation_finished", _("Consultation terminee")
        PAYMENT_CREATED = "payment_created", _("Paiement realise")
        BACKUP_CREATED = "backup_created", _("Sauvegarde creee")
        ADMIN_ACTION = "admin_action", _("Action admin")

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="system_activities",
        verbose_name=_("utilisateur"),
    )
    action = models.CharField(
        _("action"),
        max_length=40,
        choices=Action.choices,
    )
    description = models.CharField(_("description"), max_length=255)
    ip_address = models.GenericIPAddressField(_("adresse IP"), null=True, blank=True)
    user_agent = models.CharField(_("navigateur"), max_length=255, blank=True)
    path = models.CharField(_("chemin"), max_length=255, blank=True)
    metadata = models.JSONField(_("metadata"), default=dict, blank=True)
    created_at = models.DateTimeField(_("cree le"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]
        verbose_name = _("activite systeme")
        verbose_name_plural = _("activites systeme")

    def __str__(self) -> str:
        return f"{self.get_action_display()} - {self.created_at:%d/%m/%Y %H:%M}"


class DatabaseBackup(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", _("En cours")
        SUCCESS = "success", _("Reussie")
        FAILED = "failed", _("Echouee")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="database_backups",
        verbose_name=_("cree par"),
    )
    file_path = models.CharField(_("fichier"), max_length=500, blank=True)
    status = models.CharField(
        _("statut"),
        max_length=20,
        choices=Status.choices,
        default=Status.RUNNING,
    )
    size_bytes = models.PositiveBigIntegerField(_("taille octets"), default=0)
    notes = models.TextField(_("notes"), blank=True)
    error_message = models.TextField(_("erreur"), blank=True)
    created_at = models.DateTimeField(_("cree le"), auto_now_add=True)
    completed_at = models.DateTimeField(_("termine le"), null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("sauvegarde base de donnees")
        verbose_name_plural = _("sauvegardes base de donnees")

    def __str__(self) -> str:
        return f"Backup #{self.pk} - {self.get_status_display()}"


class SystemSetting(models.Model):
    key = models.SlugField(_("cle"), max_length=80, unique=True)
    label = models.CharField(_("libelle"), max_length=150)
    value = models.JSONField(_("valeur"), default=dict, blank=True)
    is_sensitive = models.BooleanField(_("sensible"), default=False)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="updated_system_settings",
        verbose_name=_("modifie par"),
    )
    updated_at = models.DateTimeField(_("modifie le"), auto_now=True)

    class Meta:
        ordering = ["key"]
        verbose_name = _("parametre systeme")
        verbose_name_plural = _("parametres systeme")

    def __str__(self) -> str:
        return self.label or self.key
