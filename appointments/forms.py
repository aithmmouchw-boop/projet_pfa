from django import forms

from .models import AppointmentRequest


class AppointmentRequestForm(forms.ModelForm):
    doctor_ref = forms.CharField(required=False, widget=forms.HiddenInput)
    service_ref = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = AppointmentRequest
        fields = (
            "full_name",
            "email",
            "phone",
            "message",
            "doctor_ref",
            "service_ref",
        )
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "autocomplete": "name",
                    "placeholder": "Votre nom",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "autocomplete": "email",
                    "placeholder": "vous@exemple.ch",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "autocomplete": "tel",
                    "placeholder": "+41 …",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Créneau souhaité, motif de consultation…",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self._user = user
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            if not self.initial.get("full_name"):
                fn = (user.get_full_name() or "").strip()
                self.initial["full_name"] = fn
            if not self.initial.get("email"):
                self.initial["email"] = user.email
            self.fields["email"].widget.attrs["readonly"] = True

    def clean_email(self):
        if self._user and self._user.is_authenticated:
            return self._user.email
        return self.cleaned_data.get("email") or ""
