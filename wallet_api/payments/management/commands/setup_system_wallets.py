from django.core.management.base import BaseCommand
from payments.models import SystemWallet, SystemWalletType

class Command(BaseCommand):
    help = "Create the RECEIVABLE and PAYABLE internal system wallets"

    def handle(self, *args, **options):
        for wtype, label in SystemWalletType.choices:
            obj, created = SystemWallet.objects.get_or_create(wallet_type=wtype)
            status = "created" if created else "already exists"
            self.stdout.write(self.style.SUCCESS(f" {label}: {status} (balance: {obj.balance})"))

        self.stdout.write(self.style.SUCCESS("System wallets ready"))


