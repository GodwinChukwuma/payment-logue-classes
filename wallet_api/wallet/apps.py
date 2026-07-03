from django.apps import AppConfig
import sys
import os
from django.apps import AppConfig

class WalletConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wallet'


    def ready(self):
        if len(sys.argv) < 2 or sys.argv[1] != "runserver":
            return

        if os.environ.get("RUN_MAIN") != "true":
            return

        from wallet import log_archiver

        log_archiver.start()

    