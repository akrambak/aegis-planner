# observability/telemetry.py

import time
from typing import Dict, Any
from datetime import datetime

METRICS = []
EVENTS = []


def record_metric(name: str, value: float, tags: Dict[str, Any] = None):
    METRICS.append({
        "ts": datetime.utcnow().isoformat(),
        "name": name,
        "value": value,
        "tags": tags or {}
    })


def record_event(event: str, payload: Dict[str, Any]):
    EVENTS.append({
        "ts": datetime.utcnow().isoformat(),
        "event": event,
        "payload": payload
    })


def flush():
    """
    Phase 14: stdout
    Phase 15+: Prometheus / Loki / DB
    """
    for m in METRICS:
        print("[METRIC]", m)

    for e in EVENTS:
        print("[EVENT]", e)

    METRICS.clear()
    EVENTS.clear()
