"""
main.py

Point d'entree de l'API IDXIA.

Lancement :
    cd backend
    uvicorn app.main:app --reload --port 8000

Documentation interactive generee automatiquement sur :
    http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.predict import predict_session
from app.schemas import PredictionOutput, SessionInput

app = FastAPI(
    title="IDXIA API",
    description="API de detection d'intrusion explicable",
    version="0.1.0",
)

# Autorise le futur dashboard web (autre origine/port) a appeler cette API.
# A restreindre a l'URL exacte du dashboard avant la mise en production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionOutput)
def predict(session: SessionInput):
    return predict_session(session)