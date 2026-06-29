from django.urls import path
from loans.views import ApplyView, LoanListView, LoanDetailView, RepayView

urlpatterns = [
    path("apply/", ApplyView.as_view(), name="loan-apply"),
    path("", LoanListView.as_view(), name="loan-list"),
    path("<int:pk>/", LoanDetailView.as_view(), name="loan-detail"),
    path("<int:pk>/repay/", RepayView.as_view(), name="loan-repay"),
]

