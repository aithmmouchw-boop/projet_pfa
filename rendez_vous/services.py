from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Iterator

from django.utils import timezone

from medecins.models import Medecin
from patients.models import Patient
from rendez_vous.models import RendezVous

# Statuts qui bloquent un creneau deja pris.
_STATUTS_OCCUPATION = (
    RendezVous.Statut.PLANIFIE,
    RendezVous.Statut.CONFIRME,
    RendezVous.Statut.ARRIVE,
    RendezVous.Statut.EN_COURS,
)


def creneaux_libres(medecin: Medecin, jour: date) -> Iterator[datetime]:
    """Itere les debuts de creneaux libres entre 08:00 et 17:30."""
    for slot in creneaux_jour(medecin, jour):
        if not slot["occupe"]:
            yield slot["dt"]


def creneaux_jour(medecin: Medecin, jour: date) -> list[dict]:
    """Retourne tous les creneaux du jour, libres et occupes."""
    debut_jour = timezone.make_aware(datetime.combine(jour, time(8, 0)))
    fin_jour = timezone.make_aware(datetime.combine(jour, time(17, 30)))
    rdvs = {
        rdv.date_heure: rdv
        for rdv in RendezVous.objects.filter(
            medecin=medecin,
            date_heure__date=jour,
            statut__in=_STATUTS_OCCUPATION,
        ).select_related("patient__user")
    }
    slots = []
    cur = debut_jour
    step = timedelta(minutes=30)
    while cur <= fin_jour:
        rdv = rdvs.get(cur)
        slots.append(
            {
                "dt": cur,
                "iso": cur.isoformat(),
                "occupe": rdv is not None,
                "rdv": rdv,
                "statut": rdv.statut if rdv else "",
                "statut_label": rdv.get_statut_display() if rdv else "Disponible",
            }
        )
        cur += step
    return slots


def creneau_est_occupe(medecin: Medecin, date_heure: datetime) -> bool:
    return RendezVous.objects.filter(
        medecin=medecin,
        date_heure=date_heure,
        statut__in=_STATUTS_OCCUPATION,
    ).exists()


def prochains_jours(n: int = 14) -> list[date]:
    today = timezone.localdate()
    return [today + timedelta(days=i) for i in range(n)]


def ensure_dossier_for_patient(patient: Patient):
    from consultations.models import DossierPatient

    dossier, _created = DossierPatient.objects.get_or_create(
        patient=patient,
        defaults={"num_dossier": f"D-{patient.num_dossier}"},
    )
    return dossier


def ensure_consultation_for_rdv(rdv: RendezVous):
    """Create or resync the consultation that belongs to a rendez-vous."""
    from consultations.models import Consultation
    from facturation.models import Facture

    dossier = ensure_dossier_for_patient(rdv.patient)
    consultation, created = Consultation.objects.get_or_create(
        rendez_vous=rdv,
        defaults={
            "medecin": rdv.medecin,
            "patient": rdv.patient,
            "dossier": dossier,
        },
    )
    update_fields = []
    if not created:
        if consultation.medecin_id != rdv.medecin_id:
            consultation.medecin = rdv.medecin
            update_fields.append("medecin")
        if consultation.patient_id != rdv.patient_id:
            consultation.patient = rdv.patient
            update_fields.append("patient")
        if consultation.dossier_id != dossier.pk:
            consultation.dossier = dossier
            update_fields.append("dossier")
        if update_fields:
            consultation.save(update_fields=update_fields)
    try:
        facture = consultation.facture
    except Facture.DoesNotExist:
        facture = None
    if facture and facture.patient_id != consultation.patient_id:
        facture.patient = consultation.patient
        facture.save(update_fields=["patient"])
    return consultation, created
