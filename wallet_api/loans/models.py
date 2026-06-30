from __future__ import annotations
from django.db import models
from wallet.models import User
from decimal import Decimal

class LoanStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    ACTIVE = "ACTIVE", "Active (Disbursed)"
    CLOSED = "CLOSED", "Closed (Fully Repaid)"
    DEFAULTED = "DEFAULTED", "Defaulted"

class LoanApplication(models.Model):
    """
    A user's request for a loan.
    Workflow:
      PENDING -> APPROVED -> ACTIVE (on disbursement) -> CLOSED
      PENDING -> REJECTED
      ACTIVE -> DEFAULTED (if overdue repayments accumulate)

    Interest is simple interest:
      total_repayable = amount_requested * (1 + interest_rate/100)
    Split evenly accross duration_months instalments:
    """
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="loans")
    user_loan_number = models.PositiveIntegerField()
    amount_requested = models.DecimalField(max_digits=15, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=15, decimal_places=2)
    duration_months = models.PositiveIntegerField()
    purpose = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=LoanStatus.choices, default=LoanStatus.PENDING)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    disbursement_ref = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "loan_applications"
        ordering = ["-created_at"]
        unique_together = [["user", "user_loan_number"]]

    def __str__(self) -> str:
        return f"Loan#{self.pk} ({self.user.email} {self.amount_requested} [{self.status}])"
    
    @property
    def total_repayable(self) -> Decimal:
        """
        Simple interest rate
        @property is used to calculate total_repayable and not a method
        """
        base = self.amount_approved or self.amount_requested
        return (base * (1 + self.interest_rate / 100)).quantize(Decimal("0.01"))
    
    @property
    def monthly_instalment(self) -> Decimal:
        if not self.duration_months:
            return Decimal("0.00")
        return (self.total_repayable / self.duration_months).quantize(Decimal("0.01"))
    
    @property
    def amount_repaid(self) -> Decimal:
        return self.repayments.filter(
            status=RepaymentStatus.PAID
        ).aggregate(
            total=models.Sum("amount_paid")
        )["total"] or Decimal("0.00")
    
    @property
    def outstanding_balance(self) -> Decimal:
        """Never goes below zero, overpayment is not tracked as negative"""
        raw = self.total_repayable - self.amount_repaid
        return max(raw, Decimal("0.00")).quantize(Decimal("0.01"))


class RepaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PAID = "PAID", "Paid"
    OVERDUE = "OVERDUE", "Overdue"
    WAIVED = "WAIVED", "Waived"

class LoanRepayment(models.Model):
    """
    One instalmemnt row per schedule repayment.
    """
    loan = models.ForeignKey(LoanApplication, on_delete=models.PROTECT, related_name="repayments")
    instalment_no = models.PositiveIntegerField()
    amount_due = models.DecimalField(max_digits=15, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    due_date = models.DateField()
    paid_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=RepaymentStatus.choices, default=RepaymentStatus.PENDING)
    transaction_ref = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "loan_repayments"
        ordering = ["due_date"]
        unique_together = [["loan", "instalment_no"]]

    def __str__(self) -> str:
        return f"Repayment#{self.instalment_no} Loan#{self.loan_id} due={self.due_date}"
 
