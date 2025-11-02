from django.contrib import admin
from .models import PatientRecord


@admin.register(PatientRecord)
class PatientRecordAdmin(admin.ModelAdmin):
    """Admin interface for Patient Records"""
    list_display = ['booking_id', 'name', 'phone_number', 'doctor_name', 'department', 'appointment_date', 'created_at']
    list_filter = ['department', 'appointment_date', 'created_at']
    search_fields = ['booking_id', 'name', 'phone_number', 'mail_id', 'doctor_name']
    readonly_fields = ['booking_id', 'created_at', 'updated_at']
    ordering = ['-appointment_date', '-created_at']

    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'created_at', 'updated_at')
        }),
        ('Patient Details', {
            'fields': ('name', 'phone_number', 'mail_id')
        }),
        ('Appointment Details', {
            'fields': ('doctor_name', 'department', 'appointment_date')
        }),
    )
