from django.urls import path
from .views import (
    CreateChitAPIView,
    AddMemberAPIView,
    JoinChitAPIView,
    DashboardAPIView,
    AddLoanAPIView,
    GetLoansAPIView,
    GetAllLedgerEntriesAPIView,
    GetPersonalLedgerEntriesAPIView,
    AddLedgerEntryAPIView,
    UpdateLedgerEntryAPIView,
    DeleteLedgerEntryAPIView
)

urlpatterns = [
    path('api/chits/', CreateChitAPIView.as_view(), name='create-chit'),
    path('api/members/', AddMemberAPIView.as_view(), name='add-member'),
    path('api/chit/join/', JoinChitAPIView.as_view(), name='join-chit'),
    path('api/dashboard/', DashboardAPIView.as_view(), name='dashboard'),
    path('api/loans/', AddLoanAPIView.as_view(), name='add-loan'),
    path('api/loans/list/', GetLoansAPIView.as_view(), name='get-loans'),
    path('api/ledger/entries/all/', GetAllLedgerEntriesAPIView.as_view(), name='get-all-ledger-entries'),
    path('api/ledger/entries/personal/', GetPersonalLedgerEntriesAPIView.as_view(), name='get-personal-ledger-entries'),
    path('api/ledger/entries/', AddLedgerEntryAPIView.as_view(), name='add-ledger-entry'),
    path('api/ledger/entries/<int:entry_id>/', UpdateLedgerEntryAPIView.as_view(), name='update-ledger-entry'),
    path('api/ledger/entries/<int:entry_id>/', DeleteLedgerEntryAPIView.as_view(), name='delete-ledger-entry'),
]
