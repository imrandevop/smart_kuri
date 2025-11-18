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
