from django.db import models
from django.utils import timezone


class WhatsAppMessage(models.Model):
    """Model to store WhatsApp message logs"""
    MESSAGE_DIRECTION = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]

    message_sid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    from_number = models.CharField(max_length=20)
    to_number = models.CharField(max_length=20)
    body = models.TextField()
    direction = models.CharField(max_length=10, choices=MESSAGE_DIRECTION)
    session_id = models.CharField(max_length=255, db_index=True)
    media_url = models.URLField(null=True, blank=True)
    status = models.CharField(max_length=50, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['from_number', '-timestamp']),
            models.Index(fields=['session_id']),
        ]

    def __str__(self):
        return f"{self.direction} - {self.from_number} - {self.timestamp}"


class WhatsAppSession(models.Model):
    """Model to track WhatsApp conversation sessions"""
    session_id = models.CharField(max_length=255, unique=True, db_index=True)
    phone_number = models.CharField(max_length=20, db_index=True)
    is_active = models.BooleanField(default=True)
    last_message_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Link to appointment if booking completed
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='whatsapp_sessions'
    )

    class Meta:
        ordering = ['-last_message_at']

    def __str__(self):
        return f"{self.phone_number} - {self.session_id}"
