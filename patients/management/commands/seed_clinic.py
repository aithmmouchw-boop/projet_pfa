"""Données de démo : utilisateurs par rôle + profils (mot de passe : demo12345)."""

from datetime import date
from decimal import Decimal

from django.core.management.base import BaseCommand

from accounts.models import User
from medecins.models import Medecin
from patients.models import Patient
from patients.utils import generer_num_dossier


class Command(BaseCommand):
    help = "Crée des comptes de démo (patient, médecin, secretaire, caissier) avec profils."

    def handle(self, *args, **options):
        pwd = "demo12345"
        specs = [
            ("patient@aesculia.local", "patient", "Pat", "Ient"),
            ("medecin@aesculia.local", "medecin", "Hélène", "Morel"),
            ("secretaire@aesculia.local", "infirmier", "Sam", "Secret"),
            ("caissier@aesculia.local", "caissier", "Cai", "Ssier"),
        ]
        for email, role, fn, ln in specs:
            u, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": fn,
                    "last_name": ln,
                    "role": role,
                },
            )
            if not created:
                u.role = role
                u.first_name = fn
                u.last_name = ln
                u.save()
            u.set_password(pwd)
            u.save()
            self.stdout.write(self.style.SUCCESS(f"Compte {email} ({role})"))

        pu = User.objects.get(email="patient@aesculia.local")
        Patient.objects.get_or_create(
            user=pu,
            defaults={
                "num_dossier": generer_num_dossier(),
                "date_naissance": date(1990, 5, 15),
                "telephone": "+41 22 000 00 01",
            },
        )

        mu = User.objects.get(email="medecin@aesculia.local")
        Medecin.objects.get_or_create(
            user=mu,
            defaults={
                "specialite": "Médecine interne",
                "tarif_consultation": Decimal("180.00"),
                "actif": True,
            },
        )

        self.stdout.write(self.style.NOTICE("Mot de passe : demo12345"))
