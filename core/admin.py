from django.contrib import admin
from .models import Chit, Member


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


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin interface for Member model"""

    list_display = [
        'member_id',
        'name',
        'mobile_number',
        'role',
        'get_chit_name',
        'created_at',
    ]

    list_filter = ['role', 'created_at', 'chit']
    search_fields = ['member_id', 'name', 'mobile_number', 'chit__chit_name']
    readonly_fields = ['member_id', 'created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('member_id', 'name', 'mobile_number', 'role')
        }),
        ('Chit Association', {
            'fields': ('chit',)
        }),
        ('Media', {
            'fields': ('profile_image',)
        }),
        ('Metadata', {
            'fields': ('created_at',)
        }),
    )

    def get_chit_name(self, obj):
        """Display chit name in list view"""
        return obj.chit.chit_name
    get_chit_name.short_description = 'Chit Name'
