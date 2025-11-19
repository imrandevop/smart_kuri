from rest_framework import serializers
from django.contrib.auth.hashers import check_password
from .models import Chit, Member, Loan, LedgerEntry
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


class JoinChitSerializer(serializers.Serializer):
    """Serializer for Join Chit (Login) functionality"""

    chit_id = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    is_admin = serializers.BooleanField(default=False)

    def validate_chit_id(self, value):
        """Validate that chit exists"""
        try:
            chit = Chit.objects.get(chit_id=value)
        except Chit.DoesNotExist:
            raise serializers.ValidationError("Chit with this ID does not exist")
        return value


class DashboardSerializer(serializers.Serializer):
    """Serializer for Dashboard request"""

    chit_id = serializers.CharField(required=True)

    def validate_chit_id(self, value):
        """Validate that chit exists"""
        try:
            chit = Chit.objects.get(chit_id=value)
        except Chit.DoesNotExist:
            raise serializers.ValidationError("Chit with this ID does not exist")
        return value


class LoanSerializer(serializers.ModelSerializer):
    """Serializer for Loan model"""

    # Accept member_id and chit_id as string inputs instead of objects
    member_id = serializers.CharField(write_only=True)
    chit_id = serializers.CharField(write_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'member_id',
            'chit_id',
            'loan_amount',
            'interest_amount',
            'interest_rate',
            'starting_date',
            'ending_date',
            'loan_date',
            'paid_amount',
            'status',
            'interest_status',
            'remark',
            'created_at',
        ]
        read_only_fields = ['loan_id', 'created_at']
        extra_kwargs = {
            'interest_rate': {'required': False},
            'loan_date': {'required': False},
            'paid_amount': {'required': False},
            'status': {'required': False},
            'interest_status': {'required': False},
            'remark': {'required': False},
        }

    def validate_loan_amount(self, value):
        """Validate that loan_amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("loan_amount must be greater than 0")
        return value

    def validate_interest_amount(self, value):
        """Validate that interest_amount is non-negative"""
        if value < 0:
            raise serializers.ValidationError("interest_amount cannot be negative")
        return value

    def validate(self, data):
        """Validate the entire object and get related objects"""
        member_id = data.get('member_id')
        chit_id = data.get('chit_id')

        # Get member by ID
        try:
            member = Member.objects.get(member_id=member_id)
        except Member.DoesNotExist:
            raise serializers.ValidationError({
                'member_id': 'Member with this ID does not exist'
            })

        # Get chit by ID
        try:
            chit = Chit.objects.get(chit_id=chit_id)
        except Chit.DoesNotExist:
            raise serializers.ValidationError({
                'chit_id': 'Chit with this ID does not exist'
            })

        # Verify that the member belongs to the specified chit
        if member.chit != chit:
            raise serializers.ValidationError({
                'member_id': f'Member {member_id} does not belong to chit {chit_id}'
            })

        # Validate date range
        if data.get('starting_date') and data.get('ending_date'):
            if data['starting_date'] >= data['ending_date']:
                raise serializers.ValidationError({
                    'ending_date': 'ending_date must be after starting_date'
                })

        # Store the objects for use in create method
        data['member'] = member
        data['chit'] = chit

        return data

    def create(self, validated_data):
        """Create loan instance"""
        # Remove string IDs from validated_data (objects are already there)
        validated_data.pop('member_id')
        validated_data.pop('chit_id')

        # Create and return the loan
        return Loan.objects.create(**validated_data)

    def to_representation(self, instance):
        """Customize output representation"""
        representation = super().to_representation(instance)
        # Add member_id and chit_id to the response
        representation['member_id'] = instance.member.member_id
        representation['chit_id'] = instance.chit.chit_id
        return representation


class AddLoanResponseSerializer(serializers.ModelSerializer):
    """Simplified serializer for Add Loan response - only returns request fields + loan_id"""

    member_id = serializers.CharField(source='member.member_id', read_only=True)
    chit_id = serializers.CharField(source='chit.chit_id', read_only=True)

    class Meta:
        model = Loan
        fields = [
            'loan_id',
            'member_id',
            'chit_id',
            'loan_amount',
            'interest_amount',
            'starting_date',
            'ending_date',
        ]
        read_only_fields = ['loan_id']

    def to_representation(self, instance):
        """Customize output to match simple format"""
        representation = super().to_representation(instance)

        # Convert decimal fields to float
        representation['loan_amount'] = float(instance.loan_amount)
        representation['interest_amount'] = float(instance.interest_amount)

        return representation


class GetLoansRequestSerializer(serializers.Serializer):
    """Serializer for Get Loans request"""

    chit_id = serializers.CharField(required=True)

    def validate_chit_id(self, value):
        """Validate that chit exists"""
        try:
            chit = Chit.objects.get(chit_id=value)
        except Chit.DoesNotExist:
            raise serializers.ValidationError("Chit with this ID does not exist")
        return value


class LoanDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed loan information in list view"""

    member_id = serializers.CharField(source='member.member_id', read_only=True)
    member_name = serializers.CharField(source='member.name', read_only=True)
    pending_amount = serializers.SerializerMethodField()
    id = serializers.CharField(source='loan_id', read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id',
            'member_id',
            'member_name',
            'loan_amount',
            'interest_amount',
            'interest_rate',
            'loan_date',
            'ending_date',
            'paid_amount',
            'pending_amount',
            'status',
            'interest_status',
            'remark',
        ]

    def get_pending_amount(self, obj):
        """Calculate pending amount"""
        return obj.pending_amount

    def to_representation(self, instance):
        """Customize output to ensure proper number formatting"""
        representation = super().to_representation(instance)

        # Convert decimal fields to float for proper JSON serialization
        representation['loan_amount'] = float(instance.loan_amount)
        representation['interest_amount'] = float(instance.interest_amount)
        representation['interest_rate'] = float(instance.interest_rate)
        representation['paid_amount'] = float(instance.paid_amount)
        representation['pending_amount'] = instance.pending_amount

        # Format dates in ISO 8601 format
        if instance.loan_date:
            representation['loan_date'] = instance.loan_date.isoformat() + 'T00:00:00Z'
        if instance.ending_date:
            representation['ending_date'] = instance.ending_date.isoformat() + 'T00:00:00Z'

        return representation


class GetLedgerEntriesRequestSerializer(serializers.Serializer):
    """Serializer for Get All Ledger Entries request"""

    chit_id = serializers.CharField(required=True)

    def validate_chit_id(self, value):
        """Validate that chit exists"""
        try:
            chit = Chit.objects.get(chit_id=value)
        except Chit.DoesNotExist:
            raise serializers.ValidationError("Chit with this ID does not exist")
        return value


class GetPersonalEntriesRequestSerializer(serializers.Serializer):
    """Serializer for Get Personal Ledger Entries request"""

    chit_id = serializers.CharField(required=True)
    member_id = serializers.CharField(required=True)

    def validate_chit_id(self, value):
        """Validate that chit exists"""
        try:
            chit = Chit.objects.get(chit_id=value)
        except Chit.DoesNotExist:
            raise serializers.ValidationError("Chit with this ID does not exist")
        return value

    def validate_member_id(self, value):
        """Validate that member exists"""
        try:
            member = Member.objects.get(member_id=value)
        except Member.DoesNotExist:
            raise serializers.ValidationError("Member with this ID does not exist")
        return value

    def validate(self, data):
        """Validate that member belongs to chit"""
        chit_id = data.get('chit_id')
        member_id = data.get('member_id')

        try:
            member = Member.objects.get(member_id=member_id)
            chit = Chit.objects.get(chit_id=chit_id)
        except (Member.DoesNotExist, Chit.DoesNotExist):
            # Already validated in field-level validators
            return data

        if member.chit != chit:
            raise serializers.ValidationError({
                'member_id': f'Member {member_id} does not belong to chit {chit_id}'
            })

        return data


class LedgerEntrySerializer(serializers.ModelSerializer):
    """Serializer for creating/updating Ledger Entry"""

    # Accept member_id and chit_id as string inputs
    member_id = serializers.CharField(write_only=True, required=False)
    chit_id = serializers.CharField(write_only=True, required=False)
    member_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = LedgerEntry
        fields = [
            'id',
            'entry_id',
            'serial_no',
            'member_id',
            'chit_id',
            'member_name',
            'amount',
            'fine',
            'loan_amount',
            'remark',
            'date',
            'payment_method',
            'created_at',
        ]
        read_only_fields = ['id', 'entry_id', 'serial_no', 'created_at']

    def validate_amount(self, value):
        """Validate that amount is non-negative"""
        if value < 0:
            raise serializers.ValidationError("amount cannot be negative")
        return value

    def validate_fine(self, value):
        """Validate that fine is non-negative"""
        if value < 0:
            raise serializers.ValidationError("fine cannot be negative")
        return value

    def validate_loan_amount(self, value):
        """Validate that loan_amount is non-negative"""
        if value < 0:
            raise serializers.ValidationError("loan_amount cannot be negative")
        return value

    def validate(self, data):
        """Validate the entire object and get related objects"""
        # For create operations, we need member_id and chit_id
        if not self.instance:  # Creating new entry
            member_id = data.get('member_id')
            chit_id = data.get('chit_id')

            if not member_id:
                raise serializers.ValidationError({
                    'member_id': 'This field is required for new entries'
                })
            if not chit_id:
                raise serializers.ValidationError({
                    'chit_id': 'This field is required for new entries'
                })

            # Get member by ID
            try:
                member = Member.objects.get(member_id=member_id)
            except Member.DoesNotExist:
                raise serializers.ValidationError({
                    'member_id': 'Member with this ID does not exist'
                })

            # Get chit by ID
            try:
                chit = Chit.objects.get(chit_id=chit_id)
            except Chit.DoesNotExist:
                raise serializers.ValidationError({
                    'chit_id': 'Chit with this ID does not exist'
                })

            # Verify that the member belongs to the specified chit
            if member.chit != chit:
                raise serializers.ValidationError({
                    'member_id': f'Member {member_id} does not belong to chit {chit_id}'
                })

            # Store the objects for use in create method
            data['member'] = member
            data['chit'] = chit

        return data

    def create(self, validated_data):
        """Create ledger entry instance"""
        # Remove string IDs and member_name from validated_data (objects are already there)
        validated_data.pop('member_id', None)
        validated_data.pop('chit_id', None)
        validated_data.pop('member_name', None)

        # Create and return the entry
        return LedgerEntry.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """Update ledger entry instance"""
        # Remove IDs from update (can't change member/chit)
        validated_data.pop('member_id', None)
        validated_data.pop('chit_id', None)
        validated_data.pop('member_name', None)

        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        """Customize output representation"""
        representation = super().to_representation(instance)

        # Add member_name from related member
        representation['member_name'] = instance.member.name

        # Convert decimal fields to float
        representation['amount'] = float(instance.amount)
        representation['fine'] = float(instance.fine)
        representation['loan_amount'] = float(instance.loan_amount)

        # Format date in ISO 8601 format with timezone
        if instance.date:
            representation['date'] = instance.date.isoformat()
            if not representation['date'].endswith('Z'):
                representation['date'] += 'Z'

        return representation
