"""Landing CLINOVA - vitrine."""

from __future__ import annotations

from types import SimpleNamespace

from django.urls import reverse
from django.views.generic import TemplateView

from clinic_common.visual_assets import (
    attach_medecin_visuals,
    medecin_photo_url,
    named_doctor_photo_url,
)
from medecins.models import Medecin


def _clinic():
    return SimpleNamespace(
        name="CLINOVA",
        tagline="La ou la medecine rencontre l'excellence.",
        subtagline="Chaque patient merite le meilleur.",
        address="Quai du Mont-Blanc 14, 1201 Geneve",
        phone="+41 22 000 00 00",
        email="contact@clinova.local",
        hours="Lun-Ven 8h00-20h00 / Sam 9h00-14h00",
        footer_statement=None,
        about_image=None,
    )


def _initials(name: str) -> str:
    parts = [part[0] for part in name.split() if part]
    return "".join(parts[:2]).upper() or "DR"


def _keywords_for_specialty(specialite: str) -> tuple[str, ...]:
    normalized = (specialite or "").casefold()
    if "cardio" in normalized:
        return ("ECG", "Rythme", "Tension")
    if "ophtal" in normalized:
        return ("Vision", "Fond d'oeil", "Correction")
    return ("Bilan", "Suivi", "Prevention")


def _featured():
    medecin = Medecin.objects.filter(actif=True).select_related("user").first()
    if medecin:
        name = medecin.user.get_full_name() or medecin.user.email
        return SimpleNamespace(
            nom=name,
            specialite=medecin.specialite,
            photo_url=medecin_photo_url(medecin),
            initials=_initials(name),
        )
    return SimpleNamespace(
        nom="Helene Morel",
        specialite="Medecine interne & preventive",
        photo_url="https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=400&q=80",
        initials="HM",
    )


def _services_demo():
    return [
        SimpleNamespace(
            pk=1,
            id=1,
            name="Medecine interne",
            short_description="Prevention, bilan global et suivi personnalise des pathologies chroniques.",
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
            name="Ophtalmologie",
            short_description="Bilan visuel, fond d'oeil et suivi de la correction optique.",
            description="",
        ),
        SimpleNamespace(
            pk=4,
            id=4,
            name="Medecine generale",
            short_description="Consultations de proximite, orientation et suivi regulier.",
            description="",
        ),
    ]


def _doctors_demo():
    return [
        SimpleNamespace(
            pk=1,
            id=1,
            nom="Dr. Helene Morel",
            specialite="Medecine interne",
            photo_url="https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=900&q=80",
            initials="HM",
            keywords=("Prevention", "Bilan", "Concierge"),
        ),
        SimpleNamespace(
            pk=2,
            id=2,
            nom="Dr. Wafae Ait Hmmouch",
            specialite="Cardiologie",
            photo_url=named_doctor_photo_url("Wafae Ait Hmmouch"),
            initials="WA",
            keywords=("ECG", "Rythme", "Urgences"),
        ),
        SimpleNamespace(
            pk=3,
            id=3,
            nom="Dr. Chaimaa Elgharzaoui",
            specialite="Ophtalmologie",
            photo_url=named_doctor_photo_url("Chaimaa Elgharzaoui"),
            initials="CE",
            keywords=("Vision", "Fond d'oeil", "Laser"),
        ),
        SimpleNamespace(
            pk=4,
            id=4,
            nom="Dr. Jonas Keller",
            specialite="Medecine generale",
            photo_url="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&w=900&q=80",
            initials="JK",
            keywords=("Bilan", "Suivi", "Prevention"),
        ),
    ]


def _doctors():
    medecins = attach_medecin_visuals(
        Medecin.objects.filter(actif=True)
        .select_related("user")
        .order_by("specialite", "user__last_name", "user__first_name")[:6]
    )
    if not medecins:
        return _doctors_demo()
    for medecin in medecins:
        name = medecin.user.get_full_name() or medecin.user.email
        medecin.nom = f"Dr. {name}"
        medecin.initials = _initials(name)
        medecin.keywords = _keywords_for_specialty(medecin.specialite)
    return medecins


def _testimonials_demo():
    return [
        SimpleNamespace(
            content="Une equipe rare : rigueur clinique, chaleur humaine, et une organisation irreprochable.",
            initials="M. R.",
            author_initials="M. R.",
            rating=5,
        ),
        SimpleNamespace(
            content="J'ai l'impression d'etre la seule patiente du cabinet. Chaque detail est pense pour nous rassurer.",
            initials="C. L.",
            author_initials="C. L.",
            rating=5,
        ),
        SimpleNamespace(
            content="Le niveau d'exigence est celui d'une clinique privee internationale, ici a Geneve.",
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
        ctx["doctors"] = _doctors()
        ctx["testimonials"] = _testimonials_demo()[:3]
        ctx["hero_slots"] = ["09:20", "14:00", "16:30"]
        ctx["stats"] = {
            "patients_count": 18420,
            "doctors_count": Medecin.objects.filter(actif=True).count() or 22,
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
