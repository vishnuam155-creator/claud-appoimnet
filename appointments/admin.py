from django.contrib import admin
from .models import Appointment, AppointmentHistory


class AppointmentHistoryInline(admin.TabularInline):
    model = AppointmentHistory
    extra = 0
    readonly_fields = ['changed_at']
    can_delete = False


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = [
        'booking_id', 'patient_name', 'doctor', 'appointment_date', 
        'appointment_time', 'status', 'created_at'
    ]
    list_filter = ['status', 'appointment_date', 'doctor', 'created_at']
    search_fields = ['booking_id', 'patient_name', 'patient_phone', 'patient_email']
    readonly_fields = ['booking_id', 'created_at', 'updated_at', 'session_id']
    date_hierarchy = 'appointment_date'
    inlines = [AppointmentHistoryInline]
    
    fieldsets = (
        ('Booking Information', {
            'fields': ('booking_id', 'status', 'session_id')
        }),
        ('Doctor Details', {
            'fields': ('doctor', 'appointment_date', 'appointment_time')
        }),
        ('Patient Information', {
            'fields': (
                'patient_name', 'patient_phone', 'patient_email',
                'patient_age', 'patient_gender'
            )
        }),
        ('Medical Details', {
            'fields': ('symptoms', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_confirmed', 'mark_as_completed', 'mark_as_cancelled']
    
    def mark_as_confirmed(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, f'{updated} appointments marked as confirmed.')
    mark_as_confirmed.short_description = 'Mark selected as Confirmed'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} appointments marked as completed.')
    mark_as_completed.short_description = 'Mark selected as Completed'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} appointments marked as cancelled.')
    mark_as_cancelled.short_description = 'Mark selected as Cancelled'


@admin.register(AppointmentHistory)
class AppointmentHistoryAdmin(admin.ModelAdmin):
    list_display = ['appointment', 'status', 'changed_by', 'changed_at']
    list_filter = ['status', 'changed_by', 'changed_at']
    search_fields = ['appointment__booking_id', 'appointment__patient_name']
    readonly_fields = ['changed_at']
    date_hierarchy = 'changed_at'
