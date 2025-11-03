from django.contrib import admin
from .models import WhatsAppMessage, WhatsAppSession


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = ['from_number', 'to_number', 'direction', 'body_preview', 'status', 'timestamp']
    list_filter = ['direction', 'status', 'timestamp']
    search_fields = ['from_number', 'to_number', 'body', 'session_id']
    readonly_fields = ['message_sid', 'from_number', 'to_number', 'body', 'direction', 'session_id', 'timestamp', 'created_at']
    date_hierarchy = 'timestamp'

    def body_preview(self, obj):
        return obj.body[:50] + '...' if len(obj.body) > 50 else obj.body
    body_preview.short_description = 'Message'


@admin.register(WhatsAppSession)
class WhatsAppSessionAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'session_id', 'is_active', 'appointment', 'last_message_at', 'created_at']
    list_filter = ['is_active', 'created_at', 'last_message_at']
    search_fields = ['phone_number', 'session_id']
    readonly_fields = ['session_id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
