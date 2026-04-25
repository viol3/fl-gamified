from __future__ import annotations

import json
import os
from typing import Any, Dict


class UnityEventPublisher:
    def __init__(self, output_path: str) -> None:
        self.output_path = output_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write("")

    def publish(self, event: Dict[str, Any]) -> None:
        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
