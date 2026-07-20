from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from payments.views import (
    BankListView,
    FundInitializeView,
    PaymentCallbackView,
    ResolveAccountView,
    WebhookView,
    WithdrawInitializeView,
    FinalizeWithdrawalView,
)

urlpatterns = [
    path("fund/initialize/", FundInitializeView.as_view(), name="fund-initialize"),
    path("callback/", PaymentCallbackView.as_view(), name="payment-callback"),
    path("webhook/", csrf_exempt(WebhookView.as_view()), name="payment-webhook"),
    path("banks/", BankListView.as_view(), name="bank-list"),
    path("withdraw/resolve/", ResolveAccountView.as_view(), name="resolve-account"),
    path("withdraw/initialize/", WithdrawInitializeView.as_view(), name="withdraw-initialize"),
    path("withdraw/finalize/", FinalizeWithdrawalView.as_view(), name="withdraw-finalize"),
]

