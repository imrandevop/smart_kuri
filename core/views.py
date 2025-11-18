from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .models import Chit, Member
from .serializers import ChitSerializer, MemberSerializer, JoinChitSerializer


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
