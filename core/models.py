from django.db import models
from django.contrib.auth.hashers import make_password
from django.db import transaction
from datetime import datetime


class Chit(models.Model):
    """Model representing a chit fund"""

    CHIT_TYPE_CHOICES = [
        ('Daily', 'Daily'),
        ('Weekly', 'Weekly'),
        ('Monthly', 'Monthly'),
    ]

    chit_id = models.CharField(max_length=255, primary_key=True, unique=True, editable=False)
    chit_name = models.CharField(max_length=255)
    chit_type = models.CharField(max_length=10, choices=CHIT_TYPE_CHOICES)
    chit_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_duration = models.IntegerField()
    starting_date = models.DateField()
    ending_date = models.DateField()
    password = models.CharField(max_length=255)
    chit_profile_image = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chits'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Override save to auto-generate unique chit_id and hash password"""
        if not self.chit_id:
            # Generate unique chit_id with sequential numbering
            self.chit_id = self._generate_sequential_chit_id()

        # Hash password if it's not already hashed
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def _generate_sequential_chit_id(self):
        """
        Generate sequential chit_id with format: CHT-YYYYMM-NNN
        Example: CHT-202501-001, CHT-202501-002, etc.
        """
        # Get current year and month
        now = datetime.now()
        year_month = now.strftime('%Y%m')  # Format: YYYYMM (e.g., 202501)

        # Prefix for all chits
        prefix = f"CHT-{year_month}-"

        # Use atomic transaction to prevent race conditions
        with transaction.atomic():
            # Find the latest chit ID for this year-month
            latest_chit = Chit.objects.filter(
                chit_id__startswith=prefix
            ).order_by('-chit_id').first()

            if latest_chit:
                # Extract the sequence number from the last chit_id
                last_sequence = int(latest_chit.chit_id.split('-')[-1])
                new_sequence = last_sequence + 1
            else:
                # First chit of this month
                new_sequence = 1

            # Format sequence number with leading zeros (3 digits)
            sequence_str = str(new_sequence).zfill(3)

            # Generate the new chit_id
            chit_id = f"{prefix}{sequence_str}"

            # Double-check uniqueness (should not happen, but safety check)
            while Chit.objects.filter(chit_id=chit_id).exists():
                new_sequence += 1
                sequence_str = str(new_sequence).zfill(3)
                chit_id = f"{prefix}{sequence_str}"

            return chit_id

    def __str__(self):
        return f"{self.chit_name} ({self.chit_id})"


class Member(models.Model):
    """Model representing a member of a chit fund"""

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('organizer', 'Organizer'),
        ('treasurer', 'Treasurer'),
    ]

    member_id = models.CharField(max_length=255, primary_key=True, unique=True, editable=False)
    name = models.CharField(max_length=255)
    mobile_number = models.CharField(max_length=10)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    chit = models.ForeignKey(Chit, on_delete=models.CASCADE, related_name='members')
    password = models.CharField(max_length=255, default='changeme')
    profile_image = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'members'
        ordering = ['-created_at']
        # Ensure unique mobile number per chit
        unique_together = [['chit', 'mobile_number']]

    def save(self, *args, **kwargs):
        """Override save to auto-generate unique member_id and hash password"""
        if not self.member_id:
            # Generate unique member_id with sequential numbering
            self.member_id = self._generate_sequential_member_id()

        # Hash password if it's not already hashed
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def _generate_sequential_member_id(self):
        """
        Generate sequential member_id with format: MEM-YYYYMM-NNN
        Example: MEM-202501-001, MEM-202501-002, etc.
        """
        # Get current year and month
        now = datetime.now()
        year_month = now.strftime('%Y%m')  # Format: YYYYMM (e.g., 202501)

        # Prefix for all members
        prefix = f"MEM-{year_month}-"

        # Use atomic transaction to prevent race conditions
        with transaction.atomic():
            # Find the latest member ID for this year-month
            latest_member = Member.objects.filter(
                member_id__startswith=prefix
            ).order_by('-member_id').first()

            if latest_member:
                # Extract the sequence number from the last member_id
                last_sequence = int(latest_member.member_id.split('-')[-1])
                new_sequence = last_sequence + 1
            else:
                # First member of this month
                new_sequence = 1

            # Format sequence number with leading zeros (3 digits)
            sequence_str = str(new_sequence).zfill(3)

            # Generate the new member_id
            member_id = f"{prefix}{sequence_str}"

            # Double-check uniqueness (should not happen, but safety check)
            while Member.objects.filter(member_id=member_id).exists():
                new_sequence += 1
                sequence_str = str(new_sequence).zfill(3)
                member_id = f"{prefix}{sequence_str}"

            return member_id

    def __str__(self):
        return f"{self.name} - {self.chit.chit_name} ({self.member_id})"


class Loan(models.Model):
    """Model representing a loan given to a member"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('overdue', 'Overdue'),
    ]

    INTEREST_STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    ]

    loan_id = models.CharField(max_length=255, primary_key=True, unique=True, editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='loans')
    chit = models.ForeignKey(Chit, on_delete=models.CASCADE, related_name='loans')
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_amount = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    starting_date = models.DateField()
    ending_date = models.DateField()
    loan_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    interest_status = models.CharField(max_length=10, choices=INTEREST_STATUS_CHOICES, default='unpaid')
    remark = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'loans'
        ordering = ['-created_at']

    @property
    def pending_amount(self):
        """Calculate pending amount: loan_amount + interest_amount - paid_amount"""
        return float(self.loan_amount) + float(self.interest_amount) - float(self.paid_amount)

    def save(self, *args, **kwargs):
        """Override save to auto-generate unique loan_id"""
        if not self.loan_id:
            # Generate unique loan_id with sequential numbering
            self.loan_id = self._generate_sequential_loan_id()

        super().save(*args, **kwargs)

    def _generate_sequential_loan_id(self):
        """
        Generate sequential loan_id with format: LN-YYYYMM-NNN
        Example: LN-202501-001, LN-202501-002, etc.
        """
        # Get current year and month
        now = datetime.now()
        year_month = now.strftime('%Y%m')  # Format: YYYYMM (e.g., 202501)

        # Prefix for all loans
        prefix = f"LN-{year_month}-"

        # Use atomic transaction to prevent race conditions
        with transaction.atomic():
            # Find the latest loan ID for this year-month
            latest_loan = Loan.objects.filter(
                loan_id__startswith=prefix
            ).order_by('-loan_id').first()

            if latest_loan:
                # Extract the sequence number from the last loan_id
                last_sequence = int(latest_loan.loan_id.split('-')[-1])
                new_sequence = last_sequence + 1
            else:
                # First loan of this month
                new_sequence = 1

            # Format sequence number with leading zeros (3 digits)
            sequence_str = str(new_sequence).zfill(3)

            # Generate the new loan_id
            loan_id = f"{prefix}{sequence_str}"

            # Double-check uniqueness (should not happen, but safety check)
            while Loan.objects.filter(loan_id=loan_id).exists():
                new_sequence += 1
                sequence_str = str(new_sequence).zfill(3)
                loan_id = f"{prefix}{sequence_str}"

            return loan_id

    def __str__(self):
        return f"Loan {self.loan_id} - {self.member.name} ({self.loan_amount})"


class LedgerEntry(models.Model):
    """Model representing a ledger entry/payment record in a chit fund"""

    PAYMENT_METHOD_CHOICES = [
        ('online', 'Online'),
        ('offline', 'Offline'),
    ]

    entry_id = models.CharField(max_length=255, unique=True, editable=False)
    serial_no = models.IntegerField(editable=False)
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='ledger_entries')
    chit = models.ForeignKey(Chit, on_delete=models.CASCADE, related_name='ledger_entries')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    loan_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    remark = models.TextField(null=True, blank=True)
    date = models.DateTimeField()
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ledger_entries'
        ordering = ['-date']
        unique_together = [['chit', 'serial_no']]

    def save(self, *args, **kwargs):
        """Override save to auto-generate unique entry_id and serial_no"""
        if not self.entry_id:
            # Generate unique entry_id with sequential numbering
            self.entry_id = self._generate_sequential_entry_id()

        if not self.serial_no:
            # Generate serial_no per chit
            self.serial_no = self._generate_serial_no()

        super().save(*args, **kwargs)

    def _generate_sequential_entry_id(self):
        """
        Generate sequential entry_id with format: LE-YYYYMM-NNN
        Example: LE-202501-001, LE-202501-002, etc.
        """
        # Get current year and month
        now = datetime.now()
        year_month = now.strftime('%Y%m')  # Format: YYYYMM (e.g., 202501)

        # Prefix for all ledger entries
        prefix = f"LE-{year_month}-"

        # Use atomic transaction to prevent race conditions
        with transaction.atomic():
            # Find the latest entry ID for this year-month
            latest_entry = LedgerEntry.objects.filter(
                entry_id__startswith=prefix
            ).order_by('-entry_id').first()

            if latest_entry:
                # Extract the sequence number from the last entry_id
                last_sequence = int(latest_entry.entry_id.split('-')[-1])
                new_sequence = last_sequence + 1
            else:
                # First entry of this month
                new_sequence = 1

            # Format sequence number with leading zeros (3 digits)
            sequence_str = str(new_sequence).zfill(3)

            # Generate the new entry_id
            entry_id = f"{prefix}{sequence_str}"

            # Double-check uniqueness (should not happen, but safety check)
            while LedgerEntry.objects.filter(entry_id=entry_id).exists():
                new_sequence += 1
                sequence_str = str(new_sequence).zfill(3)
                entry_id = f"{prefix}{sequence_str}"

            return entry_id

    def _generate_serial_no(self):
        """
        Generate sequential serial_no per chit
        Serial numbers are 1, 2, 3... within each chit
        """
        with transaction.atomic():
            # Find the latest serial_no for this chit
            latest_entry = LedgerEntry.objects.filter(
                chit=self.chit
            ).order_by('-serial_no').first()

            if latest_entry:
                return latest_entry.serial_no + 1
            else:
                # First entry for this chit
                return 1

    def __str__(self):
        return f"Entry {self.entry_id} - {self.member.name} ({self.amount})"
