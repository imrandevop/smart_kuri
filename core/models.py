from django.db import models
from django.contrib.auth.hashers import make_password
import uuid
import re


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
            # Generate unique chit_id
            self.chit_id = self._generate_unique_chit_id()

        # Hash password if it's not already hashed
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        super().save(*args, **kwargs)

    def _generate_unique_chit_id(self):
        """Generate unique chit_id with format: chitname + year + type_initial + uuid"""
        # Sanitize chit name (remove special characters, convert to lowercase)
        sanitized_name = re.sub(r'[^a-zA-Z0-9]', '', self.chit_name.lower())

        # Get year from starting_date
        year = self.starting_date.year

        # Get type initial (d/w/m)
        type_initial = self.chit_type[0].lower()

        # Generate short UUID (first 8 characters)
        short_uuid = str(uuid.uuid4())[:8]

        # Combine all parts
        chit_id = f"{sanitized_name}{year}{type_initial}-{short_uuid}"

        # Ensure uniqueness (in case of collision)
        while Chit.objects.filter(chit_id=chit_id).exists():
            short_uuid = str(uuid.uuid4())[:8]
            chit_id = f"{sanitized_name}{year}{type_initial}-{short_uuid}"

        return chit_id

    def __str__(self):
        return f"{self.chit_name} ({self.chit_id})"
