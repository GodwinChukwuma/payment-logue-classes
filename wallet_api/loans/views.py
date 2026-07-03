from __future__ import annotations

import logging

from decimal import Decimal
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from django.conf import settings as django_settings
from django.db import (
    transaction as db_transaction,
    models as db_models,
)
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

        if not user.is_kyc_validated:
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
            last_num = LoanApplication.objects.filter(
                user=user
            ).aggregate(max_num=db_models.Max("user_loan_number"))["max_num"] or 0
            loan = LoanApplication.objects.create(
                user = user,
                user_loan_number = last_num + 1,
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
        
        outstanding = loan.outstanding_balance
        if outstanding <= 0:
            return error_response(
                "LOAN_FULLY_REPAID",
                "This loan has no outstanding balance.",
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

            if amount <= 0:
                return error_response(
                    "VALIDATION_ERROR",
                    "Repayment amount must be greater than zero.",
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                )
        
        # Defaul: repay next pending instalment exact amount due
        else:
            next_inst = loan.repayments.filter(
                status=RepaymentStatus.PENDING
            ).order_by("instalment_no").first()
            amount = next_inst.amount_due if next_inst else outstanding

        # cap at the actual outstanding balance no overpayment
        # Track whether the user tried to overpay
        overpayment_attempted = amount > outstanding
        if overpayment_attempted:
            amount = outstanding

        # fetch the pending instalment befor processing
        # This prevent money taking but not credited bug. If all instalment are already paid, the loan status will be changed
        # paid but outstanding_balance > 0, allow overpayment to clear the balance
        pending = list(
            loan.repayments.filter(
                status=RepaymentStatus.PENDING
            ).order_by("instalment_no")
        )

        # if not pending instalmemt and amountnis no zero, balance-clearance payment allow it
        # The atomic block will close the loan after the wallet debit
        if amount <= 0:
            return error_response(
                "VALIDATION_ERROR",
                "Computed repayment amount is zero - nothing to pay",
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
        instalments_paid = []
        remaining = amount
        
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
                description = f"Loan repayment (Loan #{loan.user_loan_number})",
                status = TransactionStatus.SUCCESS,
            )

            # Sweep through pending instalments in order, crediting each until the payment is used upt
            # cover partial payments of one instalment, exact payment, or payment that cover several.
            if pending:
                for inst in pending:
                    if remaining <= 0:
                        break
                    pay = min(remaining, inst.amount_due)
                    inst.amount_paid = pay
                    inst.paid_at = timezone.now()
                    inst.status = RepaymentStatus.PAID
                    inst.transaction_ref = ref
                    inst.save()
                    instalments_paid.append(inst.instalment_no)
                    remaining -= pay

                if remaining > 0:
                    # if there is still remaining amount after paying all pending instalments, 
                    # but there is still unused balance, do not discard it, bank it as a catch-up 
                    # to repay the next instalment
                    last_no = loan.repayments.aggregate(
                        max_no=db_models.Max("instalment_no")
                    )["max_no"] or 0
                    catch_up = LoanRepayment.objects.create(
                        loan = loan,
                        instalment_no = last_no + 1,
                        amount_due = remaining,
                        amount_paid = remaining,
                        due_date = timezone.now().date(),
                        paid_at = timezone.now(),
                        status = RepaymentStatus.PAID,
                        transaction_ref = ref,
                    )
                    instalments_paid.append(catch_up.instalment_no)
            else:
                # in the case the payment period closes maybe by underpaying the the agreed amount
                # the catchup here so the amount paid will reflect the actual amount
                last_no =loan.repayments.aggregate(
                    max_no=db_models.Max("instalment_no")
                )["max_no"] or 0
                catch_up = LoanRepayment.objects.create(
                    loan = loan,
                    instalment_no = last_no + 1,
                    amount_due = outstanding,
                    amount_paid = amount,
                    due_date = timezone.now().date(),
                    paid_at = timezone.now(),
                    status = RepaymentStatus.PAID,
                    transaction_ref = ref,
                )
                instalments_paid.append(catch_up.instalment_no)
            
            #Close the loan if fully paid
            loan.refresh_from_db()
            if loan.outstanding_balance <= 0:
                loan.status = LoanStatus.CLOSED
                loan.save()

        logger.info(
            "loan.repayment",
            extra={
                "loan_id": loan.pk,
                "instalments_paid": instalments_paid,
                "amount": str(amount),
                "email": user.email,
                "ref": ref,
                "ip": _ip(request),
            }
        )

        loan.refresh_from_db()
        new_outstanding = loan.outstanding_balance

        # Build a contetxtual message based onwhat actaully happend
        if overpayment_attempted:
            message = (
                f"Your payment was reduced to {amount} (the exact outstanding balance)."
                f"Do not overpay - send the exact outstanding amount next time."
                f"Loan is now {'fully repaid and close' if loan.status == LoanStatus.CLOSED else f'ACTIVE with {new_outstanding} remaining.'}."
            )

        elif loan.status == LoanStatus.CLOSED:
            message = "Loan fully repaid. Your loan is now closed."
        elif not pending:
            message = (
                f"Balance clearance payment of {amount} applied. "
                f"Outstanding balance remianing: {new_outstanding}."
            )
        else:
            paid_count = len(instalments_paid)
            instalments_word = "instalment" if paid_count == 1 else "instalments"
            if new_outstanding > 0:
                message = (
                    f"Payment of {amount} applied to {instalments_word}. "
                    f"{', '.join(str(i) for i in instalments_paid)}."
                    f" Outstanding balance remianing: {new_outstanding}."
                    f"Continue repaying to close the loan."
                )
            else:
                message = (
                    f"Payment of {amount} applied to {instalments_word}. "
                    f"{', '.join(str(i) for i in instalments_paid)}."
                    f"Loan fully repaid. Your loan is now closed."
                )
        return Response({
            "success": True,
            "message": message,
            "reference": ref,
            "amount_paid": str(amount),
            "instalments_paid": instalments_paid,
            "new_balance": str(wallet.balance),
            "loan_status": loan.status,
            "outstanding": str(new_outstanding),
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






