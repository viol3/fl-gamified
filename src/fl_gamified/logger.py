import os
import json
from datetime import datetime
from typing import Optional


class EventLogger:
    """Simple JSONL event logger for simulation replay and Unity ingestion.

    Each event is written as a single JSON object per line with an ISO timestamp
    and an `event_type` field.
    """

    def __init__(self, path: str = "outputs/simulation_events.jsonl", mode: str = "a"):
        self.path = path
        self.mode = mode
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._fh = open(self.path, mode, encoding="utf-8")

    def log_event(self, event_type: str, data: dict) -> None:
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "data": data,
        }
        json.dump(record, self._fh, ensure_ascii=False)
        self._fh.write("\n")
        self._fh.flush()

    def close(self) -> None:
        try:
            self._fh.close()
        except Exception:
            pass
