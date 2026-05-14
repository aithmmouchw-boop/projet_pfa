from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django import forms


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
