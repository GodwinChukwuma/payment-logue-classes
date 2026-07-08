from __future__ import annotations

from django.db import models

import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)

from decimal import Decimal

class KYCTier(models.IntegerChoices):
    TIER_1 = 1, "Tier 1 - Registered"
    TIER_2 = 2, "Tier 2 - Email and phone verified"
    TIER_3 = 3, "Tier 3 - BVN and faceId verified"

TIER_LOANLIMITS = {
    KYCTier.TIER_1: {"max": Decimal("2000.00"), "max_months": 1},
    KYCTier.TIER_2: {"max": Decimal("10000.00"), "max_months": 3},
    KYCTier.TIER_3: {"max":Decimal("1000000.00"), "max_months": 60},
}

TIER_CREDIT_LIMITS = {
    KYCTier.TIER_1: Decimal("5000.00"),
    KYCTier.TIER_2: Decimal("500000.00"),
    KYCTier.TIER_3: Decimal("10000000.00"),
}

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
    phone_number = models.CharField(max_length=20, blank=True)
    kyc_tier = models.IntegerField(choices=KYCTier.choices, default=KYCTier.TIER_1)
    is_kyc_validated = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    face_id_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=64, blank=True)
    phone_verification_token = models.CharField(max_length=6, blank=True)
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

    def recalculate_tier(self) -> bool:
        """
        Recalculate the user's KYC tier based on the verification flags
        Return True if tier change
        """
        if self.is_kyc_validated and self.face_id_verified:
            new_tier = KYCTier.TIER_3
        elif self.is_email_verified and self.is_phone_verified:
            new_tier = KYCTier.TIER_2
        else:
            new_tier = KYCTier.TIER_1

        if new_tier != self.kyc_tier:
            self.kyc_tier = new_tier
            return True
        return False
    
    @property
    def tier_loan_limits(self) -> dict:
        """Return the loan limits for the user's KYC tier"""
        return TIER_LOANLIMITS[self.kyc_tier]
    
    @property
    def tier_label(self) -> str:
        """Return the label for the user's KYC tier"""
        return KYCTier(self.kyc_tier).label

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
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("500000.00"))
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
    
    def apply_tier_limit(self) -> None:
        """
        Set credit limit to match the user current KYC tier.
        """
        new_limit = TIER_CREDIT_LIMITS[self.user.kyc_tier]
        if self.credit_limit != new_limit:
            self.credit_limit = new_limit
            self.save()

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

