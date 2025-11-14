"""
Serializers for WhatsApp Integration models
"""
from rest_framework import serializers
from .models import WhatsAppMessage, WhatsAppSession
from appointments.serializers import AppointmentSerializer


class WhatsAppMessageSerializer(serializers.ModelSerializer):
    """Serializer for WhatsAppMessage model"""
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)

    class Meta:
        model = WhatsAppMessage
        fields = [
            'id', 'message_sid', 'from_number', 'to_number', 'body',
            'direction', 'direction_display', 'session_id', 'media_url',
            'status', 'timestamp', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WhatsAppSessionSerializer(serializers.ModelSerializer):
    """Serializer for WhatsAppSession model"""
    appointment = AppointmentSerializer(read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = WhatsAppSession
        fields = [
            'id', 'session_id', 'phone_number', 'is_active',
            'last_message_at', 'created_at', 'updated_at',
            'appointment', 'message_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        """Get total messages in session"""
        return WhatsAppMessage.objects.filter(session_id=obj.session_id).count()


class WhatsAppSessionDetailSerializer(WhatsAppSessionSerializer):
    """Detailed serializer for WhatsAppSession with messages"""
    messages = WhatsAppMessageSerializer(
        source='whatsappmessage_set',
        many=True,
        read_only=True
    )

    class Meta(WhatsAppSessionSerializer.Meta):
        fields = WhatsAppSessionSerializer.Meta.fields + ['messages']
