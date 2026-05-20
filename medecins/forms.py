from django import forms
from django.forms import inlineformset_factory

from clinic_common.clinical_specialties import (
    YES_NO_CHOICES,
    format_answers,
    format_category,
    questions_for_specialty,
    specialty_label,
)
from consultations.models import Consultation, LigneOrdonnance, Ordonnance


class ConsultationMedecinForm(forms.ModelForm):
    field_prefix = "question__"

    class Meta:
        model = Consultation
        fields = ()

    def __init__(self, *args, specialite=None, **kwargs):
        super().__init__(*args, **kwargs)
        instance_specialite = ""
        if self.instance and getattr(self.instance, "pk", None):
            instance_specialite = (
                self.instance.specialite_snapshot
                or getattr(self.instance.medecin, "specialite", "")
            )
        self.specialite_label = specialty_label(specialite or instance_specialite)
        self.questions = questions_for_specialty(self.specialite_label)
        current_answers = self.instance.reponses_specialite or {}
        for question in self.questions:
            name = self.question_field_name(question["key"])
            self.fields[name] = forms.ChoiceField(
                label=question["label"],
                choices=YES_NO_CHOICES,
                required=True,
                widget=forms.RadioSelect,
            )
            if current_answers.get(question["key"]) in {"oui", "non"}:
                self.fields[name].initial = current_answers[question["key"]]

    @classmethod
    def question_field_name(cls, key: str) -> str:
        return f"{cls.field_prefix}{key}"

    def save(self, commit=True):
        instance = super().save(commit=False)
        answers = {}
        for question in self.questions:
            answers[question["key"]] = self.cleaned_data[
                self.question_field_name(question["key"])
            ]

        instance.specialite_snapshot = self.specialite_label
        instance.reponses_specialite = answers
        instance.compte_rendu = format_answers(self.specialite_label, answers)
        instance.symptomes = format_category(self.specialite_label, answers, "symptomes")
        instance.maladies_chroniques = format_category(
            self.specialite_label,
            answers,
            "maladies_chroniques",
        )
        instance.diagnostic = format_category(self.specialite_label, answers, "diagnostic")
        instance.traitement = format_category(self.specialite_label, answers, "traitement")
        if commit:
            instance.save()
        return instance


class LigneOrdonnanceForm(forms.ModelForm):
    class Meta:
        model = LigneOrdonnance
        fields = ("medicament", "dosage", "duree", "instructions")
        widgets = {
            "medicament": forms.TextInput(attrs={"placeholder": "Médicament"}),
            "dosage": forms.TextInput(attrs={"placeholder": "Dosage"}),
            "duree": forms.TextInput(attrs={"placeholder": "Durée"}),
            "instructions": forms.Textarea(attrs={"rows": 2, "placeholder": "Instructions"}),
        }


LigneOrdonnanceFormSet = inlineformset_factory(
    Ordonnance,
    LigneOrdonnance,
    form=LigneOrdonnanceForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False,
)
