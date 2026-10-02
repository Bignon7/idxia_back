"""
predict.py

Convertit une SessionInput (donnees brutes recues par l'API) dans le
meme format que celui utilise a l'entrainement, applique le modele,
puis utilise SHAP pour expliquer la decision.
"""

import numpy as np
import pandas as pd

from app.explain_text import generate_explanation_text
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


def _get_class1_contributions(shap_values, feature_cols: list, raw_session: dict) -> list:
    """Extrait les valeurs SHAP de la classe 'attaque' (1) pour le seul
    echantillon envoye, quelle que soit la version de shap installee, et
    les associe a la valeur BRUTE (non encodee) de chaque feature, pour
    pouvoir generer une explication textuelle lisible ensuite.

    - Anciennes versions de shap : shap_values est une liste
      [array_classe_0, array_classe_1], chaque array de forme
      (n_echantillons, n_features).
    - Versions recentes : shap_values est un seul array numpy de forme
      (n_echantillons, n_features, n_classes).
    """
    if isinstance(shap_values, list):
        class1_values = shap_values[1][0]
    else:
        values = np.asarray(shap_values)
        if values.ndim == 3:
            class1_values = values[0, :, 1]
        else:
            class1_values = values[0]

    return [
        {"feature": name, "impact": float(impact), "value": raw_session.get(name)}
        for name, impact in zip(feature_cols, class1_values)
    ]


def predict_session(session: SessionInput) -> dict:
    raw_session = session.model_dump()
    X = _encode_session(session)

    probability_attack = float(artifacts.model.predict_proba(X)[0][1])
    prediction = int(probability_attack >= 0.5)
    risk_level = _risk_level(probability_attack)

    shap_values = artifacts.explainer.shap_values(X)
    contributions = _get_class1_contributions(
        shap_values, artifacts.feature_cols, raw_session
    )
    contributions.sort(key=lambda c: abs(c["impact"]), reverse=True)
    top_factors = contributions[:3]

    explanation_text = generate_explanation_text(
        top_factors, prediction, probability_attack, risk_level
    )

    return {
        "prediction": prediction,
        "risk_level": risk_level,
        "probability_attack": probability_attack,
        "top_factors": top_factors,
        "explanation_text": explanation_text,
    }