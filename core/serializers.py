from rest_framework import serializers
from .models import Chit
import base64


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
