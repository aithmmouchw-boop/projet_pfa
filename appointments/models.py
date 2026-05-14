from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AppointmentRequest(models.Model):
    """Demande de rendez-vous (concierge) — hors agenda métier complet."""

    class Status(models.TextChoices):
        PENDING = "pending", _("En attente")
        CONFIRMED = "confirmed", _("Confirmé")
        CANCELLED = "cancelled", _("Annulé")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="appointment_requests",
        verbose_name=_("compte associé"),
    )
    full_name = models.CharField(_("nom complet"), max_length=200)
    email = models.EmailField(_("e-mail"))
    phone = models.CharField(_("téléphone"), max_length=32, blank=True)
    doctor_ref = models.CharField(_("réf. praticien"), max_length=200, blank=True)
    service_ref = models.CharField(_("réf. service"), max_length=200, blank=True)
    message = models.TextField(_("message"), blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_("statut"),
    )
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("demande de rendez-vous")
        verbose_name_plural = _("demandes de rendez-vous")

    def __str__(self) -> str:
        return f"{self.full_name} ({self.get_status_display()}) — {self.created_at:%Y-%m-%d}"
