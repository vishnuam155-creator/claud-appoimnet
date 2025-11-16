"""
Conversation Context Manager - Manages conversation state and history for RAG system
Maintains full conversation memory and booking state
"""

from voicebot.models import VoiceConversation, ConversationMessage
from django.utils import timezone


class ConversationContextManager:
    """
    Manages conversation context, history, and state for RAG-based booking
    """

    def __init__(self, session_id):
        self.session_id = session_id
        self.conversation = None
        self._load_or_create_conversation()

    def _load_or_create_conversation(self):
        """Load existing conversation or create new one"""
        self.conversation, created = VoiceConversation.objects.get_or_create(
            session_id=self.session_id,
            defaults={
                'stage': 'greeting',
                'completed': False
            }
        )

        if created:
            # Add initial system message
            self.add_message(
                role='system',
                content='Conversation started',
                intent='system_init'
            )

    def add_message(self, role, content, intent=None, extracted_data=None):
        """
        Add message to conversation history

        Args:
            role: 'user', 'assistant', or 'system'
            content: Message content
            intent: Detected intent (optional)
            extracted_data: Any data extracted from message (optional)
        """
        ConversationMessage.objects.create(
            conversation=self.conversation,
            role=role,
            content=content,
            intent=intent,
            extracted_data=extracted_data or {}
        )

    def get_conversation_history(self, limit=20):
        """
        Get conversation history as list of dicts

        Args:
            limit: Maximum number of messages to retrieve

        Returns:
            List of message dicts
        """
        messages = self.conversation.messages.order_by('timestamp')[:limit]

        return [
            {
                'role': msg.role,
                'content': msg.content,
                'intent': msg.intent,
                'timestamp': msg.timestamp.isoformat()
            }
            for msg in messages
        ]

    def update_booking_state(self, **kwargs):
        """
        Update booking state in conversation

        Args:
            **kwargs: Any booking fields (patient_name, doctor_id, etc.)
        """
        for field, value in kwargs.items():
            if hasattr(self.conversation, field) and value is not None:
                setattr(self.conversation, field, value)

        self.conversation.updated_at = timezone.now()
        self.conversation.save()

    def get_booking_state(self):
        """
        Get current booking state as dict

        Returns:
            Dict with all booking information
        """
        return {
            'stage': self.conversation.stage,
            'patient_name': self.conversation.patient_name,
            'patient_phone': self.conversation.patient_phone,
            'doctor_id': self.conversation.doctor_id,
            'doctor_name': self.conversation.doctor_name,
            'appointment_date': self.conversation.appointment_date.isoformat() if self.conversation.appointment_date else None,
            'appointment_time': self.conversation.appointment_time.strftime('%I:%M %p') if self.conversation.appointment_time else None,
            'appointment_id': self.conversation.appointment_id,
            'completed': self.conversation.completed
        }

    def set_stage(self, stage):
        """Update conversation stage"""
        self.conversation.stage = stage
        self.conversation.save()

    def get_stage(self):
        """Get current conversation stage"""
        return self.conversation.stage

    def mark_completed(self, appointment_id=None):
        """Mark conversation as completed"""
        self.conversation.completed = True
        if appointment_id:
            self.conversation.appointment_id = appointment_id
        self.conversation.save()

    def get_session_data(self):
        """
        Get session data in format compatible with existing system

        Returns:
            Dict with session data
        """
        booking_state = self.get_booking_state()

        # Convert to format expected by existing code
        session_data = {
            'stage': booking_state['stage'],
            'data': {}
        }

        # Add all non-null booking fields to data
        for key, value in booking_state.items():
            if value is not None and key != 'stage':
                if key == 'patient_name':
                    session_data['data']['patient_name'] = value
                elif key == 'patient_phone':
                    session_data['data']['phone'] = value
                elif key == 'appointment_date':
                    session_data['data']['appointment_date'] = value
                elif key == 'appointment_time':
                    session_data['data']['appointment_time'] = value
                elif key == 'doctor_id':
                    session_data['data']['doctor_id'] = value
                elif key == 'doctor_name':
                    session_data['data']['doctor_name'] = value

        return session_data

    def clear_field(self, field_name):
        """
        Clear a specific booking field (for changes/corrections)

        Args:
            field_name: Name of field to clear
        """
        field_mapping = {
            'doctor': ['doctor_id', 'doctor_name'],
            'date': ['appointment_date'],
            'time': ['appointment_time'],
            'phone': ['patient_phone'],
            'name': ['patient_name']
        }

        fields_to_clear = field_mapping.get(field_name, [field_name])

        for field in fields_to_clear:
            if hasattr(self.conversation, field):
                setattr(self.conversation, field, None)

        self.conversation.save()

    def get_summary(self):
        """
        Get conversation summary for debugging/logging

        Returns:
            Dict with conversation summary
        """
        return {
            'session_id': self.session_id,
            'stage': self.conversation.stage,
            'message_count': self.conversation.messages.count(),
            'completed': self.conversation.completed,
            'booking_state': self.get_booking_state(),
            'created_at': self.conversation.created_at.isoformat(),
            'updated_at': self.conversation.updated_at.isoformat()
        }

    def reset_conversation(self):
        """Reset conversation (for testing or restart)"""
        # Clear all booking data
        self.conversation.patient_name = None
        self.conversation.patient_phone = None
        self.conversation.doctor_id = None
        self.conversation.doctor_name = None
        self.conversation.appointment_date = None
        self.conversation.appointment_time = None
        self.conversation.appointment_id = None
        self.conversation.stage = 'greeting'
        self.conversation.completed = False
        self.conversation.save()

        # Add reset message
        self.add_message(
            role='system',
            content='Conversation reset',
            intent='system_reset'
        )
