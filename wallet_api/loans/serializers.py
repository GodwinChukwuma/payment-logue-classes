from __future__ import annotations
from rest_framework import serializers
from loans.models import LoanApplication, LoanRepayment

class LoanApplicationSerializer(serializers.Serializer):
    amount_requested = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01)
    duration_months = serializers.IntegerField(min_value=1, max_value=60)
    purpose = serializers.CharField(max_length=255)
    pin = serializers.CharField(write_only=True)

class LoanRepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoanRepayment
        fields = [
            "instalment_no",
            "amount_due",
            "amount_paid",
            "due_date",
            "paid_at",
            "status",
            "transaction_ref",
        ]

class LoanDetailSerializer(serializers.ModelSerializer):
    repayments = LoanRepaymentSerializer(many=True, read_only=True)
    total_repayable = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01, read_only=True)
    monthly_instalment = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01, read_only=True)
    amount_repaid = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01, read_only=True)
    outstanding_balance = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01, read_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "amount_requested",
            "amount_approved",
            "interest_rate",
            "duration_months",
            "purpose",
            "status",
            "total_repayable",
            "monthly_instalment",
            "amount_repaid",
            "outstanding_balance",
            "disbursed_at",
            "disbursement_ref",
            "created_at",
            "last_updated_at",
            "repayments",
        ]

class LoanListSerializer(serializers.ModelSerializer):
    outstanding_balance = serializers.DecimalField(max_digits=15, decimal_places=2,min_value=0.01, read_only=True)

    class Meta:
        model = LoanApplication
        fields = [
            "id",
            "amount_requested",
            "amount_approved",
            "interest_rate",
            "duration_months",
            "purpose",
            "status",
            "outstanding_balance",
            "created_at",
        ]

class RepaySerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=0.01, required=False)
    pin = serializers.CharField(write_only=True)


