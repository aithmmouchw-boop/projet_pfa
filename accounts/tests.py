from django.test import SimpleTestCase

from accounts.forms import AesculiaSignupForm


class SignupFormTests(SimpleTestCase):
    def test_public_signup_roles_are_patient_and_medecin_only(self):
        choices = [value for value, _label in AesculiaSignupForm().fields["role"].choices]

        self.assertEqual(choices, ["patient", "medecin"])
