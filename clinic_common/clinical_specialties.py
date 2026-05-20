import unicodedata


YES = "oui"
NO = "non"

YES_NO_CHOICES = (
    (YES, "Oui"),
    (NO, "Non"),
)

SPECIALTY_LABELS = {
    "medecine_generale": "Medecine generale",
    "cardiologie": "Cardiologie",
    "ophtalmologie": "Ophtalmologie",
}

SPECIALTY_CHOICES = tuple((label, label) for label in SPECIALTY_LABELS.values())

SPECIALTY_KEYWORDS = {
    "cardiologie": (
        "cardio",
        "coeur",
        "heart",
        "qalb",
        "9alb",
        "l9alb",
    ),
    "ophtalmologie": (
        "ophtal",
        "ophthal",
        "oeil",
        "yeux",
        "eye",
        "ocul",
        "3in",
        "l3in",
        "lain",
    ),
}

COMMON_QUESTIONS = (
    {
        "key": "analyses_disponibles",
        "label": "Analyses disponibles",
        "category": "compte_rendu",
    },
    {
        "key": "analyses_normales",
        "label": "Analyses normales",
        "category": "diagnostic",
        "risk_if": NO,
        "risk": 12,
    },
    {
        "key": "allergies_presentes",
        "label": "Allergies presentes",
        "category": "maladies_chroniques",
        "risk_if": YES,
        "risk": 8,
    },
    {
        "key": "maladies_chroniques",
        "label": "Maladies chroniques presentes",
        "category": "maladies_chroniques",
        "risk_if": YES,
        "risk": 12,
    },
    {
        "key": "traitement_en_cours",
        "label": "Traitement deja en cours",
        "category": "traitement",
        "risk_if": YES,
        "risk": 5,
    },
)

SPECIALTY_QUESTIONS = {
    "medecine_generale": (
        {
            "key": "symptomes_presents",
            "label": "Symptomes presents",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 8,
        },
        {
            "key": "fievre_presente",
            "label": "Fievre presente",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 10,
        },
        {
            "key": "douleur_importante",
            "label": "Douleur importante",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 10,
        },
        {
            "key": "infection_suspectee",
            "label": "Infection suspectee",
            "category": "diagnostic",
            "risk_if": YES,
            "risk": 10,
        },
        {
            "key": "suivi_rapproche",
            "label": "Suivi rapproche necessaire",
            "category": "traitement",
            "risk_if": YES,
            "risk": 8,
        },
    ),
    "cardiologie": (
        {
            "key": "douleur_thoracique",
            "label": "Douleur thoracique",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 24,
        },
        {
            "key": "essoufflement",
            "label": "Essoufflement",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 20,
        },
        {
            "key": "palpitations",
            "label": "Palpitations",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 14,
        },
        {
            "key": "tension_elevee",
            "label": "Tension elevee",
            "category": "diagnostic",
            "risk_if": YES,
            "risk": 18,
        },
        {
            "key": "antecedent_cardiaque",
            "label": "Antecedent cardiaque",
            "category": "maladies_chroniques",
            "risk_if": YES,
            "risk": 16,
        },
        {
            "key": "ecg_realise",
            "label": "ECG realise",
            "category": "compte_rendu",
        },
        {
            "key": "ecg_normal",
            "label": "ECG normal",
            "category": "diagnostic",
            "risk_if": NO,
            "risk": 20,
        },
        {
            "key": "oedemes",
            "label": "Oedemes presents",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 14,
        },
    ),
    "ophtalmologie": (
        {
            "key": "vision_floue",
            "label": "Vision floue",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 10,
        },
        {
            "key": "baisse_acuite",
            "label": "Baisse d'acuite visuelle",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 16,
        },
        {
            "key": "douleur_oculaire",
            "label": "Douleur oculaire",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 12,
        },
        {
            "key": "rougeur_oculaire",
            "label": "Rougeur oculaire",
            "category": "symptomes",
            "risk_if": YES,
            "risk": 8,
        },
        {
            "key": "pression_oculaire_elevee",
            "label": "Pression oculaire elevee",
            "category": "diagnostic",
            "risk_if": YES,
            "risk": 20,
        },
        {
            "key": "fond_oeil_realise",
            "label": "Fond d'oeil realise",
            "category": "compte_rendu",
        },
        {
            "key": "fond_oeil_normal",
            "label": "Fond d'oeil normal",
            "category": "diagnostic",
            "risk_if": NO,
            "risk": 16,
        },
        {
            "key": "correction_necessaire",
            "label": "Correction lunettes/lentilles necessaire",
            "category": "traitement",
            "risk_if": YES,
            "risk": 5,
        },
    ),
}


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return ascii_value.casefold().strip()


def specialty_key_for_label(value: str | None) -> str:
    normalized = _normalize(value)
    if not normalized:
        return "medecine_generale"
    for key, label in SPECIALTY_LABELS.items():
        if normalized == _normalize(label):
            return key
    for key, keywords in SPECIALTY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return key
    return "medecine_generale"


def specialty_label(value: str | None) -> str:
    return SPECIALTY_LABELS[specialty_key_for_label(value)]


def questions_for_specialty(value: str | None) -> tuple[dict, ...]:
    key = specialty_key_for_label(value)
    return COMMON_QUESTIONS + SPECIALTY_QUESTIONS.get(
        key, SPECIALTY_QUESTIONS["medecine_generale"]
    )


def answer_label(value: str | None) -> str:
    return "Oui" if value == YES else "Non"


def is_alert_answer(question: dict, answer: str | None) -> bool:
    return bool(question.get("risk_if") and question.get("risk_if") == answer)


def answer_rows(value: str | None, answers: dict | None) -> list[dict]:
    answers = answers or {}
    rows = []
    for question in questions_for_specialty(value):
        answer = answers.get(question["key"])
        if answer not in {YES, NO}:
            continue
        rows.append(
            {
                "key": question["key"],
                "label": question["label"],
                "answer": answer_label(answer),
                "alert": is_alert_answer(question, answer),
            }
        )
    return rows


def format_answers(value: str | None, answers: dict | None) -> str:
    rows = answer_rows(value, answers)
    return "\n".join(f"{row['label']}: {row['answer']}" for row in rows)


def format_category(value: str | None, answers: dict | None, category: str) -> str:
    answers = answers or {}
    lines = []
    for question in questions_for_specialty(value):
        if question.get("category") != category:
            continue
        answer = answers.get(question["key"])
        if answer not in {YES, NO}:
            continue
        lines.append(f"{question['label']}: {answer_label(answer)}")
    return "\n".join(lines)


def risk_points_for_answers(value: str | None, answers: dict | None) -> int:
    answers = answers or {}
    score = 0
    for question in questions_for_specialty(value):
        answer = answers.get(question["key"])
        if is_alert_answer(question, answer):
            score += int(question.get("risk", 0) or 0)
    return score
