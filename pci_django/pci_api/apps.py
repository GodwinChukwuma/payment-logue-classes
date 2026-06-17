# import os
# from django.apps import AppConfig


# class PciApiConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "pci_api"

#     def ready(self):
#         import sys

#         is_runserver = len(sys.argv) > 1 and sys.argv[1] == "runserver"
#         uses_autoreload = "--noreload" not in sys.argv

#         if is_runserver and uses_autoreload and os.environ.get("RUN_MAIN") != "true":
#             return 
        
#         import threading
#         from pci_api import scheduler
            
#         def _start_after_app_registry_ready():
#             scheduler.start()

#             import atexit
#             atexit.register(scheduler.stop)
        
#         threading.Timer(0, _start_after_app_registry_ready).start()


import os
import sys
from django.apps import AppConfig


class PciApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pci_api"

    def ready(self):
        if sys.argv[1] != "runserver":
            return

        if os.environ.get("RUN_MAIN") != "true":
            return

        from pci_api import scheduler

        scheduler.start()