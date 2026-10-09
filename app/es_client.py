"""
es_client.py

Indexe chaque prediction IDXIA dans Elasticsearch, pour que Kibana
puisse l'afficher a cote des alertes Suricata (meme pipeline de
supervision, deux sources differentes).
"""

import os
from datetime import datetime, timezone

from elasticsearch import Elasticsearch

ES_URL = os.environ.get("ELASTICSEARCH_URL", "http://localhost:9200")
INDEX_NAME = "idxia-alerts"

_client = None


def get_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(ES_URL)
    return _client


def index_alert(raw_session: dict, result: dict) -> None:
    doc = {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "idxia",
        **raw_session,
        **result,
    }
    try:
        get_client().index(index=INDEX_NAME, document=doc)
    except Exception as e:
        # Une panne d'Elasticsearch ne doit jamais faire echouer une
        # prediction : l'API doit continuer a repondre normalement.
        print(f"[es_client] Erreur d'indexation Elasticsearch : {e}")