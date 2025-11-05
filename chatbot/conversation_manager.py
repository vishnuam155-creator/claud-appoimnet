from datetime import datetime, timedelta
from django.core.cache import cache
from doctors.models import Doctor, DoctorSchedule
from appointments.models import Appointment
from patient_booking.models import PatientRecord
from .claude_service import ClaudeService
from .date_parser import DateParser
import json


class ConversationManager:
    """
    Manages chatbot conversation flow and state
    """
    
    STAGES = [
        'greeting',
        'symptoms',
        'doctor_selection',
        'date_selection',
        'time_selection',
        'patient_details',
        'confirmation'
    ]
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.cache_key = f"chat_session_{session_id}"
        self.claude = ClaudeService()
        self.date_parser = DateParser()
        self.state = self._load_state()
    
    def _load_state(self):
        """Load conversation state from cache"""
        state = cache.get(self.cache_key)
        if not state:
            state = {
                'stage': 'greeting',
                'conversation_history': [],
                'data': {},
                'timestamp': datetime.now().isoformat()
            }
        return state
    
    def _save_state(self):
        """Save conversation state to cache"""
        cache.set(self.cache_key, self.state, timeout=3600)  # 1 hour
    
    def process_message(self, user_message):
        """
        Process user message with intelligent intent detection
        Enhanced to understand changes, corrections, and backward navigation
        """
        # Add user message to history
        self.state['conversation_history'].append({
            'role': 'user',
            'content': user_message,
            'timestamp': datetime.now().isoformat()
        })

        stage = self.state['stage']

        # Skip intent detection for greeting stage
        if stage == 'greeting':
            response = self._handle_greeting(user_message)
        else:
            # Detect user intent using AI
            intent = self.claude.detect_intent(
                user_message,
                stage,
                self.state['data']
            )

            print(f"[Intent Detection] Stage: {stage}, Intent: {intent['intent']}, Confidence: {intent['confidence']}")

            # Handle intent-based routing
            # Special case: If user is in date_selection stage and intent is change_date,
            # treat it as normal date selection (proceed)
            if stage == 'date_selection' and intent['intent'] == 'change_date':
                response = self._handle_date_selection(user_message)
            # Special case: If user is in doctor_selection stage and intent is change_doctor,
            # treat it as normal doctor selection (proceed)
            elif stage == 'doctor_selection' and intent['intent'] == 'change_doctor':
                response = self._handle_doctor_selection(user_message)
            # Special case: If user is in time_selection stage and intent is change_time,
            # treat it as normal time selection (proceed)
            elif stage == 'time_selection' and intent['intent'] == 'change_time':
                response = self._handle_time_selection(user_message)
            elif intent['intent'] == 'change_doctor':
                response = self._handle_change_doctor(user_message, intent)
            elif intent['intent'] == 'change_date':
                response = self._handle_change_date(user_message, intent)
            elif intent['intent'] == 'change_time':
                response = self._handle_change_time(user_message, intent)
            elif intent['intent'] == 'go_back':
                response = self._handle_go_back(user_message, intent)
            elif intent['intent'] == 'cancel':
                response = self._handle_cancel(user_message)
            elif intent['intent'] == 'clarify':
                response = self._handle_clarification(user_message, intent)
            else:
                # Proceed normally based on current stage
                if stage == 'symptoms':
                    response = self._handle_symptoms(user_message)
                elif stage == 'doctor_selection':
                    response = self._handle_doctor_selection(user_message)
                elif stage == 'date_selection':
                    response = self._handle_date_selection(user_message)
                elif stage == 'time_selection':
                    response = self._handle_time_selection(user_message)
                elif stage == 'patient_details':
                    response = self._handle_patient_details(user_message)
                elif stage == 'confirmation':
                    response = self._handle_confirmation(user_message)
                else:
                    response = self._default_response()

        # Add bot response to history
        self.state['conversation_history'].append({
            'role': 'assistant',
            'content': response['message'],
            'timestamp': datetime.now().isoformat()
        })

        self._save_state()
        return response
    
    def _handle_greeting(self, message):
        """Handle initial greeting with concise, direct responses and appointment context"""
        # Handle appointment context actions
        if message.lower() in ['new_booking', 'cancel_appointment', 'reschedule', 'details']:
            return self._handle_appointment_action(message.lower())

        # Check for existing appointments for this patient
        existing_appointment = self._check_existing_appointments()

        # If patient has an upcoming appointment, provide context
        if existing_appointment:
            apt_date = existing_appointment.appointment_date
            apt_time = existing_appointment.appointment_time
            doctor_name = existing_appointment.doctor.name
            booking_id = existing_appointment.booking_id

            # Format appointment details
            apt_datetime = datetime.combine(apt_date, apt_time)
            formatted_date = apt_date.strftime('%A, %B %d, %Y')
            formatted_time = apt_time.strftime('%I:%M %p')

            # Check if appointment is today or upcoming
            today = datetime.now().date()
            if apt_date == today:
                time_context = "today"
            elif apt_date == today + timedelta(days=1):
                time_context = "tomorrow"
            else:
                days_until = (apt_date - today).days
                time_context = f"in {days_until} days"

            # Provide appointment context with options
            appointment_message = f"👋 Hello! I see you have an upcoming appointment:\n\n"
            appointment_message += f"📋 Booking ID: {booking_id}\n"
            appointment_message += f"👨‍⚕️ Doctor: Dr. {doctor_name}\n"
            appointment_message += f"📅 Date: {formatted_date} ({time_context})\n"
            appointment_message += f"⏰ Time: {formatted_time}\n\n"
            appointment_message += "What would you like to do?"

            self.state['data']['existing_appointment_id'] = existing_appointment.id

            return {
                'message': appointment_message,
                'action': 'appointment_context',
                'options': [
                    {'label': '📅 Book New Appointment', 'value': 'new_booking'},
                    {'label': '❌ Cancel Appointment', 'value': 'cancel_appointment'},
                    {'label': '✏️ Reschedule', 'value': 'reschedule'},
                    {'label': 'ℹ️ Appointment Details', 'value': 'details'}
                ]
            }

        # Check if user mentioned symptoms directly
        if any(word in message.lower() for word in ['pain', 'hurt', 'sick', 'fever', 'problem', 'issue', 'cough', 'headache']):
            self.state['stage'] = 'symptoms'
            return {
                'message': "I understand you're experiencing some health issues. Could you describe your symptoms in detail? This will help me find the right doctor for you.",
                'action': 'ask_symptoms',
                'options': None
            }

        # Standard greeting - concise and direct
        self.state['stage'] = 'symptoms'
        return {
            'message': "Hello! I'm here to help you book a medical appointment.\n\nPlease tell me:\n• What symptoms are you experiencing?\n• Or choose a doctor specialization below",
            'action': 'ask_symptoms',
            'options': self._get_specialization_options()
        }

    def _handle_appointment_action(self, action):
        """Handle actions related to existing appointments"""
        existing_appointment = self._check_existing_appointments()

        if not existing_appointment:
            # No appointment found, proceed with new booking
            self.state['stage'] = 'symptoms'
            return {
                'message': "I couldn't find an existing appointment. Let's create a new one!\n\nPlease tell me:\n• What symptoms are you experiencing?\n• Or choose a doctor specialization below",
                'action': 'ask_symptoms',
                'options': self._get_specialization_options()
            }

        if action == 'new_booking':
            # Start new booking process
            self.state['stage'] = 'symptoms'
            return {
                'message': "Great! Let's book a new appointment.\n\nPlease tell me:\n• What symptoms are you experiencing?\n• Or choose a doctor specialization below",
                'action': 'ask_symptoms',
                'options': self._get_specialization_options()
            }

        elif action == 'cancel_appointment':
            # Cancel the appointment
            try:
                from appointments.models import AppointmentHistory

                # Validate appointment timing (minimum 2 hours notice)
                validation = self._validate_appointment_timing(existing_appointment, action='cancel', minimum_hours=2)
                if not validation['valid']:
                    return {
                        'message': validation['message'],
                        'action': 'validation_failed',
                        'options': [
                            {'label': '📞 Contact Clinic', 'value': 'done'},
                            {'label': '↩️ Back to Menu', 'value': 'restart'}
                        ]
                    }

                # Store old status before cancellation
                old_status = existing_appointment.status

                # Update appointment status
                existing_appointment.status = 'cancelled'
                existing_appointment.save()

                # Create appointment history record
                AppointmentHistory.objects.create(
                    appointment=existing_appointment,
                    status='cancelled',
                    notes=f'Appointment cancelled by patient via WhatsApp',
                    changed_by='patient',
                    action='cancellation',
                    reason='Patient requested cancellation',
                    old_date=existing_appointment.appointment_date,
                    old_time=existing_appointment.appointment_time
                )

                apt_date = existing_appointment.appointment_date.strftime('%A, %B %d, %Y')
                apt_time = existing_appointment.appointment_time.strftime('%I:%M %p')

                return {
                    'message': f"✅ Your appointment has been cancelled successfully.\n\n📋 Booking ID: {existing_appointment.booking_id}\n👨‍⚕️ Doctor: Dr. {existing_appointment.doctor.name}\n📅 Date: {apt_date}\n⏰ Time: {apt_time}\n\n📧 A cancellation confirmation will be sent to you shortly.\n\nWould you like to book a new appointment?",
                    'action': 'appointment_cancelled',
                    'options': [
                        {'label': '📅 Book New Appointment', 'value': 'new_booking'},
                        {'label': '✅ Done', 'value': 'done'}
                    ]
                }
            except Exception as e:
                print(f"Error cancelling appointment: {str(e)}")
                return {
                    'message': "⚠️ Sorry, there was an error cancelling your appointment. Please contact support or try again later.",
                    'action': 'error',
                    'options': None
                }

        elif action == 'reschedule':
            # Start rescheduling process
            # Validate appointment timing (minimum 2 hours notice)
            validation = self._validate_appointment_timing(existing_appointment, action='reschedule', minimum_hours=2)
            if not validation['valid']:
                return {
                    'message': validation['message'],
                    'action': 'validation_failed',
                    'options': [
                        {'label': '📞 Contact Clinic', 'value': 'done'},
                        {'label': '↩️ Back to Menu', 'value': 'restart'}
                    ]
                }

            self.state['data']['rescheduling_appointment_id'] = existing_appointment.id
            self.state['data']['doctor_id'] = existing_appointment.doctor.id
            self.state['stage'] = 'date_selection'

            return {
                'message': f"Let's reschedule your appointment with Dr. {existing_appointment.doctor.name}.\n\nPlease choose a new date:",
                'action': 'select_date',
                'options': self._get_date_options(existing_appointment.doctor.id, days=7)
            }

        elif action == 'details':
            # Show full appointment details
            apt_date = existing_appointment.appointment_date.strftime('%A, %B %d, %Y')
            apt_time = existing_appointment.appointment_time.strftime('%I:%M %p')

            details_message = f"📋 *Appointment Details*\n\n"
            details_message += f"🆔 Booking ID: {existing_appointment.booking_id}\n"
            details_message += f"👨‍⚕️ Doctor: Dr. {existing_appointment.doctor.name}\n"
            details_message += f"🏥 Specialization: {existing_appointment.doctor.specialization.name}\n"
            details_message += f"📅 Date: {apt_date}\n"
            details_message += f"⏰ Time: {apt_time}\n"
            details_message += f"👤 Patient: {existing_appointment.patient_name}\n"
            details_message += f"📞 Phone: {existing_appointment.patient_phone}\n"

            if existing_appointment.patient_email:
                details_message += f"✉️ Email: {existing_appointment.patient_email}\n"

            if existing_appointment.symptoms:
                details_message += f"💬 Symptoms: {existing_appointment.symptoms}\n"

            details_message += f"📊 Status: {existing_appointment.status.title()}"

            return {
                'message': details_message,
                'action': 'show_details',
                'options': [
                    {'label': '📅 Book New Appointment', 'value': 'new_booking'},
                    {'label': '❌ Cancel This Appointment', 'value': 'cancel_appointment'},
                    {'label': '✏️ Reschedule', 'value': 'reschedule'},
                    {'label': '✅ Done', 'value': 'done'}
                ]
            }

        else:
            # Unknown action
            return self._handle_greeting("Hello")

    def _handle_symptoms(self, message):
        """Handle symptom analysis with concise responses"""
        # Analyze symptoms using AI
        analysis = self.claude.analyze_symptoms(message)

        self.state['data']['symptoms'] = message
        self.state['data']['suggested_specialization'] = analysis['specialization']

        # Get doctors for this specialization
        doctors = Doctor.objects.filter(
            specialization__name=analysis['specialization'],
            is_active=True
        )

        if doctors.exists():
            self.state['stage'] = 'doctor_selection'

            # Concise response - straight to the point
            response_text = f"Based on your symptoms, I recommend a **{analysis['specialization']}**.\n\nAvailable doctors:"

            return {
                'message': response_text,
                'action': 'select_doctor',
                'options': self._get_doctor_options(doctors)
            }
        else:
            return {
                'message': f"I recommend seeing a {analysis['specialization']}, but unfortunately we don't have any available at the moment. Would you like to see a General Physician instead?",
                'action': 'no_doctors',
                'options': self._get_alternative_doctors()
            }
    
    def _handle_doctor_selection(self, message):
        """Handle doctor selection"""
        # Check if message is a doctor ID
        doctor = None
        try:
            if message.isdigit():
                doctor = Doctor.objects.get(id=int(message), is_active=True)
        except Doctor.DoesNotExist:
            # Try to find doctor by name
            doctors = Doctor.objects.filter(name__icontains=message, is_active=True)
            if doctors.count() == 1:
                doctor = doctors.first()
        
        if doctor:
            self.state['data']['doctor_id'] = doctor.id
            self.state['data']['doctor_name'] = doctor.name
            self.state['stage'] = 'date_selection'
            
            return {
                'message': f"Great! You've selected Dr. {doctor.name}.\n\nWhen would you like to schedule your appointment?",
                'action': 'select_date',
                'options': self._get_date_options(doctor.id)
            }
        else:
            return {
                'message': "I couldn't find that doctor. Please select from the available options:",
                'action': 'select_doctor',
                'options': self._get_doctor_options(
                    Doctor.objects.filter(is_active=True)
                )
            }
    
    def _handle_date_selection(self, message):
        """Handle date selection with natural language support"""
        
        # Try to parse the date using natural language
        parsed_date = self.date_parser.parse(message)
        
        # If parsing failed, try the old ISO format
        if not parsed_date:
            try:
                parsed_date = datetime.strptime(message, '%Y-%m-%d').date()
            except ValueError:
                # Still couldn't parse
                return {
                    'message': "I couldn't understand that date. Please try:\n• Selecting from the options below\n• Or saying something like 'next Monday', 'November 3', 'tomorrow'",
                    'action': 'select_date',
                    'options': self._get_date_options(self.state['data']['doctor_id'], days=7)
                }
        
        # Check if date is valid
        if not self.date_parser.is_valid_future_date(parsed_date):
            return {
                'message': "Please select a date that is today or in the future (within the next 90 days).",
                'action': 'select_date',
                'options': self._get_date_options(self.state['data']['doctor_id'], days=7)
            }
        
        self.state['data']['appointment_date'] = parsed_date.strftime('%Y-%m-%d')
        self.state['stage'] = 'time_selection'
        
        # Get available time slots
        slots = self._get_available_slots(
            self.state['data']['doctor_id'],
            parsed_date
        )
        
        if slots:
            return {
                'message': f"Great! Available time slots for {parsed_date.strftime('%A, %B %d, %Y')}:",
                'action': 'select_time',
                'options': slots
            }
        else:
            return {
                'message': f"Sorry, no slots available on {parsed_date.strftime('%A, %B %d, %Y')}. Please choose another date:",
                'action': 'select_date',
                'options': self._get_date_options(self.state['data']['doctor_id'], days=7)
            }
    
    def _handle_time_selection(self, message):
        """Handle time slot selection with validation"""
        from datetime import datetime as dt

        # Get the selected time and validate it's available
        selected_time = message.strip()
        appointment_date = dt.strptime(self.state['data']['appointment_date'], '%Y-%m-%d').date()
        doctor_id = self.state['data']['doctor_id']

        # Check if the selected time is available
        try:
            # Parse the time (could be in format "14:30" or "02:30 PM")
            time_formats = ['%H:%M', '%I:%M %p', '%I:%M%p']
            parsed_time = None

            for fmt in time_formats:
                try:
                    parsed_time = dt.strptime(selected_time, fmt).time()
                    break
                except ValueError:
                    continue

            if not parsed_time:
                # Try to extract time from the message
                selected_time = selected_time.replace(' ', '')
                for fmt in time_formats:
                    try:
                        parsed_time = dt.strptime(selected_time, fmt).time()
                        break
                    except ValueError:
                        continue

            if not parsed_time:
                return {
                    'message': "⚠️ Invalid time format. Please select a time from the available options.",
                    'action': 'select_time',
                    'options': self._get_available_slots(doctor_id, appointment_date)
                }

            # Check if this time slot is already booked
            # If rescheduling, exclude the current appointment from the check
            availability_check = Appointment.objects.filter(
                doctor_id=doctor_id,
                appointment_date=appointment_date,
                appointment_time=parsed_time,
                status__in=['pending', 'confirmed']
            )

            # If rescheduling, exclude the appointment being rescheduled
            if 'rescheduling_appointment_id' in self.state['data']:
                availability_check = availability_check.exclude(
                    id=self.state['data']['rescheduling_appointment_id']
                )

            existing_appointment = availability_check.first()

            if existing_appointment:
                # Slot is already booked
                available_slots = self._get_available_slots(doctor_id, appointment_date)
                return {
                    'message': f"⚠️ Sorry, the time slot {selected_time} is already booked.\n\nPlease choose from the available time slots:",
                    'action': 'select_time',
                    'options': available_slots
                }

            # Time is valid and available
            self.state['data']['appointment_time'] = parsed_time.strftime('%H:%M')

            # Check if we're rescheduling an existing appointment
            if 'rescheduling_appointment_id' in self.state['data']:
                # Rescheduling - update the existing appointment
                try:
                    appointment = Appointment.objects.get(id=self.state['data']['rescheduling_appointment_id'])

                    # IMPORTANT: Store old values BEFORE updating the appointment
                    old_date = appointment.appointment_date
                    old_time = appointment.appointment_time
                    old_formatted_date = old_date.strftime('%A, %B %d, %Y')
                    old_formatted_time = old_time.strftime('%I:%M %p')

                    # Update appointment with new date and time
                    appointment.appointment_date = appointment_date
                    appointment.appointment_time = parsed_time
                    appointment.save()

                    # Create appointment history record with old and new values
                    from appointments.models import AppointmentHistory
                    AppointmentHistory.objects.create(
                        appointment=appointment,
                        status=appointment.status,
                        notes=f'Appointment rescheduled from {old_formatted_date} {old_formatted_time} to {appointment_date.strftime("%A, %B %d, %Y")} {parsed_time.strftime("%I:%M %p")}',
                        changed_by='patient',
                        action='reschedule',
                        old_date=old_date,
                        old_time=old_time,
                        new_date=appointment_date,
                        new_time=parsed_time,
                        reason='Patient requested reschedule via WhatsApp'
                    )

                    self.state['stage'] = 'confirmation'

                    # Format confirmation for rescheduled appointment
                    formatted_date = appointment_date.strftime('%A, %B %d, %Y')
                    formatted_time = parsed_time.strftime('%I:%M %p')

                    return {
                        'message': f"✅ Appointment Rescheduled Successfully!\n\n📋 Booking ID: {appointment.booking_id}\n👨‍⚕️ Doctor: Dr. {appointment.doctor.name}\n\n📅 Previous: {old_formatted_date} at {old_formatted_time}\n📅 New Date: {formatted_date}\n⏰ New Time: {formatted_time}\n\n👤 Patient: {appointment.patient_name}\n📞 Phone: {appointment.patient_phone}\n\n✨ You'll receive a confirmation shortly.",
                        'action': 'booking_complete',
                        'options': [
                            {'label': '📅 Book Another Appointment', 'value': 'new_booking'},
                            {'label': '✅ Done', 'value': 'done'}
                        ]
                    }

                except Appointment.DoesNotExist:
                    return {
                        'message': "⚠️ Sorry, I couldn't find the appointment to reschedule. Let's start over.",
                        'action': 'error',
                        'options': [
                            {'label': '🔄 Start Over', 'value': 'restart'}
                        ]
                    }
                except Exception as e:
                    print(f"Error rescheduling appointment: {str(e)}")
                    return {
                        'message': "⚠️ There was an error rescheduling your appointment. Please try again.",
                        'action': 'error',
                        'options': None
                    }
            else:
                # New booking - proceed to collect patient details
                self.state['stage'] = 'patient_details'

                return {
                    'message': f"Perfect! Your appointment is scheduled for {self.state['data']['appointment_date']} at {parsed_time.strftime('%I:%M %p')}.\n\nNow, I need some details:\n\nWhat's your full name?",
                    'action': 'collect_name',
                    'options': None
                }

        except Exception as e:
            print(f"Error in time selection: {str(e)}")
            return {
                'message': "⚠️ There was an error processing your time selection. Please try again.",
                'action': 'select_time',
                'options': self._get_available_slots(doctor_id, appointment_date)
            }
    
    def _handle_patient_details(self, message):
        """Handle patient details collection"""
        data = self.state['data']

        if 'patient_name' not in data:
            # Validate name
            if not message or len(message.strip()) < 2:
                return {
                    'message': "Please provide a valid name (at least 2 characters).",
                    'action': 'collect_name',
                    'options': None
                }
            # Extract name
            data['patient_name'] = message.strip()
            return {
                'message': f"Thank you, {message}! What's your phone number?",
                'action': 'collect_phone',
                'options': None
            }
        elif 'patient_phone' not in data:
            # Validate phone number (basic validation)
            phone = message.strip().replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
            if not phone.isdigit() or len(phone) < 10:
                return {
                    'message': "Please provide a valid phone number (at least 10 digits).",
                    'action': 'collect_phone',
                    'options': None
                }
            # Extract phone
            data['patient_phone'] = message.strip()
            return {
                'message': "Would you like to provide your email address for appointment confirmations?",
                'action': 'collect_email',
                'options': [
                    {'label': '✉️ Enter Email', 'value': 'enter_email'},
                    {'label': '⏭️ Skip Email', 'value': 'skip_email'}
                ]
            }
        elif 'patient_email' not in data:
            # Handle email input or skip
            if message.lower() in ['skip', 'skip_email', 'skip email']:
                # Skip email - set to empty and proceed to confirmation
                data['patient_email'] = ''
                self.state['stage'] = 'confirmation'

                # Validate all required data before creating appointment
                validation_error = self._validate_booking_data()
                if validation_error:
                    return {
                        'message': f"⚠️ {validation_error}\n\nPlease start over by providing your symptoms.",
                        'action': 'error',
                        'options': [
                            {'label': '🔄 Start Over', 'value': 'restart'}
                        ]
                    }

                # Create appointment
                appointment = self._create_appointment()

                if appointment:
                    return self._format_confirmation_response(appointment)
                else:
                    return {
                        'message': "⚠️ Sorry, there was an error creating your appointment. Please try again or start over.",
                        'action': 'error',
                        'options': [
                            {'label': '🔄 Try Again', 'value': 'retry'},
                            {'label': '↩️ Start Over', 'value': 'restart'}
                        ]
                    }
            elif message == 'enter_email':
                # User wants to enter email
                return {
                    'message': "Please type your email address:",
                    'action': 'collect_email_text',
                    'options': None
                }
            else:
                # User typed an email directly - validate it
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, message.strip()):
                    return {
                        'message': "Please provide a valid email address (e.g., example@email.com) or skip this step.",
                        'action': 'collect_email',
                        'options': [
                            {'label': '✉️ Enter Email', 'value': 'enter_email'},
                            {'label': '⏭️ Skip Email', 'value': 'skip_email'}
                        ]
                    }

                data['patient_email'] = message.strip()
                self.state['stage'] = 'confirmation'

                # Validate all required data before creating appointment
                validation_error = self._validate_booking_data()
                if validation_error:
                    return {
                        'message': f"⚠️ {validation_error}\n\nPlease start over by providing your symptoms.",
                        'action': 'error',
                        'options': [
                            {'label': '🔄 Start Over', 'value': 'restart'}
                        ]
                    }

                # Create appointment
                appointment = self._create_appointment()

                if appointment:
                    return self._format_confirmation_response(appointment, include_email=True)
                else:
                    return {
                        'message': "⚠️ Sorry, there was an error creating your appointment. Please try again or start over.",
                        'action': 'error',
                        'options': [
                            {'label': '🔄 Try Again', 'value': 'retry'},
                            {'label': '↩️ Start Over', 'value': 'restart'}
                        ]
                    }
    
    def _handle_confirmation(self, message):
        """Handle post-booking actions"""
        message_lower = message.lower()

        if message_lower in ['new_booking', 'restart']:
            # Reset state
            self.state = {
                'stage': 'greeting',
                'conversation_history': [],
                'data': {},
                'timestamp': datetime.now().isoformat()
            }
            return {
                'message': "Sure! Let's start fresh. How can I help you book an appointment today?",
                'action': 'ask_symptoms',
                'options': None
            }
        elif message_lower == 'retry':
            # Retry appointment creation by going back to patient details
            self.state['stage'] = 'patient_details'
            # Clear patient info to re-collect
            if 'patient_email' in self.state['data']:
                del self.state['data']['patient_email']
            if 'patient_phone' in self.state['data']:
                del self.state['data']['patient_phone']
            if 'patient_name' in self.state['data']:
                del self.state['data']['patient_name']

            return {
                'message': "Let's try again. What's your full name?",
                'action': 'collect_name',
                'options': None
            }
        elif message_lower == 'done':
            return {
                'message': "Thank you for using our booking system! Have a great day! 😊",
                'action': 'end',
                'options': None
            }
        else:
            return {
                'message': "Thank you for using our booking system! Have a great day! 😊",
                'action': 'end',
                'options': None
            }
    
    def _default_response(self):
        """Default fallback response"""
        return {
            'message': "I'm sorry, I didn't understand that. Could you please rephrase?",
            'action': 'clarify',
            'options': None
        }

    def _handle_change_doctor(self, message, intent):
        """Handle doctor change request intelligently"""
        # Clear doctor, date and time if they were set
        if 'doctor_id' in self.state['data']:
            del self.state['data']['doctor_id']
        if 'doctor_name' in self.state['data']:
            del self.state['data']['doctor_name']
        if 'appointment_date' in self.state['data']:
            del self.state['data']['appointment_date']
        if 'appointment_time' in self.state['data']:
            del self.state['data']['appointment_time']

        # Go back to doctor selection
        self.state['stage'] = 'doctor_selection'

        # Get available doctors based on the original symptoms
        if 'suggested_specialization' in self.state['data']:
            doctors = Doctor.objects.filter(
                specialization__name=self.state['data']['suggested_specialization'],
                is_active=True
            )
        else:
            doctors = Doctor.objects.filter(is_active=True)

        return {
            'message': "Sure! Let me show you the available doctors again.\n\nPlease select a doctor:",
            'action': 'select_doctor',
            'options': self._get_doctor_options(doctors)
        }

    def _handle_change_date(self, message, intent):
        """Handle date change request intelligently"""
        # Clear time and date if they were set
        if 'appointment_time' in self.state['data']:
            del self.state['data']['appointment_time']
        if 'appointment_date' in self.state['data']:
            del self.state['data']['appointment_date']

        # Go back to date selection
        self.state['stage'] = 'date_selection'

        return {
            'message': "Sure! Let me help you select a different date.\n\nPlease choose a date:",
            'action': 'select_date',
            'options': self._get_date_options(self.state['data']['doctor_id'])
        }

    def _handle_change_time(self, message, intent):
        """Handle time change request intelligently"""
        # Clear the previously selected time
        if 'appointment_time' in self.state['data']:
            del self.state['data']['appointment_time']

        # Go back to time selection
        self.state['stage'] = 'time_selection'

        # Get available slots for the selected date
        date = datetime.strptime(self.state['data']['appointment_date'], '%Y-%m-%d').date()
        slots = self._get_available_slots(self.state['data']['doctor_id'], date)

        if slots:
            return {
                'message': f"Sure! Here are the available time slots for {date.strftime('%A, %B %d, %Y')}:",
                'action': 'select_time',
                'options': slots
            }
        else:
            # If no slots available, go back to date selection
            self.state['stage'] = 'date_selection'
            return {
                'message': f"Sorry, no time slots are available for {date.strftime('%A, %B %d, %Y')}. Please choose another date:",
                'action': 'select_date',
                'options': self._get_date_options(self.state['data']['doctor_id'], days=7)
            }

    def _handle_go_back(self, message, intent):
        """Handle go back request intelligently"""
        # Determine which stage to go back to
        stage_order = ['greeting', 'symptoms', 'doctor_selection', 'date_selection',
                      'time_selection', 'patient_details', 'confirmation']

        current_index = stage_order.index(self.state['stage'])
        if current_index > 0:
            previous_stage = stage_order[current_index - 1]
            self.state['stage'] = previous_stage

            # Clear data for stages after the previous stage
            if previous_stage == 'symptoms':
                # Clear doctor, date, time
                for key in ['doctor_id', 'doctor_name', 'appointment_date', 'appointment_time']:
                    if key in self.state['data']:
                        del self.state['data'][key]
            elif previous_stage == 'doctor_selection':
                # Clear date and time
                for key in ['appointment_date', 'appointment_time']:
                    if key in self.state['data']:
                        del self.state['data'][key]
            elif previous_stage == 'date_selection':
                # Clear time
                if 'appointment_time' in self.state['data']:
                    del self.state['data']['appointment_time']

            # Generate appropriate response based on previous stage
            if previous_stage == 'symptoms':
                return {
                    'message': "Sure! Let's go back.\n\nWhat symptoms are you experiencing?",
                    'action': 'ask_symptoms',
                    'options': None
                }
            elif previous_stage == 'doctor_selection':
                doctors = Doctor.objects.filter(
                    specialization__name=self.state['data'].get('suggested_specialization', 'General Physician'),
                    is_active=True
                )
                return {
                    'message': "Sure! Let's go back to doctor selection.\n\nPlease select a doctor:",
                    'action': 'select_doctor',
                    'options': self._get_doctor_options(doctors)
                }
            elif previous_stage == 'date_selection':
                return {
                    'message': "Sure! Let's go back to date selection.\n\nWhen would you like to schedule your appointment?",
                    'action': 'select_date',
                    'options': self._get_date_options(self.state['data']['doctor_id'])
                }

        return {
            'message': "I'm sorry, we're already at the beginning of the booking process.",
            'action': 'clarify',
            'options': None
        }

    def _handle_cancel(self, message):
        """Handle booking cancellation"""
        # Reset state
        self.state = {
            'stage': 'greeting',
            'conversation_history': self.state['conversation_history'],
            'data': {},
            'timestamp': datetime.now().isoformat()
        }

        return {
            'message': "No problem! I've cancelled this booking. If you'd like to book an appointment later, just let me know. How else can I help you?",
            'action': 'end',
            'options': [
                {'label': 'Start New Booking', 'value': 'new_booking'},
                {'label': 'End Chat', 'value': 'done'}
            ]
        }

    def _handle_clarification(self, message, intent):
        """Handle clarification requests intelligently"""
        # Re-present the current stage options
        stage = self.state['stage']

        if stage == 'doctor_selection':
            doctors = Doctor.objects.filter(is_active=True)
            return {
                'message': "Let me help you with that.\n\nHere are the available doctors:",
                'action': 'select_doctor',
                'options': self._get_doctor_options(doctors)
            }
        elif stage == 'date_selection':
            return {
                'message': "Let me help you with that.\n\nPlease select a date:",
                'action': 'select_date',
                'options': self._get_date_options(self.state['data']['doctor_id'])
            }
        elif stage == 'time_selection':
            date = datetime.strptime(self.state['data']['appointment_date'], '%Y-%m-%d').date()
            slots = self._get_available_slots(self.state['data']['doctor_id'], date)
            return {
                'message': f"Let me help you with that.\n\nHere are the available time slots for {date.strftime('%A, %B %d, %Y')}:",
                'action': 'select_time',
                'options': slots
            }
        else:
            return {
                'message': "I'm here to help! Could you please provide more details about what you need?",
                'action': 'clarify',
                'options': None
            }
    
    def _get_specialization_options(self):
        """Get all available specializations"""
        from doctors.models import Specialization
        specs = Specialization.objects.all()
        return [
            {'label': spec.name, 'value': str(spec.id), 'description': spec.description}
            for spec in specs
        ]
    
    def _get_doctor_options(self, doctors):
        """Format doctors as options"""
        return [
            {
                'label': f"Dr. {doctor.name}",
                'value': str(doctor.id),
                'description': f"{doctor.specialization.name} - {doctor.experience_years} years exp."
            }
            for doctor in doctors
        ]
    
    def _get_alternative_doctors(self):
        """Get general physicians as alternative"""
        doctors = Doctor.objects.filter(
            specialization__name='General Physician',
            is_active=True
        )
        return self._get_doctor_options(doctors)
    
    def _get_date_options(self, doctor_id, days=7):
        """Get next available dates (default 7 days for more flexibility)"""
        today = datetime.now().date()
        dates = []
        
        for i in range(days):
            date = today + timedelta(days=i)
            dates.append({
                'label': date.strftime('%A, %B %d, %Y'),
                'value': date.strftime('%Y-%m-%d')
            })
        
        return dates
    
    def _get_available_slots(self, doctor_id, date, show_all=True):
        """Get available time slots for a doctor on a specific date

        Args:
            doctor_id: ID of the doctor
            date: Date object for the appointment
            show_all: If True, shows all slots (available and booked). If False, shows only available slots.

        Returns:
            List of slot dictionaries with 'label', 'value', 'available', and 'description' fields
        """
        # Get doctor schedule for this day
        schedules = DoctorSchedule.objects.filter(
            doctor_id=doctor_id,
            day_of_week=date.weekday(),
            is_active=True
        )

        if not schedules.exists():
            return []

        schedule = schedules.first()

        # Get booked appointments with patient info
        booked_appointments = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=date,
            status__in=['pending', 'confirmed']
        ).values('appointment_time', 'patient_name', 'patient_phone')

        # Create a dictionary of booked times for quick lookup
        booked_times = {apt['appointment_time']: apt for apt in booked_appointments}

        # Generate time slots
        slots = []
        available_slots = []
        booked_slots = []

        current_time = datetime.combine(date, schedule.start_time)
        end_time = datetime.combine(date, schedule.end_time)

        while current_time < end_time:
            time_str = current_time.strftime('%H:%M')
            time_obj = current_time.time()

            # Check if slot is booked
            is_booked = time_obj in booked_times

            slot_info = {
                'label': current_time.strftime('%I:%M %p'),
                'value': time_str,
                'available': not is_booked
            }

            if is_booked:
                # Slot is booked - add description
                slot_info['description'] = '❌ Booked'
                booked_slots.append(slot_info)
            else:
                # Slot is available
                slot_info['description'] = '✅ Available'
                available_slots.append(slot_info)

            # Add to appropriate list
            if show_all:
                slots.append(slot_info)
            elif not is_booked:
                slots.append(slot_info)

            current_time += timedelta(minutes=schedule.slot_duration)

        # Return available slots first, then booked slots (for better UX)
        if show_all:
            return available_slots + booked_slots
        else:
            return available_slots

    def _check_existing_appointments(self):
        """Check if patient has any upcoming appointments based on phone number from WhatsApp session"""
        try:
            # Get the phone number from the WhatsApp session
            from whatsapp_integration.models import WhatsAppSession

            # Find the session associated with this conversation
            session = WhatsAppSession.objects.filter(
                session_id=self.session_id,
                is_active=True
            ).first()

            if not session:
                return None

            patient_phone = session.phone_number

            # Look for upcoming appointments for this phone number
            today = datetime.now().date()
            upcoming_appointments = Appointment.objects.filter(
                patient_phone=patient_phone,
                appointment_date__gte=today,
                status__in=['pending', 'confirmed']
            ).order_by('appointment_date', 'appointment_time')

            # Return the nearest upcoming appointment
            if upcoming_appointments.exists():
                return upcoming_appointments.first()

            return None

        except Exception as e:
            print(f"Error checking existing appointments: {str(e)}")
            return None

    def _validate_appointment_timing(self, appointment, action='cancel', minimum_hours=2):
        """
        Validate if an appointment can be cancelled or rescheduled based on timing.

        Args:
            appointment: Appointment object
            action: 'cancel' or 'reschedule'
            minimum_hours: Minimum hours before appointment required for the action

        Returns:
            dict with 'valid' (bool) and 'message' (str) keys
        """
        try:
            from datetime import datetime as dt

            # Combine appointment date and time
            appointment_datetime = dt.combine(
                appointment.appointment_date,
                appointment.appointment_time
            )

            # Get current time
            now = dt.now()

            # Calculate time difference
            time_until_appointment = appointment_datetime - now
            hours_until_appointment = time_until_appointment.total_seconds() / 3600

            # Check if appointment is in the past
            if hours_until_appointment < 0:
                return {
                    'valid': False,
                    'message': f"⚠️ Cannot {action} an appointment that has already passed."
                }

            # Check minimum notice period
            if hours_until_appointment < minimum_hours:
                return {
                    'valid': False,
                    'message': f"⚠️ Sorry, appointments must be {action}led at least {minimum_hours} hours in advance.\n\nYour appointment is in {hours_until_appointment:.1f} hours.\n\nPlease contact the clinic directly for last-minute changes."
                }

            return {
                'valid': True,
                'message': ''
            }

        except Exception as e:
            print(f"Error validating appointment timing: {str(e)}")
            return {
                'valid': True,  # Allow the action if validation fails
                'message': ''
            }

    def _validate_booking_data(self):
        """Validate all required booking data is present and valid"""
        data = self.state['data']

        # Check required fields
        required_fields = {
            'doctor_id': 'Doctor selection',
            'patient_name': 'Patient name',
            'patient_phone': 'Phone number',
            'appointment_date': 'Appointment date',
            'appointment_time': 'Appointment time'
        }

        for field, label in required_fields.items():
            if field not in data or not data[field]:
                return f"Missing {label}. Please complete all required information."

        # Validate date is in the future
        try:
            from datetime import datetime
            apt_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
            if apt_date < datetime.now().date():
                return "Appointment date must be in the future."
        except ValueError:
            return "Invalid appointment date format."

        return None  # No errors

    def _format_confirmation_response(self, appointment, include_email=False):
        """Format consistent confirmation response"""
        try:
            from datetime import datetime

            # Safely parse date and time
            apt_date = datetime.strptime(str(appointment.appointment_date), '%Y-%m-%d')

            # Handle both HH:MM:SS and HH:MM formats
            time_str = str(appointment.appointment_time)
            if len(time_str) == 8:  # HH:MM:SS
                apt_time = datetime.strptime(time_str, '%H:%M:%S')
            else:  # HH:MM
                apt_time = datetime.strptime(time_str, '%H:%M')

            # Build confirmation message
            message = f"""✅ Appointment Confirmed Successfully!

📋 Booking ID: {appointment.booking_id}
👨‍⚕️ Doctor: Dr. {appointment.doctor.name}
📅 Date: {apt_date.strftime('%A, %B %d, %Y')}
⏰ Time: {apt_time.strftime('%I:%M %p')}
👤 Patient: {appointment.patient_name}
📞 Phone: {appointment.patient_phone}"""

            if include_email and appointment.patient_email:
                message += f"\n✉️ Email: {appointment.patient_email}"

            message += """

✨ Please arrive 10 minutes early for your appointment.
📱 You'll receive a confirmation SMS shortly.

Is there anything else I can help you with?"""

            return {
                'message': message,
                'action': 'booking_complete',
                'options': [
                    {'label': '📅 Book Another Appointment', 'value': 'new_booking'},
                    {'label': '✅ Done', 'value': 'done'}
                ],
                'booking_id': appointment.booking_id
            }
        except Exception as e:
            print(f"Error formatting confirmation: {str(e)}")
            # Fallback to basic confirmation
            return {
                'message': f"✅ Appointment Confirmed!\n\n📋 Booking ID: {appointment.booking_id}\n\nYour appointment has been successfully booked.",
                'action': 'booking_complete',
                'options': [
                    {'label': '📅 Book Another Appointment', 'value': 'new_booking'},
                    {'label': '✅ Done', 'value': 'done'}
                ],
                'booking_id': appointment.booking_id
            }

    def _create_appointment(self):
        """Create appointment from collected data"""
        try:
            data = self.state['data']

            # Debug: Check what data we have
            print(f"Creating appointment with data: {data}")

            # Validate required fields
            required_fields = ['doctor_id', 'patient_name', 'patient_phone',
                             'appointment_date', 'appointment_time']

            for field in required_fields:
                if field not in data:
                    print(f"ERROR: Missing required field: {field}")
                    return None

            # Get doctor info
            doctor = Doctor.objects.get(id=data['doctor_id'])

            # Create appointment
            appointment = Appointment.objects.create(
                doctor_id=data['doctor_id'],
                patient_name=data['patient_name'],
                patient_phone=data['patient_phone'],
                patient_email=data.get('patient_email', ''),
                appointment_date=data['appointment_date'],
                appointment_time=data['appointment_time'],
                symptoms=data.get('symptoms', 'Not specified'),
                status='confirmed',
                session_id=self.session_id
            )

            print(f"Appointment created successfully: {appointment.booking_id}")

            # Also save to PatientRecord table
            try:
                patient_record = PatientRecord.objects.create(
                    name=data['patient_name'],
                    phone_number=data['patient_phone'],
                    mail_id=data.get('patient_email', ''),
                    doctor_name=doctor.name,
                    department=doctor.specialization.name,
                    appointment_date=data['appointment_date']
                )
                print(f"Patient record created successfully: {patient_record.booking_id}")
            except Exception as pr_error:
                print(f"Warning: Failed to create patient record: {str(pr_error)}")
                # Don't fail the appointment creation if patient record fails

            return appointment

        except Exception as e:
            print(f"ERROR creating appointment: {str(e)}")
            import traceback
            traceback.print_exc()
            return None