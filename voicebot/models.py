from django.db import models
from django.utils import timezone


class VoiceConversation(models.Model):
    """
    Stores voice conversation sessions for RAG-based context retrieval
    """
    session_id = models.CharField(max_length=100, unique=True, db_index=True)

    # Booking state
    stage = models.CharField(max_length=50, default='greeting')

    # Collected data
    patient_name = models.CharField(max_length=200, blank=True, null=True)
    patient_phone = models.CharField(max_length=15, blank=True, null=True)
    doctor_id = models.IntegerField(blank=True, null=True)
    doctor_name = models.CharField(max_length=200, blank=True, null=True)
    appointment_date = models.DateField(blank=True, null=True)
    appointment_time = models.TimeField(blank=True, null=True)

    # Appointment reference
    appointment_id = models.IntegerField(blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['completed']),
        ]

    def __str__(self):
        return f"Conversation {self.session_id} - {self.stage}"


class ConversationMessage(models.Model):
    """
    Individual messages in voice conversation for full conversation history
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(
        VoiceConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()

    # Metadata for RAG
    intent = models.CharField(max_length=50, blank=True, null=True)
    extracted_data = models.JSONField(default=dict, blank=True)

    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}"
