from django.urls import path
from wallet.views import (
    FundView,
    TransactionHistoryView,
    TransferView,
    WalletDetailView,
    WithdrawView,
    KYCValidateView,
    AccountLookupView,
)

from wallet.verification_views import (
    ConfirmEmailVerificationView,
    ConfirmPhoneVerificationView,
    FaceIDVerificationView,
    KYCStatusView,
    SendemailVerificationView,
    SendPhoneVerificationView,
)

urlpatterns = [
    path("", WalletDetailView.as_view(), name="wallet-detail"),
    path("fund/", FundView.as_view(), name="wallet-fund"),
    path("withdraw/", WithdrawView.as_view(), name="wallet-withdraw"),
    path("transfer/", TransferView.as_view(), name="wallet-transfer"),
    path("transactions/", TransactionHistoryView.as_view(), name="wallet-transactions"),


     path("kyc/validate/", KYCValidateView.as_view(), name="wallet-kyc-validate"),
     path("kyc/status/", KYCStatusView.as_view(), name="wallet-kyc-status"),

     path("verify/email/send/", SendemailVerificationView.as_view(), name="verify-email-send"),
     path("verify/email/confirm/", ConfirmEmailVerificationView.as_view(), name="verify-email-confirm"),
     path("verify/phone/send/", SendPhoneVerificationView.as_view(), name="verify-phone-send"),
     path("verify/phone/confirm/", ConfirmPhoneVerificationView.as_view(), name="verify-phone-confirm"),
     path("verify/face/", FaceIDVerificationView.as_view(), name="verify-faceid"),

     path("account/lookup/", AccountLookupView.as_view(), name="wallet-account-lookup"),
]


