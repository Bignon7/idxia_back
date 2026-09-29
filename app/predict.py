"""
predict.py

Convertit une SessionInput (donnees brutes recues par l'API) dans le
meme format que celui utilise a l'entrainement, applique le modele,
puis utilise SHAP pour expliquer la decision.
"""

import pandas as pd

from app.model_loader import artifacts
from app.schemas import SessionInput

CATEGORICAL_COLS = ["protocol_type", "encryption_used", "browser_type"]

RISK_THRESHOLDS = [
    (0.8, "critique"),
    (0.5, "eleve"),
    (0.2, "moyen"),
]


def _risk_level(probability: float) -> str:
    for threshold, label in RISK_THRESHOLDS:
        if probability >= threshold:
            return label
    return "faible"


def _encode_session(session: SessionInput) -> pd.DataFrame:
    """Reproduit exactement l'encodage fait a l'entrainement, mais avec
    .transform() (pas .fit_transform()) puisque les encodeurs sont deja
    entraines et ne doivent pas etre reajustes ici."""
    raw = session.model_dump()
    df = pd.DataFrame([raw])

    for col in CATEGORICAL_COLS:
        encoder = artifacts.encoders[col]
        # Valeur jamais vue a l'entrainement -> on la traite comme "inconnue"
        # en tombant sur la premiere classe connue plutot que de planter.
        known_classes = set(encoder.classes_)
        df[col] = df[col].apply(lambda v: v if v in known_classes else encoder.classes_[0])
        df[col] = encoder.transform(df[col])

    # Reordonne les colonnes exactement comme a l'entrainement
    df = df[artifacts.feature_cols]
    return df


def predict_session(session: SessionInput) -> dict:
    X = _encode_session(session)

    probability_attack = float(artifacts.model.predict_proba(X)[0][1])
    prediction = int(probability_attack >= 0.5)

    shap_values = artifacts.explainer.shap_values(X)
    values = shap_values[1][0] if isinstance(shap_values, list) else shap_values[0]

    contributions = list(zip(artifacts.feature_cols, values))
    contributions.sort(key=lambda x: abs(x[1]), reverse=True)
    top_factors = [
        {"feature": name, "impact": float(impact)}
        for name, impact in contributions[:3]
    ]

    return {
        "prediction": prediction,
        "risk_level": _risk_level(probability_attack),
        "probability_attack": probability_attack,
        "top_factors": top_factors,
    }