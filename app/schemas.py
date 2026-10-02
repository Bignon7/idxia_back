"""
schemas.py

Definit la forme des donnees attendues/renvoyees par l'API.
Reprend exactement les colonnes du dataset d'entrainement (hors
session_id et attack_detected, qui n'ont pas de sens en entree).
"""

from pydantic import BaseModel, Field


class SessionInput(BaseModel):
    network_packet_size: float = Field(..., description="Taille du paquet en octets")
    protocol_type: str = Field(..., description="TCP, UDP ou ICMP")
    login_attempts: int
    session_duration: float
    encryption_used: str = Field(..., description="AES, DES ou None")
    ip_reputation_score: float = Field(..., ge=0, le=1)
    failed_logins: int
    browser_type: str
    unusual_time_access: int = Field(..., ge=0, le=1)

    class Config:
        json_schema_extra = {
            "example": {
                "network_packet_size": 599,
                "protocol_type": "TCP",
                "login_attempts": 12,
                "session_duration": 45.2,
                "encryption_used": "None",
                "ip_reputation_score": 0.82,
                "failed_logins": 9,
                "browser_type": "Unknown",
                "unusual_time_access": 1,
            }
        }


class PredictionOutput(BaseModel):
    prediction: int
    risk_level: str
    probability_attack: float
    top_factors: list[dict]
    explanation_text: str