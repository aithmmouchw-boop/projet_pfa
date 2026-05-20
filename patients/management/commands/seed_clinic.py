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
            ("ceour@aesculia.local", "medecin", "Wafae", "Ceour"),
            ("ophtalmologie@aesculia.local", "medecin", "Chaimaa", "Ophta"),
            ("medecin@aesculia.local", "medecin", "Hélène", "Morel"),
            ("cardio@aesculia.local", "medecin", "Nadia", "Cardio"),
            ("ophtal@aesculia.local", "medecin", "Yassine", "Ophtal"),
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

        medecins = [
            ("medecin@aesculia.local", "Medecine generale", Decimal("180.00")),
            ("ceour@aesculia.local", "Cardiologie", Decimal("400.00")),
            ("ophtalmologie@aesculia.local", "Ophtalmologie", Decimal("300.00")),
            ("cardio@aesculia.local", "Cardiologie", Decimal("220.00")),
            ("ophtal@aesculia.local", "Ophtalmologie", Decimal("200.00")),
        ]
        for email, specialite, tarif in medecins:
            mu = User.objects.get(email=email)
            medecin, _ = Medecin.objects.get_or_create(
                user=mu,
                defaults={
                    "specialite": specialite,
                    "tarif_consultation": tarif,
                    "actif": True,
                },
            )
            medecin.specialite = specialite
            medecin.tarif_consultation = tarif
            medecin.actif = True
            medecin.save()

        self.stdout.write(self.style.NOTICE("Mot de passe : demo12345"))
