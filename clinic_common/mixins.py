"""Mixins partagés — contrôle d’accès par rôle."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Accès réservé à un rôle précis (attribut ``required_role``)."""

    required_role: str = ""

    def test_func(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return getattr(user, "role", None) == self.required_role

    def handle_no_permission(self) -> Any:
        user = self.request.user
        if not user.is_authenticated:
            return redirect(f"{reverse('auth:login')}?next={self.request.path}")
        role = getattr(user, "role", None) or "patient"
        mapping = {
            "patient": "patients:patient_dashboard",
            "medecin": "medecins:medecin_dashboard",
            "infirmier": "secretaire:secretaire_dashboard",
            "caissier": "facturation:caissier_dashboard",
        }
        name = mapping.get(role)
        if name:
            return redirect(reverse(name))
        raise PermissionDenied()
