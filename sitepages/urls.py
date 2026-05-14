"""Routage de la landing — à inclure depuis le ``urls.py`` du projet.

Intégration typique::

    urlpatterns = [
        path("", include("sitepages.urls")),
        path("rendez-vous/", include(("appointments.urls", "appointments"), namespace="appointments")),
        path("compte/", include(("accounts.urls", "auth"), namespace="auth")),
        ...
    ]

N'oubliez pas ``"sitepages"`` dans ``INSTALLED_APPS``, ainsi que
``TEMPLATES['DIRS']`` pointant vers le dossier ``templates/`` et
``STATICFILES_DIRS`` / ``collectstatic`` pour ``static/``.
"""

from django.urls import path

from .views import (
    LandingPageView,
    RoleDashboardView,
)

urlpatterns = [
    path("", LandingPageView.as_view(), name="landing"),
    path(
        "patient/dashboard/",
        RoleDashboardView.as_view(role_key="patient"),
        name="patient_dashboard",
    ),
    path(
        "medecin/dashboard/",
        RoleDashboardView.as_view(role_key="medecin"),
        name="medecin_dashboard",
    ),
    path(
        "infirmier/dashboard/",
        RoleDashboardView.as_view(role_key="infirmier"),
        name="infirmier_dashboard",
    ),
    path(
        "caissier/dashboard/",
        RoleDashboardView.as_view(role_key="caissier"),
        name="caissier_dashboard",
    ),
]
