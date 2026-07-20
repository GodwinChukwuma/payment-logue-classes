from __future__ import annotations

from django.db import models
from decimal import Decimal
from wallet.models import User, Wallet

class SystemWalletType(models.TextChoices):
    RECEIVABLE = "RECEIVABLE", "Receivable (collect incoming Paystack payments)"
    PAYABLE = "PAYABLE", "Payable (hold funds earmarked for outgoing Paystack payments)"

class SystemWallet(models.Model):
    """The money is through float account not directly betweeen paystack and customer"""
    wallet_type = models.CharField(max_length=15, choices=SystemWalletType.choices, unique=True)
    balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "system_wallets"
    
    def __str__(self):
        return f"SystemWallet({self.wallet_type}, balance={self.balance})"

class ProviderDirection(models.TextChoices):
    FUNDING = "FUNDING", "Funding (customer -> receivable -> customer wallet)"
    WITHDRAWAL = "WITHDRAWAL", "Withdrawal (customer wallet -> payable -> customer bank)"

class ProviderStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    REVERSED = "REVERSED", "Reversed"

class ProviderTransaction(models.Model):
    """Track every paystack transction and interact"""
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="provider_transactions")
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="provider_transactions")
    reference = models.CharField(max_length=64, unique=True)
    provider_ref = models.CharField(max_length=128, blank=True)
    direction = models.CharField(max_length=15, choices=ProviderDirection.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=10, choices=ProviderStatus.choices, default=ProviderStatus.PENDING)
    recipient_code = models.CharField(max_length=64, blank=True)
    bank_code = models.CharField(max_length=11, blank=True)
    account_no = models.CharField(max_length=10, blank=True)
    account_name = models.CharField(max_length=255, blank=True)
    paystack_data = models.JSONField(default=dict, blank=True)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "provider_transactions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"ProviderTxn({self.direction} {self.amount} [{self.status} {self.reference}])"



