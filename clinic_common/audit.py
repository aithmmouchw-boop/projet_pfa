from __future__ import annotations

from typing import Any

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db import DatabaseError
from django.dispatch import receiver

from clinic_common.models import SystemActivity


SENSITIVE_PATHS = (
    "/admin/patients/patient/",
    "/admin/consultations/dossierpatient/",
    "/admin/consultations/consultation/",
    "/admin/facturation/facture/",
    "/admin/facturation/paiement/",
    "/medecin/consultation/",
    "/caissier/facture/",
    "/patient/dossier/",
    "/patient/factures/",
)


def client_ip(request) -> str | None:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def user_agent(request) -> str:
    if request is None:
        return ""
    return (request.META.get("HTTP_USER_AGENT", "") or "")[:255]


def log_activity(
    *,
    action: str,
    description: str,
    request=None,
    actor=None,
    metadata: dict[str, Any] | None = None,
) -> None:
    if actor is None and request is not None and getattr(request, "user", None):
        user = request.user
        actor = user if getattr(user, "is_authenticated", False) else None
    try:
        SystemActivity.objects.create(
            actor=actor,
            action=action,
            description=description[:255],
            ip_address=client_ip(request),
            user_agent=user_agent(request),
            path=(getattr(request, "path", "") or "")[:255],
            metadata=metadata or {},
        )
    except (DatabaseError, RuntimeError, Exception):
        # Audit should never block login, page display, migrations, or backups.
        return


class SensitiveAccessAuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if (
            request.method == "GET"
            and getattr(user, "is_authenticated", False)
            and any(token in request.path for token in SENSITIVE_PATHS)
        ):
            log_activity(
                action=SystemActivity.Action.SENSITIVE_ACCESS,
                description="Consultation de donnees sensibles",
                request=request,
                metadata={"status_code": response.status_code},
            )
        return response


@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs) -> None:
    log_activity(
        action=SystemActivity.Action.LOGIN,
        description="Connexion utilisateur",
        request=request,
        actor=user,
    )


@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs) -> None:
    log_activity(
        action=SystemActivity.Action.LOGOUT,
        description="Deconnexion utilisateur",
        request=request,
        actor=user,
    )


@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs) -> None:
    email = (credentials or {}).get("username", "")
    log_activity(
        action=SystemActivity.Action.LOGIN_FAILED,
        description="Tentative de connexion echouee",
        request=request,
        metadata={"email": email[:191]},
    )
