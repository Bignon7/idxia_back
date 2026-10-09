# IDXIA — Backend (API FastAPI)

API HTTP qui sert le modèle entraîné dans `../model/models/`. Pour chaque session reçue, elle renvoie une prédiction, un niveau de risque, les facteurs SHAP déterminants et une explication en langage clair. Chaque prédiction est aussi indexée dans Elasticsearch pour être consultée dans Kibana.

## Structure

```
backend/
├── app/
│   ├── main.py            Application FastAPI, endpoints, CORS, indexation Elasticsearch
│   ├── schemas.py         Schémas d'entrée et de sortie (Pydantic)
│   ├── model_loader.py    Chargement du modèle, des encodeurs et de l'explainer SHAP
│   ├── predict.py         Encodage, prédiction, niveau de risque, facteurs SHAP
│   ├── explain_text.py    Génération de l'explication textuelle en français
│   └── es_client.py       Indexation des prédictions dans Elasticsearch
└── requirements.txt
```

## Prérequis

- Avoir lancé `model/src/train_model.py` au moins une fois : `../model/models/` doit contenir le modèle, les encodeurs et l'ordre des colonnes. Sans cela, l'API refuse de démarrer.
- Elasticsearch est optionnel pour le fonctionnement de l'API : s'il est injoignable, l'erreur est affichée dans les logs mais la prédiction est renvoyée normalement.

## Installation

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # sous Windows : venv\Scripts\activate
pip install -r requirements.txt
```

## Lancement

```bash
# Démonstration (stable)
uvicorn app.main:app --port 8000

# Développement (rechargement automatique)
uvicorn app.main:app --reload --port 8000
```

Documentation interactive (Swagger) : http://localhost:8000/docs

Variable d'environnement optionnelle : `ELASTICSEARCH_URL` (par défaut `http://localhost:9200`).

## Endpoints

| Méthode | Chemin | Rôle |
|---|---|---|
| GET | `/health` | Vérification de disponibilité |
| POST | `/predict` | Classification d'une session et explication |

### Entrée de `/predict`

| Champ | Type | Description |
|---|---|---|
| `network_packet_size` | nombre | Taille du paquet en octets |
| `protocol_type` | texte | TCP, UDP ou ICMP |
| `login_attempts` | entier | Nombre de tentatives de connexion |
| `session_duration` | nombre | Durée de la session en secondes |
| `encryption_used` | texte | AES, DES ou None |
| `ip_reputation_score` | nombre | Entre 0 et 1, plus c'est élevé plus l'IP est suspecte |
| `failed_logins` | entier | Nombre d'échecs de connexion |
| `browser_type` | texte | Chrome, Firefox, Edge, Safari ou Unknown |
| `unusual_time_access` | entier | 1 si accès à une heure inhabituelle, sinon 0 |

### Sortie de `/predict`

| Champ | Description |
|---|---|
| `prediction` | 1 si attaque (probabilité >= 0,5), sinon 0 |
| `risk_level` | `critique` (>= 0,8), `eleve` (>= 0,5), `moyen` (>= 0,2), `faible` |
| `probability_attack` | Probabilité d'attaque estimée par le modèle |
| `top_factors` | Les 3 variables les plus déterminantes (nom, impact SHAP, valeur sous forme de texte) |
| `explanation_text` | Phrase en français résumant la décision et ses facteurs |

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

Exemple de réponse (valeurs indicatives) :

```json
{
  "prediction": 1,
  "risk_level": "critique",
  "probability_attack": 0.97,
  "top_factors": [
    {"feature": "failed_logins", "impact": 0.31, "value": "9"},
    {"feature": "ip_reputation_score", "impact": 0.22, "value": "0.82"},
    {"feature": "login_attempts", "impact": 0.14, "value": "12"}
  ],
  "explanation_text": "Session classée comme une activité suspecte avec une confiance de 97 % (risque critique). Facteurs déterminants : le nombre d'échecs de connexion (9) renforce le soupçon, ..."
}
```

## Intégration Elasticsearch

Chaque prédiction est indexée dans l'index `idxia-alerts` avec un champ `@timestamp`, la session d'entrée et le résultat complet. La valeur de chaque facteur est stockée sous forme de texte afin d'éviter les conflits de typage du mapping dynamique d'Elasticsearch (entiers et décimaux mélangés pour un même champ).

## Limites connues

- Aucune authentification sur l'API et CORS ouvert à toutes les origines : acceptable en local, à restreindre avant toute exposition réseau.
- Une valeur catégorielle jamais vue à l'entraînement est remplacée par la première classe connue au lieu de provoquer une erreur.
- Le modèle ne reconnaît que les comportements d'abus d'authentification décrits par les 9 variables ci-dessus.