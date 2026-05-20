from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from consultations.models import Consultation, DossierPatient
from facturation.models import Facture, LigneFacture, Paiement
from facturation.views import _finance_stats
from medecins.models import Medecin
from patients.models import Patient
from rendez_vous.models import RendezVous


class CaissierFactureModificationTests(TestCase):
    def setUp(self):
        self.caissier = User.objects.create_user(
            email="caissier-flow@example.test",
            password="demo12345",
            role="caissier",
        )
        medecin = Medecin.objects.create(
            user=User.objects.create_user(
                email="medecin-facture@example.test",
                password="demo12345",
                role="medecin",
            ),
            specialite="Cardiologie",
            tarif_consultation=Decimal("300.00"),
            actif=True,
        )
        patient = Patient.objects.create(
            user=User.objects.create_user(
                email="patient-facture@example.test",
                password="demo12345",
                role="patient",
            ),
            num_dossier="P-FACT",
            date_naissance=date(1990, 1, 1),
        )
        dossier, _created = DossierPatient.objects.get_or_create(
            patient=patient,
            defaults={"num_dossier": "D-P-FACT"},
        )
        rdv = RendezVous.objects.create(
            patient=patient,
            medecin=medecin,
            date_heure=timezone.now(),
            motif="Controle",
            statut=RendezVous.Statut.TERMINE,
        )
        consultation = Consultation.objects.create(
            rendez_vous=rdv,
            medecin=medecin,
            patient=patient,
            dossier=dossier,
            termine=True,
        )
        self.facture = Facture.objects.create(
            consultation=consultation,
            patient=patient,
            numero="FAC-TEST-0001",
            statut=Facture.Statut.BROUILLON,
        )
        self.ligne = LigneFacture.objects.create(
            facture=self.facture,
            libelle="Consultation",
            quantite=1,
            prix_unitaire=Decimal("300.00"),
        )
        self.facture.calculer_total()

    def test_cashier_can_update_invoice_line_and_total(self):
        self.client.force_login(self.caissier)

        response = self.client.post(
            reverse("facturation:facture_detail", args=[self.facture.pk]),
            {
                "update_ligne": "1",
                "ligne_id": str(self.ligne.pk),
                "libelle": "Consultation specialisee",
                "quantite": "2",
                "prix_unitaire": "200.00",
            },
        )

        self.assertRedirects(
            response,
            reverse("facturation:facture_detail", args=[self.facture.pk]),
            fetch_redirect_response=False,
        )
        self.ligne.refresh_from_db()
        self.facture.refresh_from_db()
        self.assertEqual(self.ligne.libelle, "Consultation specialisee")
        self.assertEqual(self.ligne.quantite, 2)
        self.assertEqual(self.facture.total_ttc, Decimal("400.00"))

    def test_cashier_can_delete_invoice_line_and_total_is_recalculated(self):
        self.client.force_login(self.caissier)

        response = self.client.post(
            reverse("facturation:facture_detail", args=[self.facture.pk]),
            {
                "delete_ligne": "1",
                "ligne_id": str(self.ligne.pk),
            },
        )

        self.assertRedirects(
            response,
            reverse("facturation:facture_detail", args=[self.facture.pk]),
            fetch_redirect_response=False,
        )
        self.facture.refresh_from_db()
        self.assertFalse(LigneFacture.objects.filter(pk=self.ligne.pk).exists())
        self.assertEqual(self.facture.total_ttc, Decimal("0.00"))

    def test_paying_invoice_updates_dashboard_stats(self):
        self.client.force_login(self.caissier)

        before = _finance_stats()
        response = self.client.post(
            reverse("facturation:facture_detail", args=[self.facture.pk]),
            {
                "encaisser": "1",
                "montant": "300.00",
                "mode": Paiement.Mode.ESPECES,
            },
            follow=True,
        )

        self.facture.refresh_from_db()
        after = _finance_stats()
        self.assertRedirects(response, reverse("facturation:caissier_dashboard"))
        self.assertEqual(self.facture.statut, Facture.Statut.PAYEE)
        self.assertEqual(after["paid_consultations"], before["paid_consultations"] + 1)
        self.assertEqual(after["unpaid_consultations"], before["unpaid_consultations"] - 1)
        self.assertContains(response, "Consultations payees")
