from __future__ import annotations

import logging

from decimal import Decimal
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings as django_settings
from django.db import transaction as db_transaction
from django.utils import timezone

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from loans.serializers import (
    LoanApplicationSerializer,
    LoanDetailSerializer,
    RepaySerializer,
    LoanListSerializer,
)
from loans.models import LoanApplication, LoanStatus, LoanRepayment, RepaymentStatus

from wallet.errors import error_response
from wallet.views import _ip, _make_ref, _verify_pin
from wallet.models import Transaction, TransactionStatus, TransactionType

logger = logging.getLogger("wallet_audit")

class ApplyView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LoanApplicationSerializer

    def post(self, request: Request) -> Response:
        
        user = request.user

        if not user.is_kyc_verified:
            return error_response(
                "KYC_REQUIRED",
                "KYC validation is required before applying for a loan.",
                status.HTTP_403_FORBIDDEN,
            )
        
        if not _verify_pin(user, request.data.get("pin", "")):
            logger.warning("auth.pin_failed", extra={"email": user.email, "ip": _ip(request)})
            return error_response(
                "INVALID_PIN", "Incorrect PIN.", status.HTTP_401_UNAUTHORIZED
            )
        
        # block is active exist
        if LoanApplication.objects.filter(user=user, status=LoanStatus.ACTIVE).exists():
            return error_response(
                "ACTIVE_LOAN_EXISTS",
                "You already have an active loan. Repay it before applying for another.",
                status.HTTP_400_BAD_REQUEST,
            )
        try:
            amount = Decimal(str(request.data.get("amount_requested", "0")))
        except Exception:
            return error_response(
                "VALIDATION_ERROR",
                "Invalid amount requested.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        
        min_loan = Decimal(str(django_settings.MIN_LOAN_AMOUNT))
        max_loan = Decimal(str(django_settings.MAX_LOAN_AMOUNT))

        if not (min_loan <= amount <= max_loan):
            return error_response(
                "AMOUNT_OUT_OF_RANGE",
                f"Loan amount must be between {min_loan} and {max_loan}",
                status.HTTP_400_BAD_REQUEST,
            )
        
        duration = int(request.data.get("duration_months", 0))
        if not (1 <= duration <= 60):
            return error_response(
                "INVALID_DURATION",
                "Loan duration must be between 1 and 60 months.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        
        interest_rate = Decimal(str(django_settings.DEFAULT_INTEREST_RATE))
        ref = _make_ref("loan")
        
        with db_transaction.atomic():
            loan = LoanApplication.objects.create(
                user = user,
                amount_requested = amount,
                amount_approved = amount,
                interest_rate = interest_rate,
                duration_months = duration,
                purpose = str(request.data.get("purpose", "")).strip(),
                status = LoanStatus.ACTIVE,
                disbursed_at = timezone.now(),
                disbursement_ref = ref,
            )

            # disburse into wallet
            wallet = user.wallet
            bal_before = wallet.balance
            wallet.balance += amount
            wallet.save()

            Transaction.objects.create(
                wallet = wallet,
                reference = ref,
                type = TransactionType.LOAN_CREDIT,
                amount = amount,
                balance_before = bal_before,
                balance_after = wallet.balance,
                description = f"Loan disbursement #{loan.pk}",
                status = TransactionStatus.SUCCESS,
            )

            _schedule_repayments(loan)

        logger.info(
            "loan.disbursed",
            extra={
                "loan_id": loan.pk,
                "amount": amount,
                "email": user.email,
                "ref": ref,
                "ip": _ip(request),
            },
        )

        return Response(
            {"success": True, "message": "Loan approvedb and disbursed to your wallet.",
             "loan": LoanApplicationSerializer(loan).data},
            status=status.HTTP_201_CREATED
        )
    
class LoanListView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LoanListSerializer

    def get(self, request: Request) -> Response:
        loans = LoanApplication.objects.filter(user=request.user)
        return Response({
            "success": True,
            "count": loans.count(),
            "result": LoanListSerializer(loans, many=True).data
        })
    
class LoanDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LoanDetailSerializer
    
    def get(self, request: Request, pk: int) -> Response:
        try:
            loan = LoanApplication.objects.prefetch_related("repayments").get(pk=pk, user=request.user)
        except LoanApplication.DoesNotExist:
            return error_response("NOT_FOUND", "Loan not found.", status.HTTP_404_NOT_FOUND)
        
        return Response({"success": True, "loan": LoanDetailSerializer(loan).data})


class RepayView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = RepaySerializer
    
    def post(self, request: Request, pk: int) -> Response:
        user = request.user

        try:
            loan = LoanApplication.objects.prefetch_related("repayments").get(pk=pk, user=user)
        except LoanApplication.DoesNotExist:
            return error_response("NOT_FOUND", "Loan not found.", status.HTTP_404_NOT_FOUND)
        
        if loan.status != LoanStatus.ACTIVE:
            return error_response(
                "LOAN_NOT_ACTIVE",
                f"This loan is {loan.status} and cannot accept repayments.",
                status.HTTP_400_BAD_REQUEST,
            )
        
        if not _verify_pin(user, request.data.get("pin", "")):
            logger.warning("auth.pin_failed", extra={"email": user.email, "ip": _ip(request)})
            return error_response(
                "INVALID_PIN", "Incorrect PIN.", status.HTTP_401_UNAUTHORIZED
            )
        
        # find the next pending instalment
        next_instalment = loan.repayments.filter(
            status=RepaymentStatus.PENDING
        ).order_by("instalment_no").first()

        if not next_instalment:
            return error_response(
                "NO_PENDING_INSTALMENT",
                "No pending instalment found.",
                status.HTTP_400_BAD_REQUEST,
            )
        
        # determin repayment amount
        raw_amount = request.data.get("amount")
        if raw_amount:
            try:
                amount = Decimal(str(raw_amount)).quantize(Decimal("0.01"))
            except Exception:
                return error_response(
                    "VALIDATION_ERROR",
                    "Invalid repayment amount.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        else:
            amount = next_instalment.amount_due

        if amount <= 0:
            return error_response(
                "VALIDATION_ERROR",
                "Repayment amount must be greater than 0.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        
        wallet = user.wallet
        if not wallet.can_debit(amount):
            return error_response(
                "INSUFFICIENT_FUNDS",
                f"Insufficient funds. Available: {wallet.balance - wallet.debit_limit}",
                status.HTTP_400_BAD_REQUEST,
            )
        
        ref = _make_ref("rep")
        
        with db_transaction.atomic():
            bal_before = wallet.balance
            wallet.balance -= amount
            wallet.save()

            Transaction.objects.create(
                wallet = wallet,
                reference = ref,
                type = TransactionType.LOAN_DEBIT,
                amount = amount,
                balance_before = bal_before,
                balance_after = wallet.balance,
                description = f"Loan repayment #{loan.pk} instalment #{next_instalment.instalment_no}",
                status = TransactionStatus.SUCCESS,
            )

            next_instalment.amount_paid = amount
            next_instalment.paid_at = timezone.now()
            next_instalment.status = RepaymentStatus.PAID
            next_instalment.transaction_ref = ref
            next_instalment.save()

            # close the loan if fully repaid
            if loan.outstanding_balance <= 0:
                loan.status = LoanStatus.CLOSED
                loan.save()

        logger.info(
            "loan.repayment",
            extra={
                "loan_id": loan.pk,
                "instalment": next_instalment.instalment_no,
                "amount": str(amount),
                "email": user.email,
                "ref": ref,
                "ip": _ip(request),
            }
        )

        return Response({
            "success": True,
            "message": "Repayment successful.",
            "reference": ref,
            "amount_paid": str(amount),
            "new_balance": str(wallet.balance),
            "loan_status": loan.status,
            "outstanding": str(loan.outstanding_balance)
        })

def _schedule_repayments(loan: LoanApplication):
    """
    Create Loan Repayments rows, one per months, starting next month.
    """
    instalment = loan.monthly_instalment
    for i in range(1, loan.duration_months + 1):
        due = date.today() + relativedelta(months=i)
        LoanRepayment.objects.create(
            loan = loan,
            instalment_no = i,
            amount_due = instalment,
            due_date = due,
        )






