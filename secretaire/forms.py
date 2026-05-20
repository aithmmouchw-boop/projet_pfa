from django import forms

from consultations.models import Consultation


class ConstantesForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ("tension", "poids", "temperature")
        labels = {
            "tension": "Tension arterielle",
            "poids": "Poids",
            "temperature": "Temperature",
        }
        widgets = {
            "tension": forms.TextInput(
                attrs={"class": "dash-input", "placeholder": "ex. 120/80"}
            ),
            "poids": forms.NumberInput(
                attrs={"class": "dash-input", "placeholder": "kg", "step": "0.1"}
            ),
            "temperature": forms.NumberInput(
                attrs={"class": "dash-input", "placeholder": "deg C", "step": "0.1"}
            ),
        }
