# IDXIA — Backend (API FastAPI)

Sert le modèle entraîné dans `../model/models/` via une API HTTP.

## Prérequis

Avoir déjà lancé `model/src/train_model.py` au moins une fois, pour que
`../model/models/` contienne le modèle, les encodeurs et l'ordre des colonnes.

## Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate      # sous Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement

```bash
uvicorn app.main:app --reload --port 8000
```

Documentation interactive (Swagger) : http://localhost:8000/docs

## Test rapide

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
        "network_packet_size": 599,
        "protocol_type": "TCP",
        "login_attempts": 12,
        "session_duration": 45.2,
        "encryption_used": "None",
        "ip_reputation_score": 0.82,
        "failed_logins": 9,
        "browser_type": "Unknown",
        "unusual_time_access": 1
      }'
```

Réponse attendue : un JSON avec `prediction` (0 ou 1), `risk_level`,
`probability_attack` et `top_factors` (les 3 facteurs SHAP les plus
déterminants pour cette session).