from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.db import models
import uuid
from .models import Chit, Member, Loan, LedgerEntry
from .serializers import (
    ChitSerializer,
    MemberSerializer,
    JoinChitSerializer,
    DashboardSerializer,
    LoanSerializer,
    GetLoansRequestSerializer,
    LoanDetailSerializer,
    GetLedgerEntriesRequestSerializer,
    GetPersonalEntriesRequestSerializer,
    LedgerEntrySerializer
)


class CreateChitAPIView(APIView):
    """API view to create a new chit"""

    def post(self, request):
        """Handle POST request to create a new chit"""
        serializer = ChitSerializer(data=request.data)

        if serializer.is_valid():
            chit = serializer.save()

            # Return the created chit data (password excluded by serializer)
            return Response(
                ChitSerializer(chit).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AddMemberAPIView(APIView):
    """API view to add a member to a chit fund"""

    def post(self, request):
        """Handle POST request to add a new member"""
        serializer = MemberSerializer(data=request.data)

        if serializer.is_valid():
            member = serializer.save()

            # Return the created member data (password excluded by serializer)
            return Response(
                MemberSerializer(member).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class JoinChitAPIView(APIView):
    """API view for joining/logging into a chit fund"""

    def post(self, request):
        """Handle POST request to join a chit"""
        serializer = JoinChitSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        chit_id = serializer.validated_data['chit_id']
        password = serializer.validated_data['password']
        is_admin = serializer.validated_data.get('is_admin', False)

        # Get the chit
        try:
            chit = Chit.objects.get(chit_id=chit_id)
        except Chit.DoesNotExist:
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Admin login - verify against chit password
        if is_admin:
            if check_password(password, chit.password):
                # Return chit details with is_admin flag
                chit_data = ChitSerializer(chit).data
                chit_data['is_admin'] = True
                return Response(chit_data, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED
                )

        # Member login - find member with matching password
        else:
            members = Member.objects.filter(chit=chit)

            for member in members:
                if check_password(password, member.password):
                    # Return member details with is_admin flag
                    member_data = MemberSerializer(member).data
                    member_data['is_admin'] = False
                    return Response(member_data, status=status.HTTP_200_OK)

            # No matching member found
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )


class DashboardAPIView(APIView):
    """API view to get dashboard data for a chit"""

    def post(self, request):
        """Handle POST request to get dashboard data"""
        serializer = DashboardSerializer(data=request.data)

        if not serializer.is_valid():
            # Return error in standard format
            return Response(
                {
                    "status": "error",
                    "code": 400,
                    "message": "Bad request",
                    "data": None,
                    "errors": [
                        {
                            "field": field,
                            "message": error[0] if isinstance(error, list) else str(error)
                        }
                        for field, error in serializer.errors.items()
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        chit_id = serializer.validated_data['chit_id']

        # Get the chit
        try:
            chit = Chit.objects.get(chit_id=chit_id)
        except Chit.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "code": 400,
                    "message": "Bad request",
                    "data": None,
                    "errors": [
                        {
                            "field": "chit_id",
                            "message": "Chit with this ID does not exist"
                        }
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate total members
        total_members = Member.objects.filter(chit=chit).count()

        # Calculate statistics from LedgerEntry model
        ledger_stats = LedgerEntry.objects.filter(chit=chit).aggregate(
            total_amount=Sum('amount'),
            total_fine=Sum('fine'),
            online_cash=Sum('amount', filter=models.Q(payment_method='online')),
            offline_cash=Sum('amount', filter=models.Q(payment_method='offline'))
        )

        # Calculate statistics from Loan model
        loan_stats = Loan.objects.filter(chit=chit).aggregate(
            total_loan_amount=Sum('loan_amount'),
            total_loan_interest=Sum('interest_amount'),
            total_received_amount=Sum('paid_amount')
        )

        # Count active loans
        active_loans = Loan.objects.filter(chit=chit, status='active').count()

        # Extract values and handle None (when no data exists)
        total_amount = float(ledger_stats['total_amount'] or 0)
        total_fine = float(ledger_stats['total_fine'] or 0)
        online_cash = float(ledger_stats['online_cash'] or 0)
        offline_cash = float(ledger_stats['offline_cash'] or 0)

        total_loan_amount = float(loan_stats['total_loan_amount'] or 0)
        total_loan_interest = float(loan_stats['total_loan_interest'] or 0)
        total_received_amount = float(loan_stats['total_received_amount'] or 0)

        # Calculate profit: total contributions - total loans given + loan payments received + fines
        total_profit = total_amount - total_loan_amount + total_received_amount + total_fine

        # Calculate net balance: total contributions - loans outstanding + fines
        # Outstanding loans = total_loan_amount + total_loan_interest - total_received_amount
        outstanding_loans = total_loan_amount + total_loan_interest - total_received_amount
        net_balance = total_amount + total_fine - outstanding_loans

        # Return dashboard data in standard format
        return Response(
            {
                "status": "success",
                "code": 200,
                "message": "Dashboard data retrieved successfully",
                "data": {
                    "total_amount": total_amount,
                    "total_profit": total_profit,
                    "total_members": total_members,
                    "active_loans": active_loans,
                    "total_loan_amount": total_loan_amount,
                    "total_loan_interest": total_loan_interest,
                    "total_fine": total_fine,
                    "online_cash": online_cash,
                    "offline_cash": offline_cash,
                    "net_balance": net_balance
                },
                "meta": {
                    "timestamp": timezone.now().isoformat(),
                    "request_id": str(uuid.uuid4())[:12]
                }
            },
            status=status.HTTP_200_OK
        )


class AddLoanAPIView(APIView):
    """API view to add a new loan (Admin only)"""

    def post(self, request):
        """Handle POST request to add a new loan"""
        serializer = LoanSerializer(data=request.data)

        if serializer.is_valid():
            loan = serializer.save()

            # Return the created loan data
            return Response(
                LoanSerializer(loan).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class GetLoansAPIView(APIView):
    """API view to get active loans for a chit"""

    def post(self, request):
        """Handle POST request to get active loans"""
        # Validate request
        serializer = GetLoansRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "code": 400,
                    "message": "Bad request",
                    "data": None,
                    "errors": [
                        {
                            "field": field,
                            "message": error[0] if isinstance(error, list) else str(error)
                        }
                        for field, error in serializer.errors.items()
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        chit_id = serializer.validated_data['chit_id']

        # Get the chit
        try:
            chit = Chit.objects.get(chit_id=chit_id)
        except Chit.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "code": 400,
                    "message": "Bad request",
                    "data": None,
                    "errors": [
                        {
                            "field": "chit_id",
                            "message": "Chit with this ID does not exist"
                        }
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get active loans for this chit
        active_loans = Loan.objects.filter(chit=chit, status='active')

        # Calculate statistics
        statistics = active_loans.aggregate(
            total_loan_amount=Sum('loan_amount'),
            total_received_amount=Sum('paid_amount'),
            total_interest=Sum('interest_amount')
        )

        # Get count
        active_count = active_loans.count()

        # Handle None values from aggregate (when no loans exist)
        statistics['total_loan_amount'] = float(statistics['total_loan_amount'] or 0)
        statistics['total_received_amount'] = float(statistics['total_received_amount'] or 0)
        statistics['total_interest'] = float(statistics['total_interest'] or 0)

        # Serialize loan data
        loans_data = LoanDetailSerializer(active_loans, many=True).data

        # Build response
        return Response(
            {
                "status": "success",
                "code": 200,
                "message": "Active loans retrieved successfully",
                "data": {
                    "statistics": {
                        "active_count": active_count,
                        "total_loan_amount": statistics['total_loan_amount'],
                        "total_received_amount": statistics['total_received_amount'],
                        "total_interest": statistics['total_interest']
                    },
                    "loans": loans_data
                },
                "meta": {
                    "timestamp": timezone.now().isoformat(),
                    "request_id": str(uuid.uuid4())[:12],
                    "total_count": active_count
                }
            },
            status=status.HTTP_200_OK
        )


class GetAllLedgerEntriesAPIView(APIView):
    """API view to get all ledger entries for a chit (All tab)"""

    def post(self, request):
        """Handle POST request to get all ledger entries"""
        # Validate request
        serializer = GetLedgerEntriesRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "code": 400,
                    "message": "Bad request",
                    "data": None,
                    "errors": [
                        {
                            "field": field,
                            "message": error[0] if isinstance(error, list) else str(error)
                        }
                        for field, error in serializer.errors.items()
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        chit_id = serializer.validated_data['chit_id']

        # Get the chit
        try:
            chit = Chit.objects.get(chit_id=chit_id)
        except Chit.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "code": 400,
                    "message": "Bad request",
                    "data": None,
                    "errors": [
                        {
                            "field": "chit_id",
                            "message": "Chit with this ID does not exist"
                        }
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get all ledger entries for this chit
        entries = LedgerEntry.objects.filter(chit=chit)

        # Serialize entries
        entries_data = LedgerEntrySerializer(entries, many=True).data

        # Get selected date (today's date for meta)
        selected_date = timezone.now().date().isoformat()

        # Build response
        return Response(
            {
                "status": "success",
                "code": 200,
                "message": "Ledger entries retrieved successfully",
                "data": {
                    "entries": entries_data
                },
                "meta": {
                    "timestamp": timezone.now().isoformat(),
                    "request_id": str(uuid.uuid4())[:12],
                    "total_count": entries.count(),
                    "selected_date": selected_date
                }
            },
            status=status.HTTP_200_OK
        )


class GetPersonalLedgerEntriesAPIView(APIView):
    """API view to get personal ledger entries for a member (Personal tab)"""

    def post(self, request):
        """Handle POST request to get personal ledger entries"""
        # Validate request
        serializer = GetPersonalEntriesRequestSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    "status": "error",
                    "code": 400,
                    "message": "Bad request",
                    "data": None,
                    "errors": [
                        {
                            "field": field,
                            "message": error[0] if isinstance(error, list) else str(error)
                        }
                        for field, error in serializer.errors.items()
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        chit_id = serializer.validated_data['chit_id']
        member_id = serializer.validated_data['member_id']

        # Get the member
        try:
            member = Member.objects.get(member_id=member_id, chit__chit_id=chit_id)
        except Member.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "code": 400,
                    "message": "Bad request",
                    "data": None,
                    "errors": [
                        {
                            "field": "member_id",
                            "message": "Member not found or doesn't belong to this chit"
                        }
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get ledger entries for this member
        entries = LedgerEntry.objects.filter(member=member)

        # Serialize entries
        entries_data = LedgerEntrySerializer(entries, many=True).data

        # Build response
        return Response(
            {
                "status": "success",
                "code": 200,
                "message": "Personal entries retrieved successfully",
                "data": {
                    "member_name": member.name,
                    "entries": entries_data
                },
                "meta": {
                    "timestamp": timezone.now().isoformat(),
                    "request_id": str(uuid.uuid4())[:12],
                    "total_count": entries.count()
                }
            },
            status=status.HTTP_200_OK
        )


class AddLedgerEntryAPIView(APIView):
    """API view to add a new ledger entry (Admin only)"""

    def post(self, request):
        """Handle POST request to add a new ledger entry"""
        serializer = LedgerEntrySerializer(data=request.data)

        if serializer.is_valid():
            entry = serializer.save()

            # Return the created entry data
            return Response(
                {
                    "status": "success",
                    "code": 201,
                    "message": "Entry added successfully",
                    "data": LedgerEntrySerializer(entry).data,
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "status": "error",
                "code": 400,
                "message": "Bad request",
                "data": None,
                "errors": [
                    {
                        "field": field,
                        "message": error[0] if isinstance(error, list) else str(error)
                    }
                    for field, error in serializer.errors.items()
                ],
                "meta": {
                    "timestamp": timezone.now().isoformat(),
                    "request_id": str(uuid.uuid4())[:12]
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class UpdateLedgerEntryAPIView(APIView):
    """API view to update an existing ledger entry (Admin only)"""

    def put(self, request, entry_id):
        """Handle PUT request to update a ledger entry"""
        try:
            entry = LedgerEntry.objects.get(id=entry_id)
        except LedgerEntry.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "code": 404,
                    "message": "Entry not found",
                    "data": None,
                    "errors": [
                        {
                            "field": "id",
                            "message": "Ledger entry with this ID does not exist"
                        }
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = LedgerEntrySerializer(entry, data=request.data, partial=True)

        if serializer.is_valid():
            updated_entry = serializer.save()

            return Response(
                {
                    "status": "success",
                    "code": 200,
                    "message": "Entry updated successfully",
                    "data": LedgerEntrySerializer(updated_entry).data,
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "status": "error",
                "code": 400,
                "message": "Bad request",
                "data": None,
                "errors": [
                    {
                        "field": field,
                        "message": error[0] if isinstance(error, list) else str(error)
                    }
                    for field, error in serializer.errors.items()
                ],
                "meta": {
                    "timestamp": timezone.now().isoformat(),
                    "request_id": str(uuid.uuid4())[:12]
                }
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class DeleteLedgerEntryAPIView(APIView):
    """API view to delete a ledger entry (Admin only)"""

    def delete(self, request, entry_id):
        """Handle DELETE request to remove a ledger entry"""
        try:
            entry = LedgerEntry.objects.get(id=entry_id)
        except LedgerEntry.DoesNotExist:
            return Response(
                {
                    "status": "error",
                    "code": 404,
                    "message": "Entry not found",
                    "data": None,
                    "errors": [
                        {
                            "field": "id",
                            "message": "Ledger entry with this ID does not exist"
                        }
                    ],
                    "meta": {
                        "timestamp": timezone.now().isoformat(),
                        "request_id": str(uuid.uuid4())[:12]
                    }
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Delete the entry
        entry.delete()

        return Response(
            {
                "status": "success",
                "code": 200,
                "message": "Entry deleted successfully",
                "data": None,
                "meta": {
                    "timestamp": timezone.now().isoformat(),
                    "request_id": str(uuid.uuid4())[:12]
                }
            },
            status=status.HTTP_200_OK
        )
