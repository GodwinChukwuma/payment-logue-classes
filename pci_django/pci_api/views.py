from __future__ import annotations
import logging

from django.conf import settings
import secrets
import re
from datetime import datetime, timezone

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.request import Request
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework_simplejwt.views import TokenObtainPairView

from pci_api.encryption import decrypt_field, encrypt_field, mask_pan
from pci_api.models import Transaction, APIUser, TransactionArchive, Status
from pci_api.rate_limiter import is_allowed
from pci_api.validators import validate_transaction

from pci_api.serializers import *

from pci_api.errors import error_response, _flatten_drf_errors
from pci_api.middleware import _get_ip



logger = logging.getLogger("pci_audit")

@extend_schema(
    tags=["Authentication"],
    summary="Register a new user account",
    description=(
        "Create a new API user. The email must come from an approved provider "
        "(Gmail, Yahoo, Outlook, Hotmail, iCloud, ProtonMail, AOL). "
        "After registration, obtain tokens via POST /api/auth/token/."
    ),
    request=RegisterSerializer,
    examples=[
        OpenApiExample(
            "Registration",
            value={
                "first_name": "John",
                "last_name": "Doe",
                "email": "user3@gmail.com",
                "password": "password123",
            }
        )
    ]
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        ser = RegisterSerializer(data=request.data)
        if not ser.is_valid():
            email_errors = ser.errors.get("email", [])
            if any("UNSUPPORTED_DOMAIN" in str(err) for err in email_errors):
                return error_response(
                    "UNSURPORTED_EMAIL_PROVIDER",
                    "Email domain is not allowed",
                    status.HTTP_409_CONFLICT,
                    details=_flatten_drf_errors(ser.errors),
                )
            return error_response(
                "VALIDATION_ERROR", "Registration validation failed.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                details=_flatten_drf_errors(ser.errors),
            )
        email = ser.validated_data["email"]
        if APIUser.objects.filter(email=email).exists():
            return error_response(
                "CONFLICT", "An account with this email already exists.",
                status.HTTP_409_CONFLICT,
            )

        user = APIUser.objects.create_user(
            email=email,
            first_name=ser.validated_data["first_name"],
            last_name=ser.validated_data["last_name"],
            password=ser.validated_data["password"],
            is_verified=True,
        )
        logger.info(
            "user.registered",
            extra={"email": email, "ip": _get_ip(request)},
        )
        return Response(
            {"success": True, "message": "Account created successfully.", "email": email},
            status=status.HTTP_201_CREATED,
        )

@extend_schema(
    request=TokenResponseSerializer,
    examples=[
        OpenApiExample(
            "Registration",
            value={
                "email": "user3@gmail.com",
                "password": "password123",
            }
        )
    ]
)
class TokenObtainView(TokenObtainPairView):
    pass

@extend_schema(
    tags=["Transactions"],
    summary="Submit a card transaction",
    description=(
        "**Requires JWT authentication** (Authorization: Bearer `<access_token>`).\n\n"
        "Accepts cardholder data, validates all fields, encrypts the PAN and expiry "
        "date with AES-256-GCM, and stores the encrypted record in PostgreSQL.\n\n"
        "**What is stored in the database:**\n"
        "- `pan_encrypted` — AES-256-GCM ciphertext of the full PAN\n"
        "- `expiry_encrypted` — AES-256-GCM ciphertext of the expiry date\n"
        "- `pan_masked` — `************1111` (safe for logs and responses)\n\n"
        "**What is NEVER stored:**\n"
        "- Raw PAN\n"
        "- PIN (validated then discarded — PCI-DSS Req 3.2.1)\n"
        "- Expiry date in plaintext\n"
        "- Encryption key\n\n"
        "**Rate limit:** 30 requests per minute per IP."
    ),
    request=TransactionRequestSerializer,
    examples=[
        OpenApiExample(
            "Valid Transaction",
            value={
                "pan": "5555555555554444",
                "expiry_date": "12/30",
                "amount": "99.90",
                "pin": "2020",
                "email": "user3@gmail.com"
            }
        )
    ]
)
class ProcessTransactionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request: Request) -> Response:
        client_ip = _get_ip(request)
        allowed, _ = is_allowed(client_ip)
        if not allowed:
            logger.warning(
                "rate_limit.exceeded",
                extra={"ip": client_ip},
            )
            resp = error_response(
                "RATE_LIMIT_EXCEEDED",
                "Too many requests. Please wait 60 seconds before retrying.",
                status.HTTP_429_TOO_MANY_REQUESTS,
            )
            resp["Retry_after"] = "60"
            return resp
        
        if not request.user.is_verified:
            return error_response(
                "EMAIL_NOT_VERIFIED",
                "Please verify your email first.",
                status.HTTP_403_FORBIDDEN
            )
        
        result = validate_transaction(request.data)
        if not result.valid:
            logger.warning(
                "validation.failed",
                extra={ "ip": client_ip, "errors": result.errors },
            )
            return error_response(
                "VALIDATION_ERROR", "Request validation failed.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                details=result.errors
            )
        
        # extract clean values
        pan = re.sub(r"[\s\-]", "", str(request.data["pan"]))
        expiry = str(request.data["expiry_date"]).strip()
        amount =str(request.data["amount"])
        email = str(request.data["email"]).strip().lower()

        pan_encrypted = encrypt_field(pan)
        expiry_encrypted = encrypt_field(expiry)

        pan_masked_val = mask_pan(pan)

        # Generate unique transaction reference
        tx_ref ="txn_" + secrets.token_hex(12)
        now = datetime.now(timezone.utc)

        existing_pending = Transaction.objects.filter(
            email=request.user.email,
            status=Status.PENDING,
        ).exists()

        if existing_pending:
            return error_response(
                "PENDING_TRANSACTION_EXISTS",
                "You already have a pending transaction.",
                status.HTTP_409_CONFLICT,
            )
        # persist the postgres
        try:
            tx = Transaction.objects.create(
                transaction_ref = tx_ref,
                owner = request.user,
                pan_encrypted = pan_encrypted,
                expiry_encrypted = expiry_encrypted,
                pan_masked = pan_masked_val,
                email = email,
                amount = amount,
                status = Status.PENDING,
                client_ip = client_ip,
            )
        except Exception as exc:
            logger.warning(
                "transaction.db_error",
                extra={"ip": client_ip, "pan_masked": pan_masked_val, "error": type(exc).__name__},
            )
            return error_response(
                "INTERNAL_ERROR", "Failed to store transaction.",
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Log audit
        logger.info(
            "transaction.stored",
            extra={
                "ref": tx_ref,
                "pan_masked": pan_masked_val,
                "amount": amount,
                "email": email,
                "status": "PENDING",
                "ip": client_ip,
                "user": request.user.email,
                "db_id": tx.pk,
            },
        )

        return Response(
            {
                "success": True,
                "saved": True,
                "message": "Transaction stored successfully.",
                "transaction_ref": tx_ref,
                "pan_masked": pan_masked_val,
                "amount": amount,
                "email": email,
                "status": "PENDING",
                "timestamp": now.isoformat(),
            },
            status=status.HTTP_201_CREATED
        )

@extend_schema(
    tags=["Transactions"],
    summary="Retrieve and decrypt a transaction",
    description=(
        "**Requires JWT authentication.**\n\n"
        "Retrieves a stored transaction and demonstrates AES-256-GCM decryption.\n\n"
        "The response shows:\n"
        "- `pan_masked` — what is always safe to display\n"
        "- `pan_decrypted` — the original PAN recovered from encrypted storage\n"
        "- `expiry_decrypted` — the original expiry date recovered\n"
        "- `stored_encrypted` — what actually lives in the PostgreSQL column\n\n"
        "In production this decryption step would only occur inside the "
        "payment processor — decrypted values would never be returned to an API client."
    ),
    responses={
        200: TransactionDecryptedSerializer,
    },
)   
class TransactionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request: Request, ref: str) -> Response:
        try:
            tx = Transaction.objects.get(transaction_ref=ref)
        except Transaction.DoesNotExist:
            return error_response("NOT_FOUND", "Transaction not found.", status.HTTP_404_NOT_FOUND)
        
        if tx.email != request.user.email:
            logger.warning(
                "transaction.unauthorized_access",
                extra={"ref": ref, "ip": _get_ip(request), "user": request.user.email},
            )
            return error_response(
                "PERMISSION_ERROR",
                "You do not have permission to access this transaction.",
                status.HTTP_403_FORBIDDEN,
            )
        # Decrypt
        pan_decrypted = decrypt_field(tx.pan_encrypted)
        expiry_decrypted = decrypt_field(tx.expiry_encrypted)


        logger.info(
            "transaction.decrypted",
            extra={"ref": ref, "ip": _get_ip(request), "pan_masked": tx.pan_masked,"user": request.user.email},
        )

        return Response({
            "success": True,
            "transaction_ref": tx.transaction_ref,
            "pan_masked": tx.pan_masked,
            "stored_encrypted": {
                "pan_encrypted": tx.pan_encrypted[:50] + "...",
                "expiry_encrypted": tx.expiry_encrypted,
            },
            "decrypted": {
                "pan_decrypted": pan_decrypted, 
                "expiry_decrypted": expiry_decrypted,
            },
            "metadata": {
                "amount": str(tx.amount),
                "email": tx.email,
                "status": tx.status,
                "created_at": tx.created_at.isoformat(),
            },
        })

@extend_schema(
    tags=["Archive"],
    summary="List archived transactions for the current user",
    description=(
        "**Requires JWT authentication.**\n\n"
        "Returns all transactions that have been moved to the archive table "
        "(older than `ARCHIVE_AFTER_SECONDS` days, default 30).\n\n"
        "Encrypted fields are not decrypted here — only masked PAN is returned. "
        "the row is still in the live table)."
    ),
)
class ArchiveListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        archives = TransactionArchive.objects.filter(
            owner=request.user,
        ).values(
            "transaction_ref", "pan_masked", "amount", "email",
            "status", "created_at", "archived_at", "archived_reason",
        )
        return Response({"success": True, "count": archives.count(), "result": list(archives)})




