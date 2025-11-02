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
        """Handle initial greeting with concise, direct responses"""
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
        """Handle time slot selection"""
        self.state['data']['appointment_time'] = message
        self.state['stage'] = 'patient_details'
        
        return {
            'message': f"Perfect! Your appointment is scheduled for {self.state['data']['appointment_date']} at {message}.\n\nNow, I need some details:\n\nWhat's your full name?",
            'action': 'collect_name',
            'options': None
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
    
    def _get_available_slots(self, doctor_id, date):
        """Get available time slots for a doctor on a specific date"""
        # Get doctor schedule for this day
        schedules = DoctorSchedule.objects.filter(
            doctor_id=doctor_id,
            day_of_week=date.weekday(),
            is_active=True
        )
        
        if not schedules.exists():
            return []
        
        schedule = schedules.first()
        
        # Get booked appointments
        booked_times = Appointment.objects.filter(
            doctor_id=doctor_id,
            appointment_date=date,
            status__in=['pending', 'confirmed']
        ).values_list('appointment_time', flat=True)
        
        # Generate time slots
        slots = []
        current_time = datetime.combine(date, schedule.start_time)
        end_time = datetime.combine(date, schedule.end_time)
        
        while current_time < end_time:
            time_str = current_time.strftime('%H:%M')
            
            # Check if slot is not booked
            if current_time.time() not in booked_times:
                slots.append({
                    'label': current_time.strftime('%I:%M %p'),
                    'value': time_str
                })
            
            current_time += timedelta(minutes=schedule.slot_duration)
        
        return slots

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