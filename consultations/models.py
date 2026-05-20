import re

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from clinic_common.clinical_specialties import (
    answer_rows,
    risk_points_for_answers,
    specialty_label,
)


class DossierPatient(models.Model):
    patient = models.OneToOneField(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="dossier",
        verbose_name=_("patient"),
    )
    num_dossier = models.CharField(_("numéro de dossier médical"), max_length=20, unique=True)
    antecedents = models.TextField(_("antécédents"), blank=True)
    allergies = models.TextField(_("allergies"), blank=True)
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)

    class Meta:
        verbose_name = _("dossier patient")
        verbose_name_plural = _("dossiers patients")

    def __str__(self) -> str:
        return f"Dossier {self.num_dossier}"


class Consultation(models.Model):
    class RiskLevel(models.TextChoices):
        FAIBLE = "faible", _("Faible risque")
        MOYEN = "moyen", _("Risque moyen")
        ELEVE = "eleve", _("Risque eleve")

    rendez_vous = models.OneToOneField(
        "rendez_vous.RendezVous",
        on_delete=models.CASCADE,
        related_name="consultation",
        verbose_name=_("rendez-vous"),
    )
    medecin = models.ForeignKey(
        "medecins.Medecin",
        on_delete=models.CASCADE,
        related_name="consultations",
        verbose_name=_("médecin"),
    )
    patient = models.ForeignKey(
        "patients.Patient",
        on_delete=models.CASCADE,
        related_name="consultations",
        verbose_name=_("patient"),
    )
    dossier = models.ForeignKey(
        DossierPatient,
        on_delete=models.CASCADE,
        related_name="consultations",
        verbose_name=_("dossier"),
    )
    date = models.DateTimeField(_("date"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifie le"), auto_now=True)
    tension = models.CharField(_("tension"), max_length=20, blank=True)
    poids = models.DecimalField(
        _("poids (kg)"),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    temperature = models.DecimalField(
        _("température (°C)"),
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
    )
    symptomes = models.TextField(_("symptomes"), blank=True)
    diagnostic = models.TextField(_("diagnostic"), blank=True)
    maladies_chroniques = models.TextField(_("maladies chroniques"), blank=True)
    traitement = models.TextField(_("traitement"), blank=True)
    compte_rendu = models.TextField(_("compte rendu"), blank=True)
    specialite_snapshot = models.CharField(
        _("specialite formulaire"),
        max_length=100,
        blank=True,
    )
    reponses_specialite = models.JSONField(
        _("reponses specialisees"),
        default=dict,
        blank=True,
    )
    risk_score = models.PositiveSmallIntegerField(_("score de risque IA"), default=0)
    risk_level = models.CharField(
        _("niveau de risque"),
        max_length=20,
        choices=RiskLevel.choices,
        default=RiskLevel.FAIBLE,
    )
    risk_analyzed_at = models.DateTimeField(_("analyse IA le"), null=True, blank=True)
    termine = models.BooleanField(_("terminé"), default=False)

    class Meta:
        ordering = ["-updated_at", "-date"]
        verbose_name = _("consultation")
        verbose_name_plural = _("consultations")

    def __str__(self) -> str:
        return f"Consultation {self.patient} — {self.date:%d/%m/%Y %H:%M}"


    def patient_age(self) -> int:
        if not self.patient_id or not self.patient.date_naissance:
            return 0
        today = timezone.localdate()
        born = self.patient.date_naissance
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

    def _tension_numbers(self) -> tuple[int | None, int | None]:
        values = [int(v) for v in re.findall(r"\d+", self.tension or "")[:2]]
        if not values:
            return None, None
        if len(values) == 1:
            value = values[0]
            if value < 30:
                value *= 10
            return value, None
        systolic, diastolic = values[0], values[1]
        if systolic < 30:
            systolic *= 10
        if diastolic < 30:
            diastolic *= 10
        return systolic, diastolic

    def calculate_risk_score(self) -> int:
        score = 8
        age = self.patient_age()
        if age >= 75:
            score += 22
        elif age >= 60:
            score += 14
        elif age >= 45:
            score += 6

        if self.temperature is not None:
            temp = float(self.temperature)
            if temp >= 39:
                score += 24
            elif temp >= 38:
                score += 14
            elif temp < 35.5:
                score += 12

        systolic, diastolic = self._tension_numbers()
        if (systolic and systolic >= 180) or (diastolic and diastolic >= 110):
            score += 28
        elif (systolic and systolic >= 160) or (diastolic and diastolic >= 100):
            score += 20
        elif (systolic and systolic >= 140) or (diastolic and diastolic >= 90):
            score += 10

        if not self.reponses_specialite:
            chronic = (self.maladies_chroniques or "").lower()
            symptoms = (self.symptomes or "").lower()
            diagnostic = (self.diagnostic or "").lower()
            chronic_terms = (
                "diab",
                "hypertension",
                "card",
                "asth",
                "renal",
                "rein",
                "cancer",
            )
            severe_terms = (
                "douleur thoracique",
                "dysp",
                "essoufflement",
                "perte de connaissance",
                "syncope",
                "avc",
                "convulsion",
            )
            moderate_terms = (
                "fievre",
                "fiÃ¨vre",
                "vom",
                "vertige",
                "douleur",
                "infection",
            )
            if any(term in chronic for term in chronic_terms):
                score += 16
            if any(term in symptoms for term in severe_terms):
                score += 24
            elif any(term in symptoms for term in moderate_terms):
                score += 10
            if any(term in diagnostic for term in severe_terms):
                score += 12
        score += risk_points_for_answers(
            self.specialite_snapshot or getattr(self.medecin, "specialite", ""),
            self.reponses_specialite,
        )
        return max(0, min(100, score))

    def refresh_risk(self) -> None:
        self.risk_score = self.calculate_risk_score()
        if self.risk_score >= 70:
            self.risk_level = self.RiskLevel.ELEVE
        elif self.risk_score >= 35:
            self.risk_level = self.RiskLevel.MOYEN
        else:
            self.risk_level = self.RiskLevel.FAIBLE
        self.risk_analyzed_at = timezone.now()

    @property
    def risk_percent(self) -> int:
        return max(0, min(100, self.risk_score or 0))

    @property
    def risk_label(self) -> str:
        return {
            self.RiskLevel.FAIBLE: "Etat stable",
            self.RiskLevel.MOYEN: "Surveillance necessaire",
            self.RiskLevel.ELEVE: "Attention rapide",
        }.get(self.risk_level, "Etat stable")

    @property
    def specialite_formulaire_label(self) -> str:
        return specialty_label(
            self.specialite_snapshot or getattr(self.medecin, "specialite", "")
        )

    @property
    def reponses_specialite_list(self) -> list[dict]:
        return answer_rows(
            self.specialite_snapshot or getattr(self.medecin, "specialite", ""),
            self.reponses_specialite,
        )

    def save(self, *args, **kwargs):
        if self.patient_id:
            self.refresh_risk()
            update_fields = kwargs.get("update_fields")
            if update_fields is not None:
                kwargs["update_fields"] = set(update_fields) | {
                    "updated_at",
                    "risk_score",
                    "risk_level",
                    "risk_analyzed_at",
                }
        super().save(*args, **kwargs)


class Ordonnance(models.Model):
    consultation = models.OneToOneField(
        Consultation,
        on_delete=models.CASCADE,
        related_name="ordonnance",
        verbose_name=_("consultation"),
    )
    date = models.DateField(_("date"), auto_now_add=True)
    valide_jusqu = models.DateField(_("valide jusqu'au"))

    class Meta:
        verbose_name = _("ordonnance")
        verbose_name_plural = _("ordonnances")

    def __str__(self) -> str:
        return f"Ordonnance du {self.date}"


class LigneOrdonnance(models.Model):
    ordonnance = models.ForeignKey(
        Ordonnance,
        on_delete=models.CASCADE,
        related_name="lignes",
        verbose_name=_("ordonnance"),
    )
    medicament = models.CharField(_("médicament"), max_length=200)
    dosage = models.CharField(_("dosage"), max_length=100)
    duree = models.CharField(_("durée"), max_length=100)
    instructions = models.TextField(_("instructions"), blank=True)

    class Meta:
        verbose_name = _("ligne d'ordonnance")
        verbose_name_plural = _("lignes d'ordonnance")
