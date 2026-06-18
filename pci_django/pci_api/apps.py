import os
import sys
from django.apps import AppConfig


class PciApiConfig(AppConfig):
    """Satrt the APScheduler background thread when the app is loaded"""
    default_auto_field = "django.db.models.BigAutoField"
    name = "pci_api"

    def ready(self):
        if len(sys.argv) < 2 or sys.argv[1] != "runserver":
            return

        if os.environ.get("RUN_MAIN") != "true":
            return

        from pci_api import scheduler

        scheduler.start()