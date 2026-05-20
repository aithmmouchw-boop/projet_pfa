from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from consultations.models import Consultation
from medecins.models import Medecin
from patients.models import Patient
from rendez_vous.models import RendezVous


class SecretaireDashboardTests(TestCase):
    def setUp(self):
        self.secretaire = User.objects.create_user(
            email="sec@example.test",
            password="demo12345",
            role="infirmier",
        )
        self.patient_wafae = Patient.objects.create(
            user=User.objects.create_user(
                email="patient-wafae@example.test",
                password="demo12345",
                first_name="Patient",
                last_name="Wafae",
                role="patient",
            ),
            num_dossier="P-WAFAE",
            date_naissance=date(1995, 1, 1),
        )
        self.patient_autre = Patient.objects.create(
            user=User.objects.create_user(
                email="patient-autre@example.test",
                password="demo12345",
                first_name="Patient",
                last_name="Autre",
                role="patient",
            ),
            num_dossier="P-AUTRE",
            date_naissance=date(1994, 1, 1),
        )
        self.wafae = Medecin.objects.create(
            user=User.objects.create_user(
                email="wafae@example.test",
                password="demo12345",
                first_name="Wafae",
                last_name="Ceour",
                role="medecin",
            ),
            specialite="Cardiologie",
            tarif_consultation="400.00",
            actif=True,
        )
        self.chaimaa = Medecin.objects.create(
            user=User.objects.create_user(
                email="chaimaa@example.test",
                password="demo12345",
                first_name="Chaimaa",
                last_name="Ophta",
                role="medecin",
            ),
            specialite="Ophtalmologie",
            tarif_consultation="300.00",
            actif=True,
        )
        self.rdv_wafae = RendezVous.objects.create(
            patient=self.patient_wafae,
            medecin=self.wafae,
            date_heure=timezone.now() + timedelta(days=2),
            motif="Controle cardiologie",
            statut=RendezVous.Statut.PLANIFIE,
        )
        RendezVous.objects.create(
            patient=self.patient_autre,
            medecin=self.chaimaa,
            date_heure=timezone.now() + timedelta(days=3),
            motif="Controle ophtalmo",
            statut=RendezVous.Statut.PLANIFIE,
        )

    def test_dashboard_filters_rendez_vous_by_selected_medecin(self):
        self.client.force_login(self.secretaire)

        response = self.client.get(
            reverse("secretaire:secretaire_dashboard"),
            {"medecin": self.wafae.pk},
        )

        self.assertContains(response, "Dr. Wafae Ceour")
        self.assertContains(response, "Controle cardiologie")
        self.assertNotContains(response, "Controle ophtalmo")

    def test_secretary_can_mark_future_rdv_arrived_and_create_consultation(self):
        self.client.force_login(self.secretaire)

        response = self.client.post(
            f"{reverse('secretaire:rdv_arriver', args=[self.rdv_wafae.pk])}?medecin={self.wafae.pk}"
        )

        self.rdv_wafae.refresh_from_db()
        self.assertRedirects(
            response,
            f"{reverse('secretaire:secretaire_dashboard')}?medecin={self.wafae.pk}",
        )
        self.assertEqual(self.rdv_wafae.statut, RendezVous.Statut.ARRIVE)
        self.assertTrue(Consultation.objects.filter(rendez_vous=self.rdv_wafae).exists())
