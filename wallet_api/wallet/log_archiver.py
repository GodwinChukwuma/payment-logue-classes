from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django.conf import settings
from wallet import transaction_log

logger = logging.getLogger("wallet_audit")

_scheduler: BackgroundScheduler | None = None

def _archive_aged_log_lines() -> None:
    """
    Read transaction live log, find lines whose timestamp is older than the configured threshold,
    and move them to the archive log. Using transaction_log.move_to_archive()
    """
    live_path = Path(settings.BASE_DIR) / settings.TRANSACTION_LIVE_LOG_FILE
    if not live_path.exists():
        return
    threshold = int(getattr(settings, "LOG_ARCHIVE_AFTER_SECONDS", 30))
    cutoff = datetime.now(timezone.utc) - timedelta(seconds=threshold)
    try:
        with open(live_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return
    
    aged_refs: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            continue

        ref = payload.get("ref")
        ts = payload.get("timestamp")
        if not ref or not ts:
            continue

        try:
            recorded_at = datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            continue

        if recorded_at < cutoff:
            aged_refs.append(ref)
    
    if not aged_refs:
        return
    
    moved = 0
    for ref in aged_refs:
        try:
            if transaction_log.move_to_archived(ref, reason="age_policy"):
                moved += 1
        except Exception as exc:
            logger.error(
                "log_archiver.move_failed",
                extra={"ref": ref, "error": repr(exc)},
            )

    if moved:
        logger.info(
            "log_archiver.moved",
            extra={"moved": moved, "threshold_seconds": threshold},
        )

def start() -> None:
    """
    Start the log-archiver background scheduler.
    Called from apps.py (runserver) and gurnicorn.conf.py (gunicorn workers).
    """
    global _scheduler

    if _scheduler and _scheduler.running:
        return
    
    interval = int(getattr(settings, "LOG_ARCHIVE_INTERVAL_SECONDS", 30))

    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_job(
        _archive_aged_log_lines,
        trigger=IntervalTrigger(seconds=interval),
        id="archive_transactions_logs",
        name="move aged transaction log lines to archived log",
        replace_existing=True,
        max_instances=1,           # never run two archive jobs concurrently
        misfire_grace_time=10,     # if a tick is missed by <10s, still run it
        coalesce=True,             # if multiple ticks were missed, run once
    )

    _scheduler.start()
    logger.info(
        "log_archiver.started",
        extra={
            "job": "archive_transactions_logs",
            "interval_seconds": interval,
            "threshold_seconds": getattr(settings, "LOG_ARCHIVE_AFTER_SECONDS", 30),
        },
    )


def stop() -> None:
    """Stop the log-archiver background scheduler."""
    global _scheduler

    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        
        logger.info("log_archiver.stopped", extra={})


