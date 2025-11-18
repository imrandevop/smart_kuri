from django.contrib import admin
from .models import Chit


@admin.register(Chit)
class ChitAdmin(admin.ModelAdmin):
    """Admin interface for Chit model"""

    list_display = [
        'chit_id',
        'chit_name',
        'chit_type',
        'chit_amount',
        'total_duration',
        'starting_date',
        'ending_date',
        'created_at',
    ]

    list_filter = ['chit_type', 'created_at']
    search_fields = ['chit_id', 'chit_name']
    readonly_fields = ['chit_id', 'created_at', 'password']

    fieldsets = (
        ('Basic Information', {
            'fields': ('chit_id', 'chit_name', 'chit_type')
        }),
        ('Financial Details', {
            'fields': ('chit_amount', 'total_duration')
        }),
        ('Dates', {
            'fields': ('starting_date', 'ending_date')
        }),
        ('Security', {
            'fields': ('password',)
        }),
        ('Media', {
            'fields': ('chit_profile_image',)
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )
