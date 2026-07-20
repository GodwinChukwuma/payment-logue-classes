from __future__ import annotations

import logging

import hashlib
import hmac
import json
from decimal import Decimal
from django.http import HttpResponse

from django.conf import settings

from django.db import transaction as db_transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.request import Request
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema

from payments import paystack
from payments.serializers import (
    FundInitSerializer,
    ResolveAccountSerializer,
    WithdrawInitSerializer,
    FinalizeWithdrawalSerializer,
)
from wallet.errors import error_response

from wallet.views import _ip, _make_ref
from wallet.models import Transaction, TransactionStatus, TransactionType

from payments.models import (
    ProviderTransaction,
    SystemWallet,
    SystemWalletType,
    ProviderDirection,
    ProviderStatus
)


logger = logging.getLogger("wallet_audit")

class FundInitializeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FundInitSerializer

    def post(self, request: Request) -> Response:
        user = request.user
        wallet = user.wallet

        if not user.is_kyc_validated and not user.is_email_verified:
            return error_response(
                "KYC_REQUIRED",
                "Complete all the KYC requirements first",
                status.HTTP_403_FORBIDDEN,
            )
        try:
            amount = Decimal(str(request.data.get("amount", "0")))
        except Exception:
            return error_response("VALIDATION_ERROR", "invalid amount", status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        if amount < 100:
            return error_response("VALIDATION_ERROR", "minimum amount is 100", status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        if not wallet.can_credit(amount):
            return error_response(
                "CREDIT_LIMIT_EXCEEDED",
                f"This credit would exceed your your wallet credit limit of #{wallet.credit_limit}",
                status.HTTP_400_BAD_REQUEST,
            )
        ref = _make_ref("pay")

        provider_txn = ProviderTransaction.objects.create(
            user = user,
            wallet = wallet,
            reference = ref,
            direction = ProviderDirection.FUNDING,
            amount = amount,
            status = ProviderStatus.PENDING,
        )

        ok, data = paystack.initialize_payment(user.email, float(amount), ref)
        if not ok:
            provider_txn.status = ProviderStatus.FAILED
            provider_txn.failure_reason = data.get("error", "Paystack error")
            provider_txn.save()
            return error_response("PAYSTACK_ERROR", data.get("error", "Paystack error"), status.HTTP_502_BAD_GATEWAY)
        logger.info("payments.funding_initialized", extra={
            "ref": ref, "amount": str(amount), "email": user.email, "ip": _ip(request)
        })

        return Response({
            "success": True,
            "message": "Payment initialized. Redirect the user to the checkout URL",
            "reference": ref,
            "amount": str(amount),
            "checkout_url": data.get("authorization_url"),
            "access_code": data.get("access_code")
        })

@extend_schema(
    tags=["Payments — Funding"],
    summary="Payment callback (Paystack redirect after checkout)",
    description=(
        "Paystack redirects the customer's browser here after they complete "
        "payment on the checkout page. Pass the `reference` query parameter "
        "to verify the payment and credit the wallet.\n\n"
        "You can also call this manually in Swagger after completing a test payment "
        "to trigger the credit without waiting for Paystack's redirect."
    ),
    parameters=[
        OpenApiParameter(
            name="reference",
            type=str,
            location=OpenApiParameter.QUERY,
            required=True,
            description="The payment reference returned by /api/payments/fund/initialize/. Example: pay_8cb9a7e7013a19a796200d30",
        ),
    ],
    responses={
        200: OpenApiResponse(description="Payment verified and wallet credited"),
        400: OpenApiResponse(description="Payment failed or reference missing"),
        404: OpenApiResponse(description="Transaction not found"),
    },
)
class PaymentCallbackView(APIView):
    """Paystack redirect the customer's browser hereafter payment"""
    permission_classes = [AllowAny]

    def get(self, request: Request) -> Response:

        ref = request.query_params.get("reference", "").strip()
        if not ref:
            return error_response("MISSING_REFERENCE", "reference is required", status.HTTP_400_BAD_REQUEST)
        try:
            provider_txn = ProviderTransaction.objects.select_related("user", "wallet").get(
                reference=ref,
                direction=ProviderDirection.FUNDING,
            )
        except ProviderTransaction.DoesNotExist:
            return error_response("NOT_FUND", "Transaction not found", status.HTTP_404_NOT_FOUND)
        if provider_txn.status == ProviderStatus.SUCCESS:
            provider_txn.wallet.refresh_from_db()
            return Response({
                "success": True,
                "message": f"Transaction already completed. Current balance: ₦{provider_txn.wallet.balance}",
                "reference": ref,
                "new_balance": str(provider_txn.wallet.balance)
            })
        if provider_txn.status == ProviderStatus.FAILED:
            provider_txn.status = ProviderStatus.PENDING
            provider_txn.failure_reason = ""
            provider_txn.save()

        ok, data = paystack.verify_payment(ref)
        if not ok or data.get("status") != "success":
            provider_txn.status = ProviderStatus.FAILED
            provider_txn.failure_reason = data.get("error") or data.get("message", "Payment not successful")
            provider_txn.paystack_data = data
            provider_txn.save()
            return error_response(
                "PAYMENT_FAILED",
                "Payment was not successful",
                status.HTTP_400_BAD_REQUEST,
            )
        
        _credit_customer_from_receivable(provider_txn, data)
        provider_txn.wallet.refresh_from_db()

        return Response({
            "success": True,
            "message": f"#{provider_txn.amount} successfully added to your wallet",
            "reference": ref,
            "new_balance": str(provider_txn.wallet.balance)
        })

class WebhookView(APIView):
    def post(self, request, *args, **kwargs):
        if not _verify_webhook_signature(request):
            logger.warning("webhook.invalid_signature", extra={"ip": request.META.get("REMOTE_ADDR")})
            return HttpResponse(status=401)
        
        try:
            event = json.loads(request.body)
        except json.JSONDecodeError:
            return HttpResponse(status=400)
        
        event_type = event.get("event", "")
        data = event.get("data", {})

        logger.info("Webhook.received", extra={"event": event_type})

        if event_type == "charge.success":
            self._handle_charge_success(data)
        elif event_type == "transfer.success":
            self._handle_transfer_success(data)
        elif event_type in ("charge.failed", "transfer.failed"):
            self._handle_transfer_failed(data)

        return HttpResponse(status=200)
    
    def _handle_charge_success(self, data: dict) -> None:
        ref = data.get("reference", "")
        try:
            provider_txn = ProviderTransaction.objects.select_related("user", "wallet").get(
                reference=ref,
                direction=ProviderDirection.FUNDING,
            )
        except ProviderTransaction.DoesNotExist:
            logger.warning("Webhook.transaction_not_found", extra={"ref": ref})
            return
        
        if provider_txn.status != ProviderStatus.PENDING:
            return # skip already processed callbacks - idompetent
        
        _credit_customer_from_receivable(provider_txn, data)

    def _handle_transfer_success(self, data: dict) -> None:
        ref = data.get("reference", "")
        try:
            provider_txn = ProviderTransaction.objects.get(
                reference=ref,
                direction=ProviderDirection.WITHDRAWAL,
            )
        except ProviderTransaction.DoesNotExist:
            return
        
        if provider_txn.status != ProviderStatus.PENDING:
            return
        
        with db_transaction.atomic():
            provider_txn.status = ProviderStatus.SUCCESS
            provider_txn.reference = data.get("reference", "")
            provider_txn.paystack_data = data
            provider_txn.save()

        logger.info("payment.withdrawal_success", extra={
            "ref": ref, "amount": str(provider_txn.amount), "email": provider_txn.user.email
        })

    def _handle_transfer_failed(self, data: dict) -> None:
        """Reverse the withrawal, refund customer, debit payable wallet"""
        ref = data.get("reference", "")
        try:
            provider_txn = ProviderTransaction.objects.select_related("user", "wallet").get(
                reference=ref,
                direction=ProviderDirection.WITHDRAWAL,
            )
        except ProviderTransaction.DeosNotExist:
            return
        
        if provider_txn.status != ProviderStatus.PENDING:
            return
        
        reveral_ref = _make_ref("rev")
        with db_transaction.atomic():
            provider_txn.status = ProviderStatus.REVERSED
            provider_txn.failure_reason = data.get("reason", "Transfer failed")
            provider_txn.paystack_data = data
            provider_txn.save()

            # 1. Debit payable wallet
            payable = _get_system_wallet(SystemWalletType.PAYABLE)
            payable.balance -= provider_txn.amount
            payable.save()

            # 2. Credit customer wallet back
            wallet = provider_txn.wallet
            bal_before = wallet.balance
            wallet.balance += provider_txn.amount
            wallet.save()

            # Create txn reversal
            Transaction.objects.create(
                wallet = wallet,
                reference = reveral_ref,
                type = TransactionType.FUND,
                amount = provider_txn.amount,
                balance_before = bal_before,
                balance_after = wallet.balance,
                description = f"Reversal: withdrawal failed ({ref})",
                status = TransactionStatus.REVERSED
            )

        logger.info("payment.withdrawal_reversed", extra={
            "ref": ref, "reversal_ref": reveral_ref, "amount": str(provider_txn.amount), "email": provider_txn.user.email
        })
        
class BankListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request: Request) -> Response:
        ok, data = paystack.get_banks()

        if not ok:
            return error_response("PAYSTACK_ERROR", data.get("error", "paystack error"), status.HTTP_502_BAD_GATEWAY)
        return Response({"success": True, "count": len(data), "banks": data})
    
class ResolveAccountView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ResolveAccountSerializer

    def post(self, request: Request) -> Response:
        bank_code = request.data.get("bank_code", "").strip()
        account_number = request.data.get("account_number", "").strip()

        if not bank_code or not account_number:
            return error_response("VALIDATION_ERROR", "bank code and account number are required", status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        ok, data = paystack.resolve_account(account_number, bank_code)
        if not ok:
            return error_response("RESOLVE_FIALED", data.get("error", "could not verify the account"), status.HTTP_400_BAD_REQUEST)
        
        return Response({
            "success": True,
            "account_name": data.get("account_name"),
            "account_number": data.get("account_number"),
        })

class WithdrawInitializeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawInitSerializer

    def post(self, request: Request) -> Response:
        from wallet.views import _verify_pin
        user = request.user
        wallet = user.wallet

        if not user.is_kyc_validated:
            return error_response(
                "KYC_REQUIRED",
                "Complete all the KYC requirements first",
                status.HTTP_403_FORBIDDEN,
            )
        
        if not _verify_pin(user, request.data.get("pin", "")):
            logger.warning("auth.pin_failed", extra={"email": user.email, "ip": _ip(request)})
            return error_response("INVALID_PIN", "Incorrect PIN", status.HTTP_403_FORBIDDEN)
        
        try:
            amount = Decimal(str(request.data.get("amount", "0")))
        except Exception:
            return error_response("VALIDATION_ERROR", "invalid amount", status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        if amount < 100:
            return error_response("VALIDATION_ERROR", "minimum amount is 100", status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        if not wallet.can_debit(amount):
            return error_response(
                "INSUFFICIENT_FUNDS",
                f"Insufficient funds. Balance: #{wallet.balance - wallet.debit_limit}",
                status.HTTP_400_BAD_REQUEST,
            )

        bank_code = request.data.get("bank_code", "").strip()
        account_number = request.data.get("account_number", "").strip()
        account_name = request.data.get("account_name", "").strip()

        if not all([bank_code, account_number, account_name]):
            return error_response("VALIDATION_ERROR", "bank code, account number and account name are required", status.HTTP_422_UNPROCESSABLE_ENTITY)

        # 1. Create paystack transfer recipient
        ok, recipient_data = paystack.create_transfer_recipient(account_number=account_number, account_name=account_name, bank_code=bank_code)
        if not ok:
            return error_response("PAYSTACK_ERROR", recipient_data.get("error", "paystack error"), status.HTTP_502_BAD_GATEWAY)

        recipient_code = recipient_data.get("recipient_code", "")
        ref = _make_ref("wdr")

        #  2. Insert Provider transaction record
        with db_transaction.atomic():
            provider_txn = ProviderTransaction.objects.create(
                user = user,
                wallet = wallet,
                reference = ref,
                direction = ProviderDirection.WITHDRAWAL,
                amount = amount,
                status = ProviderStatus.PENDING,
                recipient_code = recipient_code,
                bank_code = bank_code,
                account_no = account_number,
                account_name = account_name,
                paystack_data = recipient_data,
            )
        
            # 3. Debit customer wallet
            bal_before = wallet.balance
            wallet.balance -= amount
            wallet.save()

            Transaction.objects.create(
                wallet = wallet,
                reference = ref,
                type = TransactionType.WITHDRAW,
                amount = amount,
                balance_before = bal_before,
                balance_after = wallet.balance,
                description = f"Withdrawal to {bank_code}/{account_number} ({account_name})",
                status = TransactionStatus.PENDING,
            )

            # 4. Credit payable system wallet
            payable = _get_system_wallet(SystemWalletType.PAYABLE)
            payable.balance += amount
            payable.save()
        
        # 5. iniitiate paystack traansfer
        ok, transfer_data = paystack.initiate_transfer(
            float(amount),
            recipient_code,
            ref,
            reason=request.data.get("Description", "Wallet withdrawal"),
        )
        if not ok: # Transfer failed, reverse immediately
            with db_transaction.atomic():
                wallet.balance += amount
                wallet.save()
                payable.balance -= amount
                payable.save()
                provider_txn.status = ProviderStatus.FAILED
                provider_txn.failure_reason = transfer_data.get("error", "Transfer initiation failed")
                provider_txn.save()

            return error_response("PAYSTACK_ERROR", transfer_data.get("error", "paystack error"), status.HTTP_502_BAD_GATEWAY)
        
        provider_txn.provider_ref = transfer_data.get("transfer_code", "")
        provider_txn.paystack_data = transfer_data
        provider_txn.save()

        logger.info("payment.withdrawal_initiated", extra={
            "ref": ref, "amount": str(amount), "email": user.email,
            "bank": bank_code, "account": account_number, "ip": _ip(request),
        })

        return Response({
            "success": True,
            "message": "Withdrawal initiated successfully",
            "reference":     ref,
            "amount":        str(amount),
            "recipient":     account_name,
            "transfer_code": provider_txn.provider_ref,
            "new_balance":   str(wallet.balance),
        })

class FinalizeWithdrawalView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FinalizeWithdrawalSerializer

    def post(self, request: Request) -> Response:
        transfer_code = request.data.get("transfer_code", "").strip()
        otp = request.data.get("otp", "").strip()

        if not transfer_code or not otp:
            return error_response(
                "VALIDATION_ERROR",
                "transfer code and otp are required",
                status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        if len(otp) != 6 or not otp.isdigit():
            return error_response(
                "VALIDATION_ERROR",
                "otp must be a 6 digit number",
                status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        try:
            provider_txn = ProviderTransaction.objects.select_related("user", "wallet").get(
                provider_ref=transfer_code,
                direction=ProviderDirection.WITHDRAWAL,
            )
        except ProviderTransaction.DoesNotExist:
            return error_response("NOT_FOUND", "Transaction not found", status.HTTP_404_NOT_FOUND)
        
        if provider_txn.status != ProviderStatus.PENDING:
            return error_response(
                "ALREADY_PROCESSED",
                f"This transfer has already been {provider_txn.status}",
                status.HTTP_400_BAD_REQUEST
            )
        wallet = provider_txn.wallet
        payable = _get_system_wallet(SystemWalletType.PAYABLE)

        ok, data = paystack.finalize_transfer(transfer_code=transfer_code, otp=otp)
        if not ok:
            error = data.get("error", "Unable to finalize transfer").lower()
            otp_error = (
                "opt",
                "invalid otp",
                "expired otp",
                "transfer require otp",
            )

            if any(msg in error for msg in otp_error):
                provider_txn.paystack_data = data
                provider_txn.failure_reason = error
                provider_txn.save(
                    update_fields=[
                        "paystack_data",
                        "failure_reason",
                        "last_updated_at",
                    ]
                )

                return error_response(
                    "INVALID_OTP",
                    data.get("error", "Unable to finalize transfer"),
                    status.HTTP_400_BAD_REQUEST
                )
            # OTP wrong or paystack rejected - reverse the debit
            with db_transaction.atomic():
                wallet.balance += provider_txn.amount
                wallet.save(update_fields=["balance"])
                
                payable.balance -= provider_txn.amount
                payable.save(update_fields=["balance"])
                
                provider_txn.status = ProviderStatus.FAILED
                provider_txn.failure_reason = data.get("error", "Transfer failed")
                provider_txn.paystack_data = data
                provider_txn.save(
                    update_fields=[
                        "status",
                        "failure_reason",
                        "paystack_data",
                        "last_updated_at",
                    ]
                )

                Transaction.objects.filter(
                    reference = provider_txn.reference,
                    wallet = wallet,
                ).update(
                    status = TransactionStatus.FAILED
                )

            return error_response(
                "PAYSTACK_ERROR",
                data.get("error", "Unable to finalize transfer"),
                status.HTTP_502_BAD_GATEWAY,
            )
        
        # OTP accepted - mark complete, debit payable
        with db_transaction.atomic():
            provider_txn.status = ProviderStatus.SUCCESS
            provider_txn.paystack_data = data
            provider_txn.failure_reason = ""
            provider_txn.save()
            
            payable.balance -= provider_txn.amount
            payable.save(update_fields=["balance"])
            
            Transaction.objects.filter(
                reference = provider_txn.reference,
                wallet = wallet,
            ).update(
                status = TransactionStatus.SUCCESS
            )

        logger.info(
            "payment.withdrawal_completed",
            extra={
                "reference": provider_txn.reference,
                "transfer_code": transfer_code,
                "amount": str(provider_txn.amount),
                "email": provider_txn.user.email,
                "ip": _ip(request),
            },
        )

        return Response(
            {
                "success": True,
                "message": "Withdrawal completed successfully",
                "reference": provider_txn.reference,
                "transfer_code": transfer_code,
                "amount": str(provider_txn.amount),
                "status": provider_txn.status,
            },
            status=status.HTTP_200_OK
        )

def _verify_webhook_signature(request) -> bool:
    sigs = request.headers.get("x-paystack-signature", "")
    expected = hmac.new(
        settings.PAYSTACK_SECRET_KEY.encode(),
        request.body,
        hashlib.sha512
    ).hexdigest()

    return hmac.compare_digest(sigs, expected)
    
def _credit_customer_from_receivable(provider_txn: ProviderTransaction, provider_data: dict) -> None:
    """
    Money flow on successful funding
        1. Credit the RECEIVABLE wallet (money arrived from paystack)
        2. Credit the CUSTOMER wallet (money moved from receivable to customer wallet)
    Both happen atomically
    """
    with db_transaction.atomic():
        # Mark the transaction complete
        provider_txn.status = ProviderStatus.SUCCESS
        provider_txn.reference = provider_data.get("reference", "")
        provider_txn.paystack_data = provider_data
        provider_txn.save()

        # 1. Credit the receivable system wallet
        receivable = _get_system_wallet(SystemWalletType.RECEIVABLE)
        receivable.balance += provider_txn.amount
        receivable.save()

        # 2. credit customer wallet
        wallet = provider_txn.wallet
        bal_before = wallet.balance
        wallet.balance += provider_txn.amount
        wallet.save()

        Transaction.objects.create(
            wallet = wallet,
            reference = provider_txn.reference,
            amount = provider_txn.amount,
            balance_before = bal_before,
            balance_after = wallet.balance,
            description = f"Paystack funding #{provider_txn.reference}",
            status = TransactionStatus.SUCCESS
        )

    logger.info("payment.funding_credited", extra={
        "ref": provider_txn.reference,
        "amount": str(provider_txn.amount),
        "email": provider_txn.user.email,
    })

def _get_system_wallet(wtype: str) -> SystemWallet:
    return SystemWallet.objects.get(wallet_type=wtype)


