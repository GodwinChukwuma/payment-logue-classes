from django.urls import path
from wallet.views import (
    FundView,
    TransactionHistoryView,
    TransferView,
    WalletDetailView,
    WithdrawView,
)

ulrpatterns = [
    path("", WalletDetailView.as_view(), name="wallet-detail"),
    path("fund/", FundView.as_view(), name="wallet-fund"),
    path("withdraw/", WithdrawView.as_view(), name="wallet-withdraw"),
    path("transfer/", TransferView.as_view(), name="wallet-transfer"),
    path("history/", TransactionHistoryView.as_view(), name="wallet-transactions"),
]


