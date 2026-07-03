from __future__ import annotations
 
import logging
import os
 
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore
 
logger = logging.getLogger("wallet_audit")
 
_scheduler: BackgroundScheduler | None = None
 
 
# def _run_archive() -> None:
#     """
#     Called by APScheduler. Runs the archive logic in-process.
#     Equivalent to: python manage.py archive_transactions
#     """
#     from pci_api.management.commands.archive_transactions import Command
#     logger.info("archive.scheduler_triggered", extra={"source": "apscheduler"})
#     try:
#         cmd = Command()
#         cmd.handle(seconds=None, dry_run=False)
#     except Exception as exc:
#         logger.error("archive.scheduler_error", extra={"error": repr(exc)}, exc_info=exc)
 
 
def start() -> None:
    """Start the background scheduler. Called once from apps.py ready()."""
    global _scheduler
 
    if _scheduler and _scheduler.running:
        return
 
    interval = int(os.environ.get("ARCHIVE_INTERVAL_SECONDS", "30"))
 
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.add_jobstore(DjangoJobStore(), "default")
 
    try:
        _scheduler.remove_job("archive_transactions", jobstore="default")
    except KeyError:
        pass


    _scheduler.add_job(
        trigger=IntervalTrigger(seconds=interval),
        id="archive_transactions",
        name="Archive old transactions",
        jobstore="default",
        replace_existing=True,
        max_instances=1,           # never run two archive jobs concurrently
        misfire_grace_time=10,     # if a tick is missed by <10s, still run it
        coalesce=True,             # if multiple ticks were missed, run once
    )
 
    _scheduler.start()
    logger.info(
        "scheduler.started",
        extra={"job": "archive_transactions", "interval_seconds": interval},
    )
 
 
def stop() -> None:
    """Graceful shutdown — called from apps.py on Django exit signal."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("scheduler.stopped", extra={})

