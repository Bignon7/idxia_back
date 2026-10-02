"""
history.py

Garde en memoire les N dernieres predictions faites par l'API, pour que
le dashboard puisse afficher un flux "en direct" sans base de donnees
dediee (largement suffisant pour une demo de soutenance).
"""

from collections import deque
from datetime import datetime, timezone

MAX_HISTORY = 200
_history = deque(maxlen=MAX_HISTORY)


def add_entry(session_input: dict, result: dict) -> dict:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": session_input,
        **result,
    }
    _history.appendleft(entry)
    return entry


def get_history(limit: int = 50) -> list:
    return list(_history)[:limit]