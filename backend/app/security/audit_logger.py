import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.models.domain import Principal

logger = logging.getLogger(__name__)


class AuditLogger:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or get_settings().audit_log_path)

    async def log(self, event_type: str, principal: Principal | None, payload: dict[str, Any]) -> None:
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "principal": principal.model_dump(mode="json") if principal else None,
            "payload": payload,
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event) + "\n")
        logger.info("audit_event=%s user=%s", event_type, principal.username if principal else "anonymous")

    def read_recent(self, limit: int = 100) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        return [json.loads(line) for line in lines if line.strip()]

