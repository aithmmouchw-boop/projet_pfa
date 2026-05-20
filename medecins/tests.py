from django.test import SimpleTestCase

from consultations.models import Consultation
from medecins.forms import ConsultationMedecinForm
from medecins.models import Medecin


class ConsultationMedecinFormTests(SimpleTestCase):
    def test_cardiologie_form_uses_specialty_questions(self):
        consultation = Consultation(medecin=Medecin(specialite="Cardiologie"))

        form = ConsultationMedecinForm(
            instance=consultation,
            specialite="Cardiologie",
        )

        self.assertIn("question__douleur_thoracique", form.fields)
        self.assertIn("question__ecg_normal", form.fields)
        self.assertNotIn("question__vision_floue", form.fields)

    def test_form_stores_yes_no_answers_in_consultation(self):
        consultation = Consultation(medecin=Medecin(specialite="Cardiologie"))
        blank_form = ConsultationMedecinForm(
            instance=consultation,
            specialite="Cardiologie",
        )
        data = {name: "non" for name in blank_form.fields}
        data["question__douleur_thoracique"] = "oui"

        form = ConsultationMedecinForm(
            data=data,
            instance=consultation,
            specialite="Cardiologie",
        )

        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save(commit=False)
        self.assertEqual(saved.specialite_snapshot, "Cardiologie")
        self.assertEqual(saved.reponses_specialite["douleur_thoracique"], "oui")
        self.assertIn("Douleur thoracique: Oui", saved.symptomes)
