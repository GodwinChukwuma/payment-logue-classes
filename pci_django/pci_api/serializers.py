from __future__ import annotations
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from pci_api.validators import APPROVED_DOMAINS
from rest_framework.exceptions import ValidationError

class RegisterSerializer(serializers.Serializer):
   email = serializers.EmailField(help_text="Must be gmail, yahoo, outlook.....")
   password = serializers.CharField(min_length=8, write_only=True, style={"input_type": "password"})
   first_name = serializers.CharField(max_length=50)
   last_name = serializers.CharField(max_length=50)

   def validate_email(self, value: str) -> str:
    domain = value.lower().split("@", 1)[1]
    if domain not in APPROVED_DOMAINS:
        raise ValidationError("UNSUPPORTED_DOMAIN")
    return value.lower()

class RegisterResponseSerializer(serializers.Serializer):
   success = serializers.BooleanField(default=True)
   message = serializers.CharField()
   email = serializers.EmailField()

class TokenResponseSerializer(serializers.Serializer):
   access = serializers.CharField(help_text="JWT access token (expires in 60 min)")
   refresh = serializers.CharField(help_text="JWT refresh token (expires in 1 day)")

class PCITokenObtainSerializer(TokenObtainPairSerializer):
   username_field = "email"

   def validate(self, attrs):
      data = super().validate(attrs)
      return data
   
class TransactionRequestSerializer(serializers.Serializer):
   pan = serializers.CharField(
      min_length=13, max_length=19,
      help_text="Card PAN — 13 to 19 digits. Spaces/dashes stripped automatically."
   )
   expiry_date = serializers.CharField(
      help_text="Card expiry date in MM/YY or MM/YYYY format.",
   )
   amount = serializers.DecimalField(
    max_digits=12, decimal_places=2,
        help_text="Transaction amount (max 1,000,000).",
   )
   pin = serializers.CharField(
        min_length=4, max_length=6,
        help_text="Card PIN — 4 to 6 digits. NEVER stored or logged.",
        style={"input_type": "password"},
   )
   email = serializers.EmailField(
        help_text="Cardholder email. Must be from an approved provider.",
   )

class TransactionResponseSerializer(serializers.Serializer):
   success = serializers.BooleanField(default=True)
   saved = serializers.BooleanField(default=True)
   message = serializers.CharField()
   transaction_ref = serializers.CharField()
   pan_masked = serializers.CharField()
   amount = serializers.CharField()
   email = serializers.EmailField()
   status = serializers.CharField()
   timestamp = serializers.DateTimeField()

class TransactionDecryptedSerializer(serializers.Serializer):
   success = serializers.BooleanField(default=True)
   transaction_ref = serializers.CharField()
   pan_masked = serializers.CharField()
   pan_decrypted = serializers.CharField()
   expiry_decrypted = serializers.CharField()
   stored_encrypted = serializers.DictField()
   amount = serializers.CharField()
   email = serializers.EmailField()
   status = serializers.CharField()
   created_at = serializers.DateTimeField()

class ErrorSerializer(serializers.Serializer):
   success = serializers.BooleanField(default=False)
   error = serializers.DictField()


