from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django import forms

from medecins.models import Medecin
from patients.models import Patient
from patients.utils import generer_num_dossier

from .models import User


ROLE_CHOICES_INSCRIPTION = [
    ("patient", "Patient"),
    ("medecin", "Medecin"),
    ("infirmier", "Secretaire"),
    ("caissier", "Caissier"),
]


class AesculiaLoginForm(AuthenticationForm):
    """Formulaire connexion : champ interne ``username`` = e-mail (compat. Django)."""

    username = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "votre@email.com",
                "autocomplete": "email",
                "class": "auth-input-native",
            }
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "••••••••",
                "autocomplete": "current-password",
                "class": "auth-input-native",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = ""
        self.fields["password"].label = ""


class AesculiaSignupForm(forms.Form):
    first_name = forms.CharField(
        label="Prenom",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Votre prenom",
                "autocomplete": "given-name",
                "class": "auth-input-native",
            }
        ),
    )
    last_name = forms.CharField(
        label="Nom",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Votre nom",
                "autocomplete": "family-name",
                "class": "auth-input-native",
            }
        ),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(
            attrs={
                "placeholder": "votre@email.com",
                "autocomplete": "email",
                "class": "auth-input-native",
            }
        ),
    )
    role = forms.ChoiceField(
        label="Role",
        choices=ROLE_CHOICES_INSCRIPTION,
        widget=forms.Select(attrs={"class": "auth-input-native auth-select-native"}),
    )
    password1 = forms.CharField(
        label="Mot de passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "********",
                "autocomplete": "new-password",
                "class": "auth-input-native",
            }
        ),
    )
    password2 = forms.CharField(
        label="Confirmer le mot de passe",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "********",
                "autocomplete": "new-password",
                "class": "auth-input-native",
            }
        ),
    )
    date_naissance = forms.DateField(
        label="Date de naissance",
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "auth-input-native",
            }
        ),
    )
    telephone = forms.CharField(
        label="Telephone",
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "+212 ...",
                "autocomplete": "tel",
                "class": "auth-input-native",
            }
        ),
    )
    adresse = forms.CharField(
        label="Adresse",
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "Votre adresse",
                "autocomplete": "street-address",
                "class": "auth-input-native auth-textarea-native",
            }
        ),
    )
    specialite = forms.CharField(
        label="Specialite",
        max_length=100,
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ex. Medecine generale",
                "class": "auth-input-native",
            }
        ),
    )
    tarif_consultation = forms.DecimalField(
        label="Tarif consultation",
        required=False,
        max_digits=8,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(
            attrs={
                "placeholder": "150.00",
                "step": "0.01",
                "class": "auth-input-native",
            }
        ),
    )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Un compte existe deja avec cet e-mail.")
        return email

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role")
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Les deux mots de passe ne correspondent pas.")

        if password1:
            try:
                validate_password(password1)
            except ValidationError as exc:
                self.add_error("password1", exc)

        if role == "admin":
            self.add_error(
                "role",
                "Le compte administrateur est reserve. Utilisez les identifiants admin fournis.",
            )
        elif role == "patient" and not cleaned.get("date_naissance"):
            self.add_error("date_naissance", "La date de naissance est obligatoire.")
        elif role == "medecin":
            if not cleaned.get("specialite"):
                self.add_error("specialite", "La specialite est obligatoire.")
            if cleaned.get("tarif_consultation") is None:
                self.add_error(
                    "tarif_consultation",
                    "Le tarif de consultation est obligatoire.",
                )

        return cleaned

    @transaction.atomic
    def save(self):
        role = self.cleaned_data["role"]
        user = User.objects.create_user(
            email=self.cleaned_data["email"],
            password=self.cleaned_data["password1"],
            first_name=self.cleaned_data["first_name"].strip(),
            last_name=self.cleaned_data["last_name"].strip(),
            role=role,
        )

        if role == "patient":
            Patient.objects.create(
                user=user,
                num_dossier=generer_num_dossier(),
                date_naissance=self.cleaned_data["date_naissance"],
                telephone=self.cleaned_data.get("telephone", ""),
                adresse=self.cleaned_data.get("adresse", ""),
            )
        elif role == "medecin":
            Medecin.objects.create(
                user=user,
                specialite=self.cleaned_data["specialite"].strip(),
                tarif_consultation=self.cleaned_data["tarif_consultation"],
                actif=True,
            )

        return user


class AesculiaPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="",
        max_length=254,
        widget=forms.EmailInput(
            attrs={
                "placeholder": "votre@email.com",
                "autocomplete": "email",
                "class": "auth-input-native",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].label = ""


class AesculiaSetPasswordForm(SetPasswordForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        for name in ("new_password1", "new_password2"):
            self.fields[name].label = ""
            self.fields[name].widget.attrs.update(
                {
                    "class": "auth-input-native",
                    "placeholder": "••••••••",
                    "autocomplete": "new-password",
                }
            )
