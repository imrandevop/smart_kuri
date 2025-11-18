from rest_framework import serializers
from django.contrib.auth.hashers import check_password
from .models import Chit, Member
import base64
import re


class ChitSerializer(serializers.ModelSerializer):
    """Serializer for Chit model"""

    class Meta:
        model = Chit
        fields = [
            'chit_id',
            'chit_name',
            'chit_type',
            'chit_amount',
            'total_duration',
            'starting_date',
            'ending_date',
            'password',
            'chit_profile_image',
            'created_at',
        ]
        read_only_fields = ['chit_id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate_chit_type(self, value):
        """Validate that chit_type is one of the allowed choices"""
        allowed_types = ['Daily', 'Weekly', 'Monthly']
        if value not in allowed_types:
            raise serializers.ValidationError(
                f"chit_type must be one of: {', '.join(allowed_types)}"
            )
        return value

    def validate_chit_profile_image(self, value):
        """Validate base64 image if provided"""
        if value:
            try:
                # Try to decode the base64 string to validate it
                base64.b64decode(value)
            except Exception:
                raise serializers.ValidationError(
                    "Invalid base64 encoded image"
                )
        return value

    def validate_total_duration(self, value):
        """Validate that total_duration is positive"""
        if value <= 0:
            raise serializers.ValidationError(
                "total_duration must be greater than 0"
            )
        return value

    def validate(self, data):
        """Validate the entire object"""
        # Ensure starting_date is before ending_date
        if data.get('starting_date') and data.get('ending_date'):
            if data['starting_date'] >= data['ending_date']:
                raise serializers.ValidationError(
                    "starting_date must be before ending_date"
                )
        return data


class MemberSerializer(serializers.ModelSerializer):
    """Serializer for Member model"""

    # Accept chit_id as string instead of object
    chit_id = serializers.CharField(write_only=True)

    class Meta:
        model = Member
        fields = [
            'member_id',
            'name',
            'mobile_number',
            'role',
            'chit_id',
            'password',
            'profile_image',
            'created_at',
        ]
        read_only_fields = ['member_id', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        """Get chit object from chit_id"""
        chit_id = data.get('chit_id')

        # Get chit by ID
        try:
            chit = Chit.objects.get(chit_id=chit_id)
        except Chit.DoesNotExist:
            raise serializers.ValidationError({
                'chit_id': 'Chit with this ID does not exist'
            })

        # Store the chit object for use in create method
        data['chit'] = chit

        return data

    def create(self, validated_data):
        """Create member instance"""
        # Remove chit_id from validated_data (chit object is already there)
        validated_data.pop('chit_id')

        # Create and return the member (password will be hashed in model's save method)
        return Member.objects.create(**validated_data)

    def to_representation(self, instance):
        """Customize output representation"""
        representation = super().to_representation(instance)
        # Add chit_id to the response (from the related chit object)
        representation['chit_id'] = instance.chit.chit_id
        return representation
