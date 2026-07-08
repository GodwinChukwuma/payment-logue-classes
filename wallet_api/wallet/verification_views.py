from __future__ import annotations

import logging
import random
import secrets

from django.db import transaction as db_transaction

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

from wallet.errors import error_response
from wallet.email_service import send_email_verification, send_phone_verification
from wallet.views import _ip

from wallet.serializers import (
    EmailTokenSerializer,
    PhoneOTPSerializer,
    FaceIDSerializer,
    PhoneSendSerializer,
)

logger = logging.getLogger("wallet_audit")

@extend_schema(
    tags=["Verification"],
    summary="Send email verification token",
    responses={200: OpenApiResponse(description="Token sent")},
)
class SendemailVerificationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user = request.user

        if user.is_email_verified:
            return error_response(
                "ALREADY_VERIFIED",
                "Email already verified",
                status.HTTP_409_CONFLICT
            )
        
        token = f"{secrets.randbelow(900000) + 100000}"
        user.email_verification_token =token
        user.save()

        email_sent = send_email_verification(user.email, user.full_name, token)
        print(f"\n{'='*60}")
        print(f"  EMAIL VERIFICATION TOKEN for {user.email}")
        print(f"  Token: {token}")
        print(f"  POST to /api/wallet/verify/email/confirm/ with {{\"token\": \"{token}\"}}")
        print(f"{'='*60}\n")

        return Response({
            "success": True,
            "message": "Email verification TOKEN sent to your mailtrap sandbox"
                "Token is also printed to console for testing purposes.",
            "dev_token": token,
            "email_sent": email_sent
        })
    
class ConfirmEmailVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = EmailTokenSerializer

    def post(self, request: Request) -> Response:
        user = request.user
        token = request.data.get("token", "").strip()

        if user.is_email_verified:
            return error_response(
                "ALREADY_VERIFIED",
                "Email already verified",
                status.HTTP_409_CONFLICT
            )
        
        if not token:
            return error_response(
                "VALIDATION_ERROR",
                "Token is required",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        
        if not user.email_verification_token or user.email_verification_token != token:
            return error_response(
                "INVALID_TOKEN",
                "Invalid or expired token",
                status.HTTP_400_BAD_REQUEST
            )
        
        with db_transaction.atomic():
            user.is_email_verified = True
            user.email_verification_token = ""
            _upgrade_tier_wallet(user)
            user.save()

        logger.info(
            "kyc.email_verified",
            extra={"email": user.email, "ip": _ip(request)}
        )

        return Response({
            "success": True,
            "message": "Email verified successfully",
            "kyc_tier": user.kyc_tier,
            "tier_label": user.tier_label
        })

@extend_schema(
    tags=["Verification"],
    responses={200: OpenApiResponse(description="OTP sent")},
    examples=[
        OpenApiExample("Request body", value={"phone_number": "+2348012345678"}, request_only=True),
    ],
)  
class SendPhoneVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PhoneSendSerializer

    def post(self, request: Request) -> Response:
        user = request.user
        
        if user.is_phone_verified:
            return error_response(
                "ALREADY_VERIFIED",
                "Phone already verified",
                status.HTTP_409_CONFLICT
            )
        
        phone = request.data.get("phone_number").strip()
        if not phone:
            return error_response(
                "VALIDATION_ERROR",
                "Phone number is required",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        
        code = f"{secrets.randbelow(900000) + 100000}"
        user.phone_number = phone
        user.phone_verification_token = code
        user.save()

        email_sent = send_phone_verification(user.email, user.full_name, code, phone)
        print(f"\n{'='*60}")
        print(f"  PHONE OTP for {user.email} ({phone})")
        print(f"  OTP: {code}")
        print(f"  POST to /api/wallet/verify/phone/confirm/ with {{\"code\": \"{code}\"}}")
        print(f"{'='*60}\n")

        logger.info(
            "kyc.phone_verification_sent",
            extra={"email": user.email, "phone": phone, "ip": _ip(request)}
        )

        return Response({
            "success": True,
            "message": "Email verification token sent to your Mailtrap sandbox."
            "Token is also printed to the console for testing.",
            "dev_otp": code,
            "phone": phone,
            "email_sent": email_sent
        })

@extend_schema(
    tags=["Verification"],
    responses={200: OpenApiResponse(description="Phone verified")},
    examples=[
        OpenApiExample("Confirm", value={"code": "123456"}, request_only=True),
    ],
)
class ConfirmPhoneVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PhoneOTPSerializer

    def post(self, request: Request) -> Response:
        user = request.user
        code = request.data.get("code", "").strip()

        if user.is_phone_verified:
            return error_response(
                "ALREADY_VERIFIED",
                "Phone already verified",
                status.HTTP_409_CONFLICT
            )
        
        if not code:
            return error_response(
                "VALIDATION_ERROR",
                "Code is required",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        
        if not user.phone_verification_token or user.phone_verification_token != code:
            return error_response(
                "INVALID_CODE",
                "Invalid or expired code",
                status.HTTP_400_BAD_REQUEST
            )
        
        with db_transaction.atomic():
            user.is_phone_verified = True
            user.phone_verification_token = ""
            _upgrade_tier_wallet(user)
            user.save()

        logger.info(
            "kyc.phone_verified",
            extra={"email": user.email, "phone": user.phone_number, "ip": _ip(request)}
        )

        return Response({
            "success": True,
            "message": "Phone verified successfully",
            "kyc_tier": user.kyc_tier,
            "tier_label": user.tier_label
        })

@extend_schema(
    tags=["Verification"],
    summary="Verify face ID (simulated)",
    description=(
        "Marks face ID as verified. In production this would receive a result "
        "from a biometric verification SDK (e.g. Smile Identity, Youverify). "
        "Here it is simulated — calling this endpoint with `{\"face_verified\": true}` "
        "sets the flag directly.\n\n"
        "Requires BVN to already be validated (`is_kyc_validated=True`). "
        "Both BVN + face ID are needed to reach Tier 3."
    ),
    request=FaceIDSerializer,
    responses={200: OpenApiResponse(description="Face ID verified")},
    examples=[
        OpenApiExample("Simulate success", value={"face_verified": True}, request_only=True),
    ],
) 
class FaceIDVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FaceIDSerializer

    def post(self, request: Request) -> Response:
        user = request.user
        serializer = FaceIDSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not user.is_kyc_validated:
            return error_response(
                "BVN_REQUIRED",
                "BVN must be validated before Face ID verification",
                status.HTTP_403_FORBIDDEN,
            )
        face_ok = serializer.validated_data["face_verified"]
        # face_ok = request.data.get("face_verified", False)
        if not face_ok:
            return error_response(
                "FACE_VERIFICATION_FAILED",
                "Face ID verification failed",
                status.HTTP_400_BAD_REQUEST
            )
        
        with db_transaction.atomic():
            user.face_id_verified = True
            _upgrade_tier_wallet(user)
            user.save()

        logger.info(
            "kyc.face_id_verified",
            extra={"email": user.email, "ip": _ip(request)}
        )

        return Response({
            "success": True,
            "message": "Face ID verified successfully",
            "kyc_tier": user.kyc_tier,
            "tier_label": user.tier_label,
            "loan_limits": {
                "max_amount": str(user.tier_loan_limits["max"]),
                "max_months": user.tier_loan_limits["max_months"]
            },
        })

@extend_schema(
    tags=["Verification"],
    summary="Get KYC tier and verification status",
    description="Returns the user's current KYC tier, all verification flags, and the loan limits their tier unlocks.",
    responses={200: OpenApiResponse(description="KYC status")},
)
class KYCStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        user = request.user
        limits = user.tier_loan_limits
        return Response({
            "success": True,
            "kyc_tier": user.kyc_tier,
            "tier_label": user.tier_label,
            "verification": {
                "email_verified": user.is_email_verified,
                "phone_verified": user.is_phone_verified,
                "bvn_validated": user.is_kyc_validated,
                "face_id_verified": user.face_id_verified
            },
            "wallet_credit_limit": str(user.wallet.credit_limit),
            "loan_limits": {
                "max_amount": str(limits["max"]),
                "max_months": limits["max_months"]
            },
            "next_tier_requires": _next_tier_hint(user),
        })

def _next_tier_hint(user) -> str:
    tier = user.kyc_tier
    if tier == 1:
        missing = []
        if not user.is_email_verified:
            missing.append("email verification")
        if not user.is_phone_verified:
            missing.append("phone verification")
        return f"Complete {' and' .join(missing)} to reach Tier 2." if missing else "Tier 2 requirement met - recalculate"
    
    if tier == 2:
        missing = []
        if not user.is_kyc_validated:
            missing.append("BVN validation")
        if not user.face_id_verified:
            missing.append("Face ID verification")
        return f"Complete {" and" .join(missing)} to reach Tier 3." if missing else "Tier 3 requirement met"

    return "You are at the highest KYC tier"

def _upgrade_tier_wallet(user) -> None:
    """
    Recalulate tier and update wallet credit limit if tier changed.
    """
    changed = user.recalculate_tier()
    user.save()
    if changed:
        user.wallet.apply_tier_limit()
        logger.info(
            "kyc.tier_upgraded",
            extra={"email": user.email, "tier": user.kyc_tier}
        )
