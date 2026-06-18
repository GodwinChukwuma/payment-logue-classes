from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from pci_api import transaction_log
from pci_api.models import Transaction, TransactionArchive

logger = logging.getLogger("pci_audit")

BATCH_SIZE = 500

class Command(BaseCommand):
    """Archive transactions older than ARCHIVE_AFTER_SECONDS seconds."""
    help = "Archive transactions older than ARCHIVE_AFTER_SECONDS seconds."

    def add_arguments(self, parser):
        parser.add_argument(
            "--seconds",
            type=int,
            default=None,
            help="Override ARCHIVE_AFTER_SECONDS from environment Default: 30",
        )
        parser.add_argument(
            "--dry_run",
            action="store_true",
            help="Print how many rows would be archived without moving them.",
        )

    def handle(self, *args, **options):
        seconds = options.get("seconds") or int(os.environ.get("ARCHIVE_AFTER_SECONDS", 30))
        dry_run = options.get("dry_run", False)
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=seconds)

        candidate_qs = Transaction.objects.filter(created_at__lt=cutoff)
        total = candidate_qs.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"[DRY RUN] {total} transaction(s) older than {seconds}s"
                    f"(before {cutoff.isoformat()}) would be archived."
                )
            )
            return
        if total == 0:
            self.stdout.write("No transactions qualify for archiving.")
            logger.info(
                "archive.skipped",
                extra={"reason": "no_candidates", "cutoff_seconds": seconds, "cutoff_time": cutoff.isoformat()},
            )
            return
        
        archived_total = 0
        errors = 0
        batch_num = 0

        while True:
            batch = list(
                candidate_qs.select_related("owner").order_by("id")[:BATCH_SIZE]
            )
            if not batch:
                break
            
            batch_num += 1
            try:
                archived_total += _archive_batch(batch)
            except Exception as exc:
                errors += 1
                logger.error(
                    "archive.batch_failed",
                    extra={"batch": batch_num, "error": repr(exc)},
                )
                break # Do not abort batches for one failure

            #candidate_qs = candidate_qs.exclude(pk__in=[t.pk for t in batch])

        outcome = "archive.completed" if errors == 0 else "archive.completed_with_errors"
        logger.info(
            outcome,
            extra={
                "archved": archived_total,
                "errors": errors,
                "cutoff_seconds": seconds,
                "cutoff_date": cutoff.isoformat(),
                "batches": batch_num,
            },
        )

        msg = (
            f"Arhived {archived_total} of {total} transaction(s)"
            f"(cutoff: {seconds} / {cutoff.isoformat()})"
        )
        if errors:
            self.stdout.write(self.style.ERROR(msg + f"Erros: {errors} batch(es) failed."))
        else:
            self.stdout.write(self.style.SUCCESS(msg))


def _archive_batch(batch: list[Transaction]) -> int:
    """
    Move one batch of Transaction rows to TransactiobnArchive atomically.
    Uses select_for_update() conceptually - the batch was alreadey fetched.

    Return the number of rows  successfully archived
    """
    archive_row = [
        TransactionArchive(
            original_id=tx.pk,
            transaction_ref=tx.transaction_ref,
            owner_id=tx.owner_id,
            pan_encrypted=tx.pan_encrypted,
            expiry_encrypted=tx.expiry_encrypted,
            pan_masked=tx.pan_masked,
            amount=tx.amount,
            email=tx.email,
            status=tx.status,
            client_ip=tx.client_ip,
            created_at=tx.created_at,
            archived_reason="age_policy",
        )
        for tx in batch
    ]
    with transaction.atomic():
        TransactionArchive.objects.bulk_create(archive_row, ignore_conflicts=False)
        ids = [tx.pk for tx in batch]
        Transaction.objects.filter(pk__in=ids).delete()
    for tx in batch:
        try:
            transaction_log.move_to_archived(tx.transaction_ref, archived_reason="age_policy")
        except Exception as exc:
            logger.error(
                "transaction_log.move_to_archived_failed",
                extra={"ref": tx.transaction_ref, "error": repr(exc)},
            )

    return len(batch)


