from __future__ import annotations

from django.db import models

import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from decimal import Decimal

class UserManager(BaseUserManager):
    def create_user(
        self,
        email: str,
        full_name: str,
        password: str,
        bvn_encrypted: str,
        pin_encrypted: str,
        **extra,
    ) -> "User":
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            full_name=full_name,
            bvn_encrypted=bvn_encrypted,
            pin_encrypted=pin_encrypted,
            **extra,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email: str, password: str, **extra) -> "User":
        
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(
            email=email,
            full_name=extra.pop("full_name", "Admin"),
            password=password,
            bvn_encrypted=extra.pop("bvn_encrypted", ""),
            pin_encrypted=extra.pop("pin_encrypted", ""),
            **extra
        )

class User(AbstractBaseUser, PermissionsMixin):
    """User Model"""
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    bvn_encrypted = models.TextField()
    pin_encrypted = models.TextField()
    account_no = models.CharField(max_length=20, unique=True, blank=True)
    is_kyc_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS =[]

    class Meta:
        db_table = "wallet_users"

    def __str__(self) -> str:
        return self.email
    
    def save(self, *args, **kwargs):
        if not self.account_no:
            self.account_no = self._generate_account_no()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_account_no():
        """Generate a unique account number 10-digits long for each user"""
        return str(uuid.uuid4().int)[0:10]


class Wallet(models.Model):
    """
    One wallet per user, created automatically on registration
    Balanced, DebitLmit, CreditLimit are stored as precise Decimal values.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="wallet")
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    debit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("1000000.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallets"

    def __str__(self) -> str:
        return f"Wallet({self.user.email}, balance={self.balance})"
    
    def can_debit(self, amount: Decimal) -> bool:
        """Return true if this debit wouyld leav balance >= debit_limit"""
        return (self.balance - amount) >= self.debit_limit
    
    def can_credit(self, amount: Decimal) -> bool:
        """Return true if this credit would leave balance <= credit_limit"""
        return (self.balance + amount) <= self.credit_limit

class TransactionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    REVERSED = "REVERSED", "Reversed"

class TransactionType(models.TextChoices):
    FUND = "FUND", "Wallet Funding"
    WITHDRAW = "WITHDRAW", "External Withdrawal"
    TRANSFER_IN = "TRANSFER_IN", "Intra-wallet Transfer (received)"
    TRANSFER_OUT = "TRANSFER_OUT", "Intra-wallet Transfer (sent)"
    LOAN_CREDIT = "LOAN_CREDIT", "Loan Disbursement"
    LOAN_DEBIT = "LOAN_DEBIT", "Loan Repayment"

class Transaction(models.Model):
    """Every wallet movement, one row per event"""
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="transactions")
    reference = models.CharField(max_length=64, unique=True)
    type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=TransactionStatus.choices, default=TransactionStatus.SUCCESS)
    counterpart_ref = models.CharField(max_length=64, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallet_transactions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"({self.type} {self.amount} [{self.reference}])"

