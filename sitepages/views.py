"""Landing AESCULIA — vitrine."""

from __future__ import annotations

from types import SimpleNamespace

from django.urls import reverse
from django.views.generic import TemplateView


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


_PORTAL_BY_ROLE = {
    "patient": "patients:patient_dashboard",
    "medecin": "medecins:medecin_dashboard",
    "infirmier": "secretaire:secretaire_dashboard",
    "caissier": "facturation:caissier_dashboard",
}


class LandingPageView(TemplateView):
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
            elif role in _PORTAL_BY_ROLE:
                ctx["portal_dashboard_url"] = reverse(_PORTAL_BY_ROLE[role])
                ctx["portal_label"] = "Mon espace"

        return ctx
