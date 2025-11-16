from django.contrib import admin
from voicebot.models import VoiceConversation, ConversationMessage


@admin.register(VoiceConversation)
class VoiceConversationAdmin(admin.ModelAdmin):
    """Admin interface for VoiceConversation"""
    list_display = [
        'session_id', 'stage', 'patient_name', 'doctor_name',
        'appointment_date', 'appointment_time', 'completed', 'created_at'
    ]
    list_filter = ['stage', 'completed', 'created_at']
    search_fields = ['session_id', 'patient_name', 'patient_phone', 'doctor_name']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    ordering = ['-updated_at']

    fieldsets = (
        ('Session Information', {
            'fields': ('session_id', 'stage', 'completed')
        }),
        ('Patient Details', {
            'fields': ('patient_name', 'patient_phone')
        }),
        ('Appointment Details', {
            'fields': ('doctor_id', 'doctor_name', 'appointment_date', 'appointment_time', 'appointment_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ConversationMessage)
class ConversationMessageAdmin(admin.ModelAdmin):
    """Admin interface for ConversationMessage"""
    list_display = ['id', 'conversation', 'role', 'content_preview', 'intent', 'timestamp']
    list_filter = ['role', 'intent', 'timestamp']
    search_fields = ['conversation__session_id', 'content']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']

    def content_preview(self, obj):
        """Show preview of message content"""
        return obj.content[:100] + '...' if len(obj.content) > 100 else obj.content

    content_preview.short_description = 'Message Preview'

    fieldsets = (
        ('Message Information', {
            'fields': ('conversation', 'role', 'content')
        }),
        ('Metadata', {
            'fields': ('intent', 'extracted_data', 'timestamp')
        }),
    )
