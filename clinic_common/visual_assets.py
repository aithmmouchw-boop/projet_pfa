from __future__ import annotations

import hashlib


DOCTOR_PHOTOS = (
    "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1622253692010-333f2da6031d?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1582750433449-648ed127bb54?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&w=900&q=80",
)

NAMED_DOCTOR_PHOTOS = {
    "wafae": "https://images.pexels.com/photos/33055499/pexels-photo-33055499.jpeg?auto=compress&cs=tinysrgb&fit=crop&w=900&h=900",
    "ait hmmouch": "https://images.pexels.com/photos/33055499/pexels-photo-33055499.jpeg?auto=compress&cs=tinysrgb&fit=crop&w=900&h=900",
    "chaimaa": "https://images.pexels.com/photos/32254665/pexels-photo-32254665.jpeg?auto=compress&cs=tinysrgb&fit=crop&w=900&h=900",
    "elgharzaoui": "https://images.pexels.com/photos/32254665/pexels-photo-32254665.jpeg?auto=compress&cs=tinysrgb&fit=crop&w=900&h=900",
}

CABINET_PHOTOS = {
    "cardiologie": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=1100&q=80",
    "ophtalmologie": "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?auto=format&fit=crop&w=1100&q=80",
    "default": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?auto=format&fit=crop&w=1100&q=80",
}


def _pick(items: tuple[str, ...], seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8", errors="ignore")).hexdigest()
    return items[int(digest[:8], 16) % len(items)]


def _text(value) -> str:
    return (value or "").strip().casefold()


def named_doctor_photo_url(name: str) -> str | None:
    normalized = _text(name)
    for marker, url in NAMED_DOCTOR_PHOTOS.items():
        if marker in normalized:
            return url
    return None


def cabinet_photo_for_specialty(specialite: str | None) -> str:
    normalized = _text(specialite)
    if "cardio" in normalized or "coeur" in normalized:
        return CABINET_PHOTOS["cardiologie"]
    if "ophtal" in normalized or "oeil" in normalized or "yeux" in normalized:
        return CABINET_PHOTOS["ophtalmologie"]
    return CABINET_PHOTOS["default"]


def medecin_photo_url(medecin) -> str:
    photo = getattr(medecin, "photo", None)
    if photo:
        try:
            return photo.url
        except ValueError:
            pass
    user = getattr(medecin, "user", None)
    name = ""
    if user is not None:
        name = user.get_full_name() or user.email
    named_photo = named_doctor_photo_url(name)
    if named_photo:
        return named_photo
    seed = f"{name} {getattr(medecin, 'specialite', '')}"
    return _pick(DOCTOR_PHOTOS, seed)


def attach_medecin_visuals(medecins):
    prepared = list(medecins)
    for medecin in prepared:
        medecin.photo_url = medecin_photo_url(medecin)
        medecin.cabinet_photo_url = cabinet_photo_for_specialty(medecin.specialite)
    return prepared
