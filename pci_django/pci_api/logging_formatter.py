from __future__ import annotations
import logging
import re
import json
from datetime import datetime, timezone
from typing import Any

# Regex catches raw PAN (13-19 consecutively)
_PAN_RE = re.compile(r"\b\d{13, 19}\b")

class PCIJsonFormatter(logging.Formatter):
    """Format log as a single line JSON object"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }

        # Attach any extra field added via logger.info(extra=...)
        for key, value in record.__dict__.items():
            if key in (
                "args", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "message",
                "module", "msecs", "msg", "name", "pathname", "process",
                "processName", "relativeCreated", "stack_info", "thread",
                "threadName",
            ):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        clean = _scrub(payload)
        return json.dumps(clean, default=str)


def _scrub(value: Any) -> Any:
    """Replace any value that look like a raw PAN with [PAN-SCRUBBED]."""
    if isinstance(value, str):
        return _PAN_RE.sub("[PAN-SCRUBBED]", value)
    
    if isinstance(value, dict):
        return {k: _scrub(v) for k, v in value.items()}
    
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value

