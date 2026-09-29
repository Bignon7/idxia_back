"""
model_loader.py

Charge une seule fois, au demarrage de l'API, tout ce qui a ete produit
par le pipeline d'entrainement (dossier model/models/) :
- le modele (Random Forest ou XGBoost, peu importe lequel a ete retenu)
- les encodeurs des colonnes categorielles
- l'ordre exact des colonnes utilise a l'entrainement
- un explainer SHAP pret a l'emploi
"""

import glob
import os

import joblib
import shap

MODEL_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "model", "models"
)


def _find_model_path() -> str:
    candidates = glob.glob(os.path.join(MODEL_DIR, "idxia_model_*.pkl"))
    if not candidates:
        raise FileNotFoundError(
            f"Aucun modele trouve dans {MODEL_DIR}. "
            "Lance model/src/train_model.py avant de demarrer l'API."
        )
    return max(candidates, key=os.path.getmtime)


class ModelArtifacts:
    """Regroupe tout ce dont l'API a besoin pour predire et expliquer."""

    def __init__(self):
        model_path = _find_model_path()
        self.model = joblib.load(model_path)
        self.encoders = joblib.load(os.path.join(MODEL_DIR, "idxia_encoders.pkl"))
        self.feature_cols = joblib.load(
            os.path.join(MODEL_DIR, "idxia_feature_cols.pkl")
        )
        self.explainer = shap.TreeExplainer(self.model)
        print(f"[model_loader] Modele charge depuis : {model_path}")


# Instance unique, chargee une seule fois au demarrage du process FastAPI
artifacts = ModelArtifacts()