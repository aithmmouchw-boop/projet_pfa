"""Landing AESCULIA — contexte vitrine (Obsidian Sage)."""

from __future__ import annotations

from types import SimpleNamespace

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from appointments.models import AppointmentRequest


def _clinic():
    return SimpleNamespace(
        name="AESCULIA",
        tagline="Là où la médecine rencontre l'excellence.",
        subtagline="Chaque patient mérite le meilleur.",
        address="Quai du Mont-Blanc 14, 1201 Genève",
        phone="+41 22 000 00 00",
        email="concierge@aesculia.ch",
        hours="Lun–Ven 8h00–20h00 · Sam 9h00–14h00",
        footer_statement=None,
        about_image=None,
    )


def _featured():
    return SimpleNamespace(
        nom="Hélène Morel",
        specialite="Médecine interne & préventive",
        photo=None,
        initials="HM",
    )


def _services_demo():
    return [
        SimpleNamespace(
            pk=1,
            id=1,
            name="Médecine interne",
            short_description="Prévention, bilan global et suivi personnalisé des pathologies chroniques.",
            description="",
        ),
        SimpleNamespace(
            pk=2,
            id=2,
            name="Cardiologie",
            short_description="Explorations non invasives et prise en charge des facteurs de risque.",
            description="",
        ),
        SimpleNamespace(
            pk=3,
            id=3,
            name="Gynécologie",
            short_description="Accompagnement confidentiel à chaque étape de la vie des femmes.",
            description="",
        ),
        SimpleNamespace(
            pk=4,
            id=4,
            name="Pédiatrie",
            short_description="Soins dédiés aux plus jeunes patients dans un environnement apaisé.",
            description="",
        ),
    ]


def _doctors_demo():
    return [
        SimpleNamespace(
            pk=1,
            id=1,
            nom="Dr. Hélène Morel",
            specialite="Médecine interne",
            photo=None,
            initials="HM",
            keywords=("Prévention", "Bilan", "Concierge"),
        ),
        SimpleNamespace(
            pk=2,
            id=2,
            nom="Dr. Marc Auberjonois",
            specialite="Cardiologie",
            photo=None,
            initials="MA",
            keywords=("Imagerie", "Rythme", "Urgences"),
        ),
        SimpleNamespace(
            pk=3,
            id=3,
            nom="Dr. Sofia El Mansouri",
            specialite="Gynécologie",
            photo=None,
            initials="SE",
            keywords=("Fertilité", "Suivi", "Laser"),
        ),
        SimpleNamespace(
            pk=4,
            id=4,
            nom="Dr. Jonas Keller",
            specialite="Pédiatrie",
            photo=None,
            initials="JK",
            keywords=("Vaccins", "Croissance", "Urgences"),
        ),
    ]


def _testimonials_demo():
    return [
        SimpleNamespace(
            content="Une équipe rare : rigueur clinique, chaleur humaine, et une organisation irréprochable.",
            initials="M. R.",
            author_initials="M. R.",
            rating=5,
        ),
        SimpleNamespace(
            content="J'ai l'impression d'être la seule patiente du cabinet. Chaque détail est pensé pour nous rassurer.",
            initials="C. L.",
            author_initials="C. L.",
            rating=5,
        ),
        SimpleNamespace(
            content="Le niveau d'exigence est celui d'une clinique privée internationale — ici, à Genève.",
            initials="P. V.",
            author_initials="P. V.",
            rating=5,
        ),
    ]


_DASHBOARD_URLNAME_BY_ROLE = {
    "patient": "patient_dashboard",
    "medecin": "medecin_dashboard",
    "infirmier": "infirmier_dashboard",
    "caissier": "caissier_dashboard",
}


class LandingPageView(TemplateView):
    """Accueil AESCULIA — branchez vos modèles dans ``get_context_data``."""

    template_name = "landing.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["clinic"] = _clinic()
        ctx["featured_doctor"] = _featured()
        ctx["services"] = _services_demo()[:6]
        ctx["doctors"] = _doctors_demo()[:6]
        ctx["testimonials"] = _testimonials_demo()[:3]
        ctx["hero_slots"] = ["09:20", "14:00", "16:30"]
        ctx["stats"] = {
            "patients_count": 18420,
            "doctors_count": 22,
            "years": 28,
            "consultations_per_day": 94,
        }
        ctx["system_name"] = "Clinic OS"

        ctx["portal_dashboard_url"] = None
        ctx["portal_label"] = ""
        user = self.request.user
        if user.is_authenticated:
            role = getattr(user, "role", None) or "patient"
            if role == "admin" and getattr(user, "is_staff", False):
                ctx["portal_dashboard_url"] = reverse("admin:index")
                ctx["portal_label"] = "Administration"
            elif role in _DASHBOARD_URLNAME_BY_ROLE:
                ctx["portal_dashboard_url"] = reverse(
                    _DASHBOARD_URLNAME_BY_ROLE[role]
                )
                ctx["portal_label"] = "Mon espace"

        # Branchement réel (exemple) :
        # ctx["clinic"] = Clinic.objects.first()
        # ctx["featured_doctor"] = ctx["clinic"].featured_doctor
        # ctx["services"] = Service.objects.filter(active=True)[:6]
        # ctx["doctors"] = Medecin.objects.filter(on_homepage=True)[:6]
        # ctx["testimonials"] = Testimonial.objects.filter(published=True)[:3]
        # ctx["stats"] = {...}

        return ctx


_ROLE_LABELS = {
    "patient": "Patient",
    "medecin": "Médecin",
    "infirmier": "Infirmier·ère",
    "caissier": "Caissier·ère",
}

_DASH_NAV = {
    "patient": [
        {"label": "Vue d'ensemble", "url_name": "patient_dashboard", "active": True},
        {
            "label": "Mes demandes",
            "url_name": "patient_dashboard",
            "fragment": "demandes-rdv",
        },
        {"label": "Prendre un rendez-vous", "url_name": "appointments:create"},
        {"label": "Messages", "soon": True},
        {"label": "Profil", "soon": True},
    ],
    "medecin": [
        {"label": "Vue d'ensemble", "url_name": "medecin_dashboard", "active": True},
        {"label": "Agenda", "soon": True},
        {"label": "Dossiers patients", "soon": True},
        {"label": "Ordonnances", "soon": True},
    ],
    "infirmier": [
        {"label": "Vue d'ensemble", "url_name": "infirmier_dashboard", "active": True},
        {"label": "Planning des soins", "soon": True},
        {"label": "Consignes", "soon": True},
        {"label": "Matériel", "soon": True},
    ],
    "caissier": [
        {"label": "Vue d'ensemble", "url_name": "caissier_dashboard", "active": True},
        {"label": "Encaissements", "soon": True},
        {"label": "Factures", "soon": True},
        {"label": "Clôtures de journée", "soon": True},
    ],
}

_DASH_CARDS = {
    "patient": [
        {
            "title": "Prochain rendez-vous",
            "value": "—",
            "hint": "L’agenda patient sera relié ici.",
        },
        {
            "title": "Documents",
            "value": "0",
            "hint": "Ordonnances et résultats d’analyses.",
        },
        {
            "title": "Messages",
            "value": "—",
            "hint": "Échanges sécurisés avec la clinique.",
        },
    ],
    "medecin": [
        {
            "title": "Consultations du jour",
            "value": "—",
            "hint": "Flux agenda / file d’attente.",
        },
        {
            "title": "Dossiers à relire",
            "value": "—",
            "hint": "Priorités et tâches cliniques.",
        },
        {
            "title": "Ordonnances en attente",
            "value": "—",
            "hint": "Signature et envoi patient.",
        },
    ],
    "infirmier": [
        {
            "title": "Soins en cours",
            "value": "—",
            "hint": "Chambres et postes assignés.",
        },
        {
            "title": "Tâches du poste",
            "value": "—",
            "hint": "Check-lists et consignes médecin.",
        },
        {
            "title": "Matériel / stérilisation",
            "value": "—",
            "hint": "Suivi logistique soins.",
        },
    ],
    "caissier": [
        {
            "title": "Encaissements du jour",
            "value": "—",
            "hint": "Totaux et moyens de paiement.",
        },
        {
            "title": "Factures en attente",
            "value": "—",
            "hint": "Émission et relances.",
        },
        {
            "title": "Clôture journée",
            "value": "—",
            "hint": "Rapprochement et exports.",
        },
    ],
}

_DASH_INTRO = {
    "patient": "Votre espace personnel : rendez-vous, documents et échanges avec Aesculia.",
    "medecin": "Pilotage de l’activité clinique : agenda, dossiers et prescriptions.",
    "infirmier": "Coordination des soins : planning, consignes et suivi au chevet.",
    "caissier": "Caisse et facturation : encaissements, factures et fin de journée.",
}

_DASH_HERO = {
    "patient": {
        "kicker": "Parcours patient",
        "title": "Vos rendez-vous et vos échanges, au même endroit",
        "subtitle": "La demande de créneau est ouverte ; l’historique, les rappels et la messagerie seront reliés à mesure du branchement métier.",
        "primary_label": "Demander un rendez-vous",
        "primary_url_name": "appointments:create",
    },
    "medecin": {
        "kicker": "Quotidien",
        "title": "Vue d’ensemble de l’activité",
        "subtitle": "Agenda, dossiers et prescriptions seront pilotés depuis cet espace.",
    },
    "infirmier": {
        "kicker": "Coordination",
        "title": "Soins et consignes, structurés",
        "subtitle": "Planning des postes, tâches et matériel seront synchronisés avec le service.",
    },
    "caissier": {
        "kicker": "Facturation",
        "title": "Encaissements et clôtures",
        "subtitle": "Suivi des paiements, factures et fin de journée seront intégrés ici.",
    },
}

_DASH_CTAS = {
    "patient": [
        {"label": "Site public", "url_name": "landing", "style": "ghost"},
    ],
    "medecin": [
        {"label": "Site public", "url_name": "landing", "style": "ghost"},
    ],
    "infirmier": [
        {"label": "Site public", "url_name": "landing", "style": "ghost"},
    ],
    "caissier": [
        {"label": "Site public", "url_name": "landing", "style": "ghost"},
    ],
}


def _user_display_name(user) -> str:
    parts = [
        (getattr(user, "first_name", None) or "").strip(),
        (getattr(user, "last_name", None) or "").strip(),
    ]
    full = " ".join(p for p in parts if p)
    if full:
        return full
    return (getattr(user, "email", None) or "").strip()


class RoleDashboardView(LoginRequiredMixin, TemplateView):
    """Tableau de bord par rôle — interface dédiée jusqu’aux modules métier."""

    template_name = "dashboards/home.html"
    role_key = "patient"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        user = request.user
        user_role = getattr(user, "role", None) or "patient"
        if user_role == "admin":
            if getattr(user, "is_staff", False):
                return redirect(reverse("admin:index"))
            return redirect(reverse("landing"))
        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if user_role != self.role_key:
            url_name = _DASHBOARD_URLNAME_BY_ROLE.get(user_role, "patient_dashboard")
            return redirect(reverse(url_name))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["clinic"] = _clinic()
        ctx["role_title"] = _ROLE_LABELS.get(self.role_key, self.role_key.capitalize())
        ctx["dashboard_nav"] = list(_DASH_NAV.get(self.role_key, _DASH_NAV["patient"]))
        ctx["dashboard_cards"] = list(_DASH_CARDS.get(self.role_key, _DASH_CARDS["patient"]))
        ctx["dashboard_intro"] = _DASH_INTRO.get(self.role_key, _DASH_INTRO["patient"])
        ctx["dashboard_ctas"] = list(_DASH_CTAS.get(self.role_key, []))
        ctx["dashboard_hero"] = _DASH_HERO.get(self.role_key)
        user = self.request.user
        ctx["user_display"] = _user_display_name(user) if user.is_authenticated else ""
        if self.role_key == "patient" and user.is_authenticated:
            ctx["appointment_requests"] = list(
                AppointmentRequest.objects.filter(user=user)[:10]
            )
        else:
            ctx["appointment_requests"] = []
        return ctx
