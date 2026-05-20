from __future__ import annotations

from django.utils import timezone

from facturation.models import Facture


def next_facture_numero() -> str:
    year = timezone.now().year
    prefix = f"FAC-{year}-"
    last = (
        Facture.objects.filter(numero__startswith=prefix).order_by("-numero").first()
    )
    if last is None:
        return f"{prefix}0001"
    try:
        tail = int(last.numero.replace(prefix, ""))
    except ValueError:
        tail = 0
    return f"{prefix}{tail + 1:04d}"


def refresh_facture_totals_and_status(facture: Facture) -> Facture:
    facture.calculer_total()
    if facture.statut == Facture.Statut.ANNULEE:
        return facture
    total_paye = facture.total_paye_valide()
    if facture.total_ttc <= 0:
        next_status = Facture.Statut.BROUILLON
    elif total_paye >= facture.total_ttc:
        next_status = Facture.Statut.PAYEE
    elif total_paye > 0 or facture.statut in (Facture.Statut.EMISE, Facture.Statut.PAYEE):
        next_status = Facture.Statut.EMISE
    else:
        next_status = Facture.Statut.BROUILLON
    if facture.statut != next_status:
        facture.statut = next_status
        facture.save(update_fields=["statut"])
    return facture
