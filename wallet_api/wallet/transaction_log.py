
from __future__ import annotations

import json
import logging
import os
from typing import Any
from django.conf import settings
from pathlib import Path

try:
    import fcntl          # POSIX — Linux containers and macOS both have this
    _HAVE_FCNTL = True
except ImportError:       # native Windows without WSL
    _HAVE_FCNTL = False

_live_logger = logging.getLogger("wallet_txn_live")
_archived_logger = logging.getLogger("wallet_txn_archived")


def record(
    *,
    ref: str,
    txn_type: str,
    amount: str,
    email: str,
    wallet_id: int,
    balance_before: str,
    balance_after: str,
    description: str = "",
    status: str = "SUCCESS",
    ip: str = "",
) -> None:
    """
    Append one JSON line to logs/transactions_live.log.

    Call this in ADDITION to the existing wallet_audit logger call in
    views.py — never as a replacement. Wrapped in a try/except at the
    call site so a logging failure never affects the actual transaction.
    """
    _live_logger.info(
        "transaction.recorded",
        extra={
            "ref": ref,
            "type": txn_type,
            "amount": amount,
            "email": email,
            "wallet_id": wallet_id,
            "balance_before": balance_before,
            "balance_after": balance_after,
            "description": description,
            "status": status,
            "ip": ip,
        },
    )


def move_to_archived(ref: str, *, reason: str = "manual") -> bool:
    """
    Move a transaction's log line from transactions_live.log to
    transactions_archived.log.

    Returns True if the line was found and moved, False if it wasn't
    present in the live log (non-fatal — the database operation is
    already committed by the time this is called).

    The live log file is locked with fcntl.flock() during the read-
    rewrite cycle so concurrent requests can't corrupt it with
    interleaved writes.
    """
    live_path = settings.BASE_DIR / settings.TRANSACTION_LIVE_LOG_FILE

    if not live_path.exists():
        return False

    moved_payload: dict[str, Any] | None = None
    lock_fd = _acquire_lock(live_path)

    try:
        with open(live_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        remaining = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if moved_payload is None:
                try:
                    payload = json.loads(stripped)
                except json.JSONDecodeError:
                    remaining.append(line)
                    continue
                if payload.get("ref") == ref:
                    moved_payload = payload
                    continue 
            remaining.append(line)

        if moved_payload is not None:
            with open(live_path, "w", encoding="utf-8") as f:
                f.writelines(remaining)
    finally:
        _release_lock(lock_fd)

    if moved_payload is None:
        return False

    for reserved in ("taskName", "event", "level", "timestamp"):
        moved_payload.pop(reserved, None)

    moved_payload["archive_reason"] = reason
    _archived_logger.info("transaction.archived", extra=moved_payload)
    return True


def _acquire_lock(path: Path) -> int | None:
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