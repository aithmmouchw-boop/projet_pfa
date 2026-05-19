from django import forms

from consultations.models import Consultation


class ConstantesForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ("tension", "poids", "temperature")
        widgets = {
            "tension": forms.TextInput(attrs={"placeholder": "ex. 120/80"}),
            "poids": forms.NumberInput(attrs={"placeholder": "kg", "step": "0.1"}),
            "temperature": forms.NumberInput(attrs={"placeholder": "°C", "step": "0.1"}),
        }
