from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Chit, Member
from .serializers import ChitSerializer, MemberSerializer


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
