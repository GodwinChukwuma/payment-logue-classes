from __future__ import annotations

from rest_framework import serializers
import requests

class FundInitSerializer(serializers.Serializer):
    amount = serializers.DecimalField(min_value=0.01, max_digits=15, decimal_places=2)

class ResolveAccountSerializer(serializers.Serializer):
    bank_code = serializers.CharField()
    account_number = serializers.CharField(max_length=10)

class WithdrawInitSerializer(serializers.Serializer):
    amount = serializers.DecimalField(min_value=100, max_digits=15, decimal_places=2)
    bank_code = serializers.CharField()
    account_number = serializers.CharField(max_length=10)
    account_name = serializers.CharField()
    pin = serializers.CharField(write_only=True)
    description = serializers.CharField(required=False, default="Wallet withdrawal")


class FinalizeWithdrawalSerializer(serializers.Serializer):
    transfer_code = serializers.CharField()
    otp = serializers.CharField(min_length=6, max_length=6)

