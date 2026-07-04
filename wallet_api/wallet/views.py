from __future__ import annotations

import logging
import secrets

from django.db import transaction as db_transaction

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView

from wallet.errors import error_response
from wallet import transaction_log
from wallet.serializers import (
    RegisterSerializer,
    TransactionSerializer,
    WithdrawSerializer,
    TransferSerializer,
    WalletSerializer,
    LoginSerializer,
    FundSerializer,
    AccountLookupSerializer,
    KYCValidateSerializer,
)
from wallet.validators import (
    validate_registration,
    validate_withdrawal,
    validate_transfer,
    validate_amount,
)
from wallet.models import (
    User,
    Wallet,
    Transaction,
    TransactionType,
    TransactionStatus,
)
from wallet.encryption import encrypt_field, decrypt_field, masked_bvn


logger = logging.getLogger("wallet_audit")

class RegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request: Request) -> Response:
        result = validate_registration(request.data)
        if not result.valid:
            return error_response(
                "VALIDATION_ERROR", "Regsitration validation failed.",
                status.HTTP_422_UNPROCESSABLE_ENTITY, details=result.errors
            )
        
        email = request.data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            return error_response(
                "CONFLICT", "An account with this email already exists.",
                status.HTTP_409_CONFLICT
            )
        
        bvn = str(request.data["bvn"]).strip()
        pin = str(request.data["pin"]).strip()

        # encrypt sensitive fields
        bvn_encrypted = encrypt_field(bvn)
        pin_encrypted = encrypt_field(pin)

        with db_transaction.atomic():
            user = User.objects.create_user(
                email=email,
                full_name=request.data["full_name"].strip(),
                password=request.data["password"],
                bvn_encrypted=bvn_encrypted,
                pin_encrypted=pin_encrypted,
                is_kyc_validated=False
            )
            # Auto create wallet for the user kyc is validated
            Wallet.objects.create(user=user)

        logger.info(
            "user.regsistered",
            extra={
                "email": email,
                "account_no": user.account_no,
                "ip": _ip(request)
            },
        )

        return Response(
            {
                "success": True,
                "message": (
                    "Account created successfully. Your wallet is ready."
                    "KYC is pending and will be validated before you can make transactions."
                ),
                "email": email,
                "account_no": user.account_no,
                "kyc_status": "PENDING"
            },
            status=status.HTTP_201_CREATED
        )

        
class LoginView(TokenObtainPairView):
    serializeer_class = LoginSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            response.data["success"] = True
            response.data["message"] = "Loged successfully. Use the access token to authenticate requests."
            
            logger.info(
                "auth.login_success",
                extra={
                    "email": request.data.get("email", ""),
                    "ip": _ip(request)
                },
            )

        return response



class WalletDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WalletSerializer

    def get(self, request: Request) -> Response:
        wallet = request.user.wallet
        return Response({"success": True, "wallet": WalletSerializer(wallet).data})

class FundView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FundSerializer

    def post(self, request: Request) -> Response:
        ok, amount, err = validate_amount(request.data.get("amount"))
        if not ok:
            return error_response("VALIDATION_ERROR", err, status.HTTP_422_UNPROCESSABLE_ENTITY)

        if not request.user.is_kyc_validated:
            return error_response(
                "KYC_REQUIRED",
                "KYC validation is required before funding your wallet.",
                status.HTTP_403_FORBIDDEN
            )
        
        wallet = request.user.wallet
        description = str(request.data.get("description", "Wallet funding")).strip()

        if not wallet.can_credit(amount):
            return error_response(
                "CREDIT_LIMIT_EXCEEDED",
                f"This credit would exceed your your wallet credit limit of {wallet.credit_limit}",
                status.HTTP_400_BAD_REQUEST,
            )
        
        ref = _make_ref("fund")
        with db_transaction.atomic():
            bal_before = wallet.balance
            wallet.balance += amount
            wallet.save()

            Transaction.objects.create(
                wallet = wallet,
                reference = ref,
                type = TransactionType.FUND,
                amount = amount,
                balance_before = bal_before,
                balance_after = wallet.balance,
                description = description,
                status = TransactionStatus.SUCCESS
            )

        logger.info(
            "wallet.funded",
            extra={
                "ref": ref,
                "amount": str(amount),
                "email": request.user.email,
                "ip": _ip(request)
            },
        )
        try:
            transaction_log.record(
                ref=ref,
                txn_type=TransactionType.FUND,
                amount=str(amount),
                email=request.user.email,
                wallet_id=wallet.pk,
                balance_before=str(bal_before),
                balance_after=str(wallet.balance),
                description=description,
                ip=_ip(request),
            )
        except Exception as exc:
            logger.error(
                "txn_log.record_failed",
                extra={
                    "ref": ref,
                    "error": repr(exc),
                },
            )

        return Response({
            "success": True,
            "message": "Wallet funded successfully.",
            "reference": ref,
            "amount": str(amount),
            "new_balance": str(wallet.balance),
        })


class WithdrawView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = WithdrawSerializer

    def post(self, request: Request) -> Response:
        v = validate_withdrawal(request.data)
        if not v.valid:
            return error_response(
                "VALIDATION_ERROR", "Withdrawal validation failed.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                details=v.errors,
            )
        
        user = request.user
        wallet = user.wallet

        if not user.is_kyc_validated:
            return error_response(
                "KYC_REQUIRED",
                "KYC validdation is required before making withrawals.",
                status.HTTP_403_FORBIDDEN,
            )
        
        if not _verify_pin(user, request.data["pin"]):
            logger.warning("auth.pin_failed", extra={"email": user.email, "ip": _ip(request)})
            return error_response(
               "INVALID_PIN", "Incorrect PIN.", status.HTTP_401_UNAUTHORIZED
            )
        
        _, amount, _ = validate_amount(request.data["amount"])
        if not wallet.can_debit(amount):
            return error_response(
                 "INSUFFICIENT_FUNDS",
                f"Insufficient funds. Available: {wallet.balance - wallet.debit_limit}",
                status.HTTP_400_BAD_REQUEST,
            )
        ref = _make_ref("wdr")
        with db_transaction.atomic():
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
                description = request.data.get(
                    f"{request.data.get('description', 'External withdrawal')}",
                    f"{request.data.get('bank_code', '')} / {request.data.get('account_number', '')}",
                ).strip(),
                status = TransactionStatus.SUCCESS
            )

        logger.info(
            "wallet.withdrawal",
            extra={
                "ref": ref,
                "amount": str(amount),
                "bank_code": request.data.get("bank_code"),
                "email": user.email,
                "ip": _ip(request)
            },
        )

        try:
            transaction_log.record(
                ref=ref,
                txn_type=TransactionType.WITHDRAW,
                amount=str(amount),
                email=user.email,
                wallet_id=wallet.pk,
                balance_before=str(bal_before),
                balance_after=str(wallet.balance),
                description=request.data.get("description", "External withdrawal"),
                ip=_ip(request),
            )
        except Exception as exc:
            logger.error(
                "txn_log.record_failed",
                extra={
                    "ref": ref,
                    "error": repr(exc),
                },
            )

        return Response({
            "success": True,
            "message": "Withdrawal successful.",
            "reference": ref,
            "amount": str(amount),
            "new_balance": str(wallet.balance),
        })

class TransferView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransferSerializer

    def post(self, request: Request) -> Response:
        v = validate_transfer(request.data)
        if not v.valid:
            return error_response(
                "VALIDATION_ERROR", "Transfer validation failed.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                details=v.errors,
            )
        
        sender = request.user
        if not sender.is_kyc_validated:
            return error_response(
                "KYC_REQUIRED",
                "KYC validdation is required before making transfers.",
                status.HTTP_403_FORBIDDEN,
            )
        
        if not _verify_pin(sender, request.data["pin"]):
            logger.warning("auth.pin_failed", extra={"email": sender.email, "ip": _ip(request)})
            return error_response(
                "INVALID_PIN", "Incorrect PIN.", status.HTTP_401_UNAUTHORIZED
            )
        
        recipient_account = request.data["recipient_account_no"]
        try:
            recipient = User.objects.select_related("wallet").get(account_no=recipient_account)
        except User.DoesNotExist:
            return error_response(
               "RECIPENT_NOT_FOUND",
               "No wallet found for that account number.",
               status.HTTP_404_NOT_FOUND
            )
        
        if recipient.pk == sender.pk:
            return error_response(
                "SELF_TRANSFER",
                "You cannot transfer to your own account.",
                status.HTTP_400_BAD_REQUEST
            )
        
        _, amount, _ = validate_amount(request.data["amount"])
        sender_wallet = sender.wallet
        recipient_wallet = recipient.wallet

        if not sender_wallet.can_debit(amount):
            return error_response(
                "INSUFFICIENT_FUNDS",
                f"Insufficient funds. Available: {sender_wallet.balance - sender_wallet.debit_limit}",
                status.HTTP_400_BAD_REQUEST,
            )
        
        if not recipient_wallet.can_credit(amount):
            return error_response(
                "RECIPIENT_CREDIT_LIMIT",
                "This transfer would exceed recipient's credit limit.",
                status.HTTP_400_BAD_REQUEST,
            )
        
        desc = str(request.data.get("decription", "Intra-wallet transfer")).strip()
        ref_out = _make_ref("trf")
        ref_in = _make_ref("trf")

        with db_transaction.atomic():
            # debit sender
            s_before = sender_wallet.balance
            sender_wallet.balance -= amount
            sender_wallet.save()

            Transaction.objects.create(
                wallet = sender_wallet,
                reference = ref_out,
                type = TransactionType.TRANSFER_OUT,
                amount = amount,
                balance_before = s_before,
                balance_after = sender_wallet.balance,
                description = f"{desc} -> {recipient.account_no}",
                status = TransactionStatus.SUCCESS,
                counterpart_ref = ref_in
            )

            # Credit recipient
            r_before = recipient_wallet.balance
            recipient_wallet.balance += amount
            recipient_wallet.save()

            Transaction.objects.create(
                wallet = recipient_wallet,
                reference = ref_in,
                type = TransactionType.TRANSFER_IN,
                amount = amount,
                balance_before = r_before,
                balance_after = recipient_wallet.balance,
                description = f"{desc} <- {sender.account_no}",
                status = TransactionStatus.SUCCESS,
                counterpart_ref = ref_out
            )

        logger.info(
            "wallet.transfer",
            extra={
                "ref_out": ref_out,
                "ref_in": ref_in,
                "amount": str(amount),
                "sender": sender.email,
                "recipient": recipient.email,
                "ip": _ip(request)
            }
        )

        try:
            transaction_log.record(
                ref=ref_out,
                txn_type=TransactionType.TRANSFER_OUT,
                amount=str(amount),
                email=sender.email,
                wallet_id=sender_wallet.pk,
                balance_before=str(s_before),
                balance_after=str(sender_wallet.balance),
                description=f"Transfer for {recipient.account_no}",
                ip=_ip(request),
            )

            transaction_log.record(
                ref=ref_in,
                txn_type=TransactionType.TRANSFER_IN,
                amount=str(amount),
                email=recipient.email,
                wallet_id=recipient_wallet.pk,
                balance_before=str(r_before),
                balance_after=str(recipient_wallet.balance),
                description=f"Transfer from {sender.account_no}",
                ip=_ip(request),
            )
        except Exception as exc:
            logger.error(
                "txn_log.record_failed",
                extra={
                    "ref_out": ref_out,
                    "error": repr(exc)
                }
            )

        return Response({
            "success": True,
            "message": "Transfer successful.",
            "reference_out": ref_out,
            "amount": str(amount),
            "recipient_account": recipient_account,
            "new_balance": str(sender_wallet.balance),
        })


class TransactionHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TransactionSerializer

    def get(self, request: Request) -> Response:
        txns = request.user.wallet.transactions.all()[:50]
        return Response({
            "success": True,
            "count": txns.count(),
            "transactions": TransactionSerializer(txns, many=True).data
        })

class KYCValidateView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = KYCValidateSerializer

    def post(self, request: Request) -> Response:
        user = request.user

        if user.is_kyc_validated:
            return error_response(
                "KYC_ALREADY_VALIDATED",
                "KYC has already been validated.",
                status.HTTP_409_CONFLICT,
            )
        
        submitted_bvn = str(request.data.get("bvn", "")).strip()
        if len(submitted_bvn) != 11 or not submitted_bvn.isdigit():
            return error_response(
                "VALIDATION_ERROR",
                "BVN must be 11 digits long.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        try:
            store_bvn = decrypt_field(user.bvn_encrypted)
        except ValueError:
            return error_response(
                "DECRYPTION_ERROR",
                "Could not verify stored BVN.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        if submitted_bvn != store_bvn:
            return error_response(
                "BVN_MISMATCH",
                "The submitted BVN does not match the BVN on file for this account.",
                status.HTTP_400_BAD_REQUEST,
            )
        
        user.is_kyc_validated = True
        user.save()

        logger.info(
            "kyc.validate",
            extra={"email": user.email, "ip": _ip(request)}
        )

        return Response({
            "success": True,
            "message": "KYC validated successfully.",
            "kyc_validated": "VALIDATED",
            "masked_bvn": masked_bvn(store_bvn)
        })

class AccountLookupView(APIView):
    serializer_class = AccountLookupSerializer

    def get(self, request: Request) -> Response:
        ser = AccountLookupSerializer(data=request.data)
        if not ser.is_valid():
            return error_response(
                "VALIDATION_ERROR", "Provide at least email or account_no.",
                status.HTTP_422_UNPROCESSABLE_ENTITY, details=ser.errors
            )
        
        email = ser.validated_data.get("email", "").strip().lower()
        account_no = ser.validated_data.get("account_no", "").strip()

        query = User.objects.all()
        if email:
            query = query.filter(email=email)
        if account_no:
            query = query.filter(account_no=account_no)
            
        user = query.first()
        if not user:
            return error_response(
                "NOT_FOUND",
                "No account found matching the supplied details.",
                status.HTTP_404_NOT_FOUND,
            )
        
        try:
            store_bvn = decrypt_field(user.bvn_encrypted)
            masked = masked_bvn(store_bvn)
        except ValueError:
            masked = "***********"

        logger.info(
            "account.lookup",
            extra={"email": user.email, "ip": _ip(request)}
        )

        return Response({
            "success": True,
            "email": user.email,
            "full_name": user.full_name,
            "account_no": user.account_no,
            "masked_bvn": masked,
            "kyc_status": "VALIDATED" if user.is_kyc_validated else "PENDING",
        })
    
def _ip(request: Request) -> str:
    return (
        request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip()
        or request.META.get("REMOTE_ADDR", "")
    )

def _make_ref(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(12)}"

def _verify_pin(user: User, raw_pin: str) -> bool:
    """Decrypt stored PIN and compare to submitted PIN"""
    try:
        stored = decrypt_field(user.pin_encrypted)
        return stored == str(raw_pin).strip()
    except Exception:
        return False