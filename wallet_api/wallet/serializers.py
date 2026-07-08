from __future__ import annotations
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from wallet.models import Transaction, Wallet, User

class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    bvn = serializers.CharField(min_length=11, max_length=11, write_only=True)
    pin = serializers.CharField(min_length=4, max_length=6, write_only=True)

class RegistrationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    email = serializers.EmailField()
    account_no = serializers.CharField()

class LoginSerializer(TokenObtainPairSerializer):
    """"Use email as the username field"""
    username_field = User.USERNAME_FIELD

class LoginResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    access = serializers.CharField()
    refresh = serializers.CharField()


class WalletSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="user.email", read_only=True)
    account_no = serializers.CharField(source="user.account_no", read_only=True)

    class Meta:
        model = Wallet
        fields = [
            "owner_email",
            "account_no",
            "balance",
            "debit_limit",
            "credit_limit",
            "created_at",
            "last_updated_at",
        ]

class FundSerializer(serializers.Serializer):
    amount = serializers.DecimalField(min_value=0.01, max_digits=15, decimal_places=2)
    description = serializers.CharField(max_length=255, required=False, default="wallet funding")

class WithdrawSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)
    bank_code = serializers.CharField(max_length=11)
    account_number = serializers.CharField(max_length=10)
    description = serializers.CharField(max_length=255, required=False, default="External withdrawal")
    pin = serializers.CharField(write_only=True)


class TransferSerializer(serializers.Serializer):
    recipient_account_no = serializers.CharField(max_length=10)
    amount = serializers.DecimalField(min_value=0.01, max_digits=15, decimal_places=2)
    description = serializers.CharField(max_length=255, required=False, default="Intra-wallet transfer")
    pin = serializers.CharField(write_only=True)

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "reference",
            "type",
            "amount",
            "balance_before",
            "balance_after",
            "description",
            "status",
            "counterpart_ref",
            "date",     
        ]

class KYCValidateSerializer(serializers.Serializer):
    bvn = serializers.CharField(max_length=11, min_length=11)

class KYCStatusResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    message = serializers.CharField()
    kyc_status = serializers.CharField()
    masked_bvn = serializers.CharField()

class AccountLookupSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    account_no = serializers.CharField(required=False, max_length=10)
    
    def validate(self, attrs):
        if not attrs.get("email") and not attrs.get("account_no"):
            raise serializers.ValidationError(
                "Provide at least one of the email of account_no"
            )
        return attrs


class AccountLookupResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=True)
    full_name = serializers.CharField()
    email = serializers.EmailField()
    account_no = serializers.CharField()
    masked_bvn = serializers.CharField()
    kyc_status = serializers.CharField()


class EmailTokenSerializer(serializers.Serializer):
    token = serializers.CharField(min_length=6, max_length=6)

class PhoneSendSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

class PhoneOTPSerializer(serializers.Serializer):
    code = serializers.CharField(min_length=6, max_length=6)

class FaceIDSerializer(serializers.Serializer):
    face_verified = serializers.BooleanField()

    


