"""
Voice Assistant Manager with RAG - Complete Restructure
LLM-driven appointment booking using Gemini 2.5 Flash with Retrieval-Augmented Generation

This manager acts as a senior booking receptionist, handling natural conversations
with full context awareness and ability to handle changes at any stage.
"""

from datetime import datetime, timedelta
from django.utils import timezone
from voicebot.conversation_context_manager import ConversationContextManager
from voicebot.rag_retriever import RAGRetriever
from voicebot.gemini_rag_service import GeminiRAGService
from doctors.models import Doctor
from appointments.models import Appointment


class VoiceAssistantManagerRAG:
    """
    RAG-powered voice assistant for natural appointment booking conversations
    Uses Gemini 2.5 Flash with full database context and conversation history
    """

    def __init__(self, session_id):
        self.session_id = session_id
        self.context_manager = ConversationContextManager(session_id)
        self.rag_retriever = RAGRetriever()
        self.gemini_service = GeminiRAGService()

    def process_voice_message(self, message):
        """
        Process incoming voice message with RAG-based understanding

        Args:
            message: User's voice input (transcribed text)

        Returns:
            Dict with response message, stage, action, and data
        """
        try:
            # Get current state
            current_stage = self.context_manager.get_stage()
            booking_state = self.context_manager.get_booking_state()

            # Add user message to history
            self.context_manager.add_message(
                role='user',
                content=message or ''
            )

            # Retrieve relevant context from database
            context = self.rag_retriever.get_all_context_for_conversation(booking_state)

            # Get conversation history
            conversation_history = self.context_manager.get_conversation_history(limit=20)

            # Generate response using Gemini with RAG
            response = self.gemini_service.generate_response_with_context(
                user_message=message or '',
                conversation_history=conversation_history,
                context=context,
                current_stage=current_stage
            )

            # Extract LLM response
            assistant_message = response.get('message', 'I apologize, could you repeat that?')
            action = response.get('action', 'continue')
            extracted_data = response.get('extracted_data', {})
            next_stage = response.get('next_stage', current_stage)

            # Update booking state based on extracted data
            self._update_booking_from_extracted_data(extracted_data, booking_state)

            # Handle special intents
            intent = extracted_data.get('intent', 'proceed')
            if intent and intent != 'proceed':
                result = self._handle_special_intent(intent, extracted_data, booking_state, context)
                if result:
                    return result

            # Update conversation stage
            self.context_manager.set_stage(next_stage)

            # Add assistant message to history
            self.context_manager.add_message(
                role='assistant',
                content=assistant_message,
                intent=intent,
                extracted_data=extracted_data
            )

            # Get updated booking state
            updated_booking_state = self.context_manager.get_booking_state()

            return {
                'success': True,
                'message': assistant_message,
                'stage': next_stage,
                'action': action,
                'data': updated_booking_state
            }

        except Exception as e:
            import traceback
            print(f"Error in process_voice_message: {e}")
            traceback.print_exc()

            return {
                'success': False,
                'message': "I apologize, I encountered an error. Could you please repeat that?",
                'stage': current_stage,
                'action': 'error',
                'data': booking_state
            }

    def _update_booking_from_extracted_data(self, extracted_data, current_booking):
        """
        Update booking state from LLM-extracted data

        Args:
            extracted_data: Data extracted by LLM
            current_booking: Current booking state
        """
        updates = {}

        # Extract and validate patient name
        if extracted_data.get('patient_name'):
            updates['patient_name'] = extracted_data['patient_name']

        # Extract and validate phone
        if extracted_data.get('phone'):
            phone = extracted_data['phone']
            # Clean phone number
            phone_digits = ''.join(filter(str.isdigit, phone))
            if len(phone_digits) == 10:
                updates['patient_phone'] = phone_digits

        # Extract doctor information
        if extracted_data.get('doctor_id'):
            doctor_id_value = extracted_data['doctor_id']

            # Handle case where LLM returns name instead of ID
            if isinstance(doctor_id_value, str) and not doctor_id_value.isdigit():
                # Try to find doctor by name
                doctor = self._find_doctor_by_name(doctor_id_value)
                if doctor:
                    updates['doctor_id'] = doctor.id
                    updates['doctor_name'] = doctor.name
            else:
                # It's a valid numeric ID
                try:
                    updates['doctor_id'] = int(doctor_id_value)
                except (ValueError, TypeError):
                    print(f"Invalid doctor_id format: {doctor_id_value}")

        if extracted_data.get('doctor_name') and 'doctor_name' not in updates:
            # Only update if not already set from doctor_id lookup
            doctor_name = extracted_data['doctor_name']
            updates['doctor_name'] = doctor_name

            # Try to find doctor ID from name if not already set
            if 'doctor_id' not in updates:
                doctor = self._find_doctor_by_name(doctor_name)
                if doctor:
                    updates['doctor_id'] = doctor.id

        # Extract appointment date
        if extracted_data.get('appointment_date'):
            try:
                date_str = extracted_data['appointment_date']
                if isinstance(date_str, str):
                    # Parse YYYY-MM-DD format
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                    updates['appointment_date'] = date_obj
            except Exception as e:
                print(f"Error parsing date: {e}")

        # Extract appointment time
        if extracted_data.get('appointment_time'):
            try:
                time_str = extracted_data['appointment_time']
                if isinstance(time_str, str):
                    # Parse time in various formats
                    for fmt in ['%I:%M %p', '%H:%M', '%I %p']:
                        try:
                            time_obj = datetime.strptime(time_str, fmt).time()
                            updates['appointment_time'] = time_obj
                            break
                        except ValueError:
                            continue
            except Exception as e:
                print(f"Error parsing time: {e}")

        # Apply updates
        if updates:
            self.context_manager.update_booking_state(**updates)

    def _handle_special_intent(self, intent, extracted_data, booking_state, context):
        """
        Handle special intents like change requests, cancellations, etc.

        Args:
            intent: Detected intent
            extracted_data: Extracted data from LLM
            booking_state: Current booking state
            context: Retrieved context

        Returns:
            Response dict if intent was handled, None otherwise
        """
        if intent == 'cancel':
            return self._handle_cancellation()

        elif intent == 'change_doctor':
            return self._handle_change_doctor(extracted_data, context)

        elif intent == 'change_date':
            return self._handle_change_date(extracted_data, context)

        elif intent == 'change_time':
            return self._handle_change_time(extracted_data, context)

        elif intent == 'change_phone':
            self.context_manager.clear_field('phone')
            self.context_manager.set_stage('phone_collection')
            return None  # Let normal flow handle

        elif intent == 'change_name':
            self.context_manager.clear_field('name')
            self.context_manager.set_stage('patient_name')
            return None  # Let normal flow handle

        elif intent == 'confirm':
            # Handle booking confirmation
            if booking_state.get('stage') == 'confirmation':
                return self._create_appointment(booking_state)

        return None

    def _handle_cancellation(self):
        """Handle booking cancellation"""
        self.context_manager.mark_completed()
        self.context_manager.add_message(
            role='system',
            content='Booking cancelled by user'
        )

        return {
            'success': True,
            'message': "I understand. Your booking has been cancelled. If you'd like to book an appointment later, just let me know. Is there anything else I can help you with?",
            'stage': 'completed',
            'action': 'cancelled',
            'data': self.context_manager.get_booking_state()
        }

    def _handle_change_doctor(self, extracted_data, context):
        """Handle request to change doctor"""
        self.context_manager.clear_field('doctor')
        self.context_manager.set_stage('doctor_selection')

        # If new doctor mentioned, try to find it
        new_doctor_name = extracted_data.get('extracted_value')

        if new_doctor_name:
            # Search for doctor
            doctor = self._find_doctor_by_name(new_doctor_name)
            if doctor:
                self.context_manager.update_booking_state(
                    doctor_id=doctor.id,
                    doctor_name=doctor.name
                )

        return None  # Let normal flow continue

    def _handle_change_date(self, extracted_data, context):
        """Handle request to change date"""
        self.context_manager.clear_field('date')
        self.context_manager.clear_field('time')  # Also clear time since it depends on date
        self.context_manager.set_stage('date_selection')

        return None  # Let normal flow continue

    def _handle_change_time(self, extracted_data, context):
        """Handle request to change time"""
        self.context_manager.clear_field('time')
        self.context_manager.set_stage('time_selection')

        return None  # Let normal flow continue

    def _find_doctor_by_name(self, name):
        """Find doctor by name with fuzzy matching"""
        try:
            # Try exact match first
            doctor = Doctor.objects.filter(
                name__iexact=name,
                is_active=True
            ).first()

            if doctor:
                return doctor

            # Try partial match
            doctor = Doctor.objects.filter(
                name__icontains=name,
                is_active=True
            ).first()

            return doctor

        except Exception as e:
            print(f"Error finding doctor: {e}")
            return None

    def _create_appointment(self, booking_state):
        """
        Create appointment in database

        Args:
            booking_state: Complete booking information

        Returns:
            Response dict with booking confirmation
        """
        try:
            # Validate all required fields
            required_fields = ['patient_name', 'patient_phone', 'doctor_id', 'appointment_date', 'appointment_time']
            for field in required_fields:
                if not booking_state.get(field):
                    return {
                        'success': False,
                        'message': f"Missing required information: {field}. Could you please provide that?",
                        'stage': self.context_manager.get_stage(),
                        'action': 'error',
                        'data': booking_state
                    }

            # Get doctor
            doctor = Doctor.objects.get(id=booking_state['doctor_id'])

            # Parse date and time
            if isinstance(booking_state['appointment_date'], str):
                appointment_date = datetime.strptime(booking_state['appointment_date'], '%Y-%m-%d').date()
            else:
                appointment_date = booking_state['appointment_date']

            if isinstance(booking_state['appointment_time'], str):
                appointment_time = datetime.strptime(booking_state['appointment_time'], '%I:%M %p').time()
            else:
                appointment_time = booking_state['appointment_time']

            # Check if slot is still available
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status__in=['pending', 'confirmed']
            ).exists()

            if existing:
                return {
                    'success': False,
                    'message': "I'm sorry, but that time slot was just booked by someone else. Let me show you other available times.",
                    'stage': 'time_selection',
                    'action': 'slot_taken',
                    'data': booking_state
                }

            # Create appointment
            appointment = Appointment.objects.create(
                doctor=doctor,
                patient_name=booking_state['patient_name'],
                patient_phone=booking_state['patient_phone'],
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='confirmed',
                symptoms='Booked via voice assistant',
                session_id=self.session_id
            )

            # Mark conversation as completed
            self.context_manager.mark_completed(appointment_id=appointment.id)

            # Format success message
            date_formatted = appointment_date.strftime('%B %d, %Y')
            time_formatted = appointment_time.strftime('%I:%M %p')

            success_message = f"""Perfect! Your appointment is confirmed!

Your booking ID is {appointment.booking_id}.

To recap:
- Patient: {booking_state['patient_name']}
- Doctor: Dr. {doctor.name} ({doctor.specialization.name if doctor.specialization else 'General'})
- Date: {date_formatted}
- Time: {time_formatted}
- Phone: {booking_state['patient_phone']}

You'll receive an SMS confirmation shortly. Please arrive 10 minutes early for your appointment. Is there anything else I can help you with today?"""

            self.context_manager.add_message(
                role='assistant',
                content=success_message,
                intent='booking_complete',
                extracted_data={'appointment_id': appointment.id, 'booking_id': appointment.booking_id}
            )

            # Try to send SMS (if configured)
            try:
                self._send_confirmation_sms(appointment, booking_state)
            except Exception as e:
                print(f"SMS sending failed: {e}")

            return {
                'success': True,
                'message': success_message,
                'stage': 'completed',
                'action': 'booking_complete',
                'data': {
                    **booking_state,
                    'appointment_id': appointment.id,
                    'booking_id': appointment.booking_id
                }
            }

        except Doctor.DoesNotExist:
            return {
                'success': False,
                'message': "I'm sorry, there was an error finding the doctor. Could we start over?",
                'stage': 'doctor_selection',
                'action': 'error',
                'data': booking_state
            }

        except Exception as e:
            import traceback
            print(f"Error creating appointment: {e}")
            traceback.print_exc()

            return {
                'success': False,
                'message': "I apologize, but I encountered an error while creating your appointment. This might be a technical issue. Could you please try again?",
                'stage': 'confirmation',
                'action': 'error',
                'data': booking_state
            }

    def _send_confirmation_sms(self, appointment, booking_state):
        """Send SMS confirmation (if Twilio is configured)"""
        try:
            from voicebot.sms_service import send_appointment_confirmation_sms

            send_appointment_confirmation_sms(
                phone=booking_state['patient_phone'],
                patient_name=booking_state['patient_name'],
                doctor_name=appointment.doctor.name,
                appointment_date=appointment.appointment_date,
                appointment_time=appointment.appointment_time,
                booking_id=appointment.booking_id
            )

        except ImportError:
            print("SMS service not configured")
        except Exception as e:
            print(f"Error sending SMS: {e}")

    def get_conversation_summary(self):
        """Get conversation summary for debugging"""
        return self.context_manager.get_summary()

    def reset_conversation(self):
        """Reset conversation (for testing)"""
        self.context_manager.reset_conversation()
