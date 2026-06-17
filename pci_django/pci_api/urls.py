from django.urls import path
from pci_api.views import (
    ArchiveListView,
    ProcessTransactionView,
    RegisterView,
    SignInView,
    TransactionDetailView,
)

urlpatterns = [
    path("auth/register/", RegisterView.as_view()),
    path("auth/signin/", SignInView.as_view()),
    path("processTransaction", ProcessTransactionView.as_view()),
    path("transaction/<str:ref>/", TransactionDetailView.as_view()),
    path("archive/", ArchiveListView.as_view()),
]

