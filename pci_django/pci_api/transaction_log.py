from __future__ import annotations

import logging
import json
import os
from typing import Any

try:
   import fcntl # POSIX only (docker, linux container, macOS) deployment

   _HAVE_FCNTL = True
except ImportError:
   _HAVE_FCNTL = False

from django.conf import settings

_live_logger = logging.getLogger("pci_transaction_live")
_archived_logger = logging.getLogger("pci_transaction_archived")

def record_live(*, ref: str, pan_masked: str, amount: str, email: str, status: str, _get_ip: str, user: str, db_id: int) -> None:
   """Append one JSON to transaction live log a newly stored transaction"""
   _live_logger.info(
      "tansaction.live",
      extra={
         "ref": ref,
         "pan_masked": pan_masked,
         "amount": amount,
         "email": email,
         "status": status,
         "ip": _get_ip,
         "user": user,
         "db_id": db_id,
      },
   )


def move_to_archived(ref: str, *, archived_reason: str = "age_policy") -> bool:
    """Move ref's line from transaction live log to archived log"""
    live_path = settings.BASE_DIR / settings.TRANSACTION_LIVE_LOG_FILE
 
    if not live_path.exists():
        return False
 
    moved_payload: dict[str, Any] | None = None
 
    lock_fd = _acquire_lock(live_path)
    try:
        with open(live_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
 
        remaining_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if moved_payload is None:
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError:
                    remaining_lines.append(line)
                    continue
                if payload.get("ref") == ref:
                    moved_payload = payload
                    continue
            remaining_lines.append(line)
 
        if moved_payload is not None:
            with open(live_path, "w", encoding="utf-8") as f:
                f.writelines(remaining_lines)
    finally:
        _release_lock(lock_fd)
 
    if moved_payload is None:
        return False

    for reserved_key in ("taskName", "event", "level", "timestamp"):
        moved_payload.pop(reserved_key, None)
    
    _archived_logger.info("transaction.archived", extra=moved_payload)
    return True

def _acquire_lock(path) -> int | None:
    """Best effort exclusive lock on the live log file during move"""
    if not _HAVE_FCNTL:
        return None
    fd = os.open(str(path), os.O_RDWR | os.O_CREAT)
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd

def _release_lock(fd: int | None) -> None:
    if fd is None:
        return
    try:
        fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)

