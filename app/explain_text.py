"""
explain_text.py

Transforme les facteurs SHAP (numeriques) en une phrase comprehensible
par un analyste SOC, sans dependre d'un appel a une IA externe.
Deterministe, rapide, fiable pour une demo en direct.
"""

FEATURE_LABELS_FR = {
    "network_packet_size": "la taille des paquets réseau",
    "protocol_type": "le protocole réseau utilisé",
    "login_attempts": "le nombre de tentatives de connexion",
    "session_duration": "la durée de la session",
    "encryption_used": "le type de chiffrement utilisé",
    "ip_reputation_score": "la réputation de l'adresse IP",
    "failed_logins": "le nombre d'échecs de connexion",
    "browser_type": "le navigateur utilisé",
    "unusual_time_access": "l'heure d'accès inhabituelle",
}

RISK_LABELS_FR = {
    "critique": "critique",
    "eleve": "élevé",
    "moyen": "moyen",
    "faible": "faible",
}


def _format_value(feature: str, value) -> str:
    if feature == "unusual_time_access":
        return "oui" if value in (1, True, "1") else "non"
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)


def generate_explanation_text(
    factors_with_values: list, prediction: int, probability: float, risk_level: str
) -> str:
    """
    factors_with_values : liste de dicts {"feature", "impact", "value"}
    deja triee par importance (valeur absolue de l'impact decroissante).
    """
    verdict = "une activité suspecte" if prediction == 1 else "une activité normale"
    risk_fr = RISK_LABELS_FR.get(risk_level, risk_level)

    phrases = []
    for f in factors_with_values:
        label = FEATURE_LABELS_FR.get(f["feature"], f["feature"])
        value_str = _format_value(f["feature"], f["value"])
        if f["impact"] > 0:
            direction = "renforce le soupçon"
        else:
            direction = "atténue légèrement le soupçon"
        phrases.append(f"{label} ({value_str}) {direction}")

    reasons_text = ", ".join(phrases)

    return (
        f"Session classée comme {verdict} avec une confiance de "
        f"{probability * 100:.0f} % (risque {risk_fr}). "
        f"Facteurs déterminants : {reasons_text}."
    )