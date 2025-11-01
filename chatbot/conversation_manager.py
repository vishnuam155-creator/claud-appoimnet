from datetime import datetime, timedelta
from django.core.cache import cache
from doctors.models import Doctor, DoctorSchedule
from appointments.models import Appointment
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
            if intent['intent'] == 'change_doctor':
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
        """Handle initial greeting"""
        response_text = self.claude.generate_conversational_response(
            message,
            {'stage': 'greeting', 'conversation_history': self.state['conversation_history']}
        )
        
        # Check if user mentioned symptoms
        if any(word in message.lower() for word in ['pain', 'hurt', 'sick', 'fever', 'problem', 'issue']):
            self.state['stage'] = 'symptoms'
            return {
                'message': response_text + "\n\nCould you tell me more about your symptoms so I can help you find the right doctor?",
                'action': 'ask_symptoms',
                'options': None
            }
        
        self.state['stage'] = 'symptoms'
        return {
            'message': response_text + "\n\nHow can I help you today? You can:\n• Tell me about your symptoms\n• Choose a doctor specialization directly",
            'action': 'ask_symptoms',
            'options': self._get_specialization_options()
        }
    
    def _handle_symptoms(self, message):
        """Handle symptom analysis"""
        # Analyze symptoms using Claude
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
            
            response_text = f"Based on your symptoms, I recommend seeing a {analysis['specialization']}. "
            response_text += f"\n\n{analysis['reasoning']}\n\nHere are our available doctors:"
            
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
            # Extract name
            data['patient_name'] = message
            return {
                'message': f"Thank you, {message}! What's your phone number?",
                'action': 'collect_phone',
                'options': None
            }
        elif 'patient_phone' not in data:
            # Extract phone
            data['patient_phone'] = message
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
                
                # Create appointment
                appointment = self._create_appointment()
                
                if appointment:
                    # Format the date properly
                    from datetime import datetime
                    apt_date = datetime.strptime(str(appointment.appointment_date), '%Y-%m-%d')
                    apt_time = datetime.strptime(str(appointment.appointment_time), '%H:%M:%S' if len(str(appointment.appointment_time)) > 5 else '%H:%M')
                    
                    return {
                        'message': f"""✅ Appointment Confirmed!

📋 Booking ID: {appointment.booking_id}
👨‍⚕️ Doctor: Dr. {appointment.doctor.name}
📅 Date: {apt_date.strftime('%A, %B %d, %Y')}
⏰ Time: {apt_time.strftime('%I:%M %p')}
👤 Patient: {appointment.patient_name}
📞 Phone: {appointment.patient_phone}

Please arrive 10 minutes early. You'll receive a confirmation SMS shortly.

Is there anything else I can help you with?""",
                        'action': 'booking_complete',
                        'options': [
                            {'label': '📅 Book Another Appointment', 'value': 'new_booking'},
                            {'label': '✅ Done', 'value': 'done'}
                        ],
                        'booking_id': appointment.booking_id
                    }
                else:
                    return {
                        'message': "Sorry, there was an error creating your appointment. Please try again.",
                        'action': 'error',
                        'options': None
                    }
            elif message == 'enter_email':
                # User wants to enter email
                return {
                    'message': "Please type your email address:",
                    'action': 'collect_email_text',
                    'options': None
                }
            else:
                # User typed an email directly
                data['patient_email'] = message
                self.state['stage'] = 'confirmation'
                
                # Create appointment
                appointment = self._create_appointment()
                
                if appointment:
                    # Format the date properly
                    from datetime import datetime
                    apt_date = datetime.strptime(str(appointment.appointment_date), '%Y-%m-%d')
                    apt_time = datetime.strptime(str(appointment.appointment_time), '%H:%M:%S' if len(str(appointment.appointment_time)) > 5 else '%H:%M')
                    
                    return {
                        'message': f"""✅ Appointment Confirmed!

📋 Booking ID: {appointment.booking_id}
👨‍⚕️ Doctor: Dr. {appointment.doctor.name}
📅 Date: {apt_date.strftime('%A, %B %d, %Y')}
⏰ Time: {apt_time.strftime('%I:%M %p')}
👤 Patient: {appointment.patient_name}
📞 Phone: {appointment.patient_phone}
✉️ Email: {appointment.patient_email}

Please arrive 10 minutes early. You'll receive a confirmation SMS shortly.

Is there anything else I can help you with?""",
                        'action': 'booking_complete',
                        'options': [
                            {'label': '📅 Book Another Appointment', 'value': 'new_booking'},
                            {'label': '✅ Done', 'value': 'done'}
                        ],
                        'booking_id': appointment.booking_id
                    }
                else:
                    return {
                        'message': "Sorry, there was an error creating your appointment. Please try again.",
                        'action': 'error',
                        'options': None
                    }
    
    def _handle_confirmation(self, message):
        """Handle post-booking actions"""
        if message.lower() == 'new_booking':
            # Reset state
            self.state = {
                'stage': 'greeting',
                'conversation_history': [],
                'data': {},
                'timestamp': datetime.now().isoformat()
            }
            return {
                'message': "Sure! Let's book another appointment. How can I help you?",
                'action': 'ask_symptoms',
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
        response_text = self.claude.generate_contextual_response(
            message, intent, self.state['stage'], self.state['data']
        )

        # Clear date and time if they were set
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
            'message': response_text + "\n\nHere are the available doctors again:",
            'action': 'select_doctor',
            'options': self._get_doctor_options(doctors)
        }

    def _handle_change_date(self, message, intent):
        """Handle date change request intelligently"""
        response_text = self.claude.generate_contextual_response(
            message, intent, self.state['stage'], self.state['data']
        )

        # Clear time if it was set
        if 'appointment_time' in self.state['data']:
            del self.state['data']['appointment_time']

        # Go back to date selection
        self.state['stage'] = 'date_selection'

        return {
            'message': response_text + "\n\nPlease select a new date:",
            'action': 'select_date',
            'options': self._get_date_options(self.state['data']['doctor_id'])
        }

    def _handle_change_time(self, message, intent):
        """Handle time change request intelligently"""
        response_text = self.claude.generate_contextual_response(
            message, intent, self.state['stage'], self.state['data']
        )

        # Go back to time selection
        self.state['stage'] = 'time_selection'

        # Get available slots for the selected date
        date = datetime.strptime(self.state['data']['appointment_date'], '%Y-%m-%d').date()
        slots = self._get_available_slots(self.state['data']['doctor_id'], date)

        return {
            'message': response_text + "\n\nHere are the available time slots:",
            'action': 'select_time',
            'options': slots
        }

    def _handle_go_back(self, message, intent):
        """Handle go back request intelligently"""
        response_text = self.claude.generate_contextual_response(
            message, intent, self.state['stage'], self.state['data']
        )

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
                    'message': response_text + "\n\nWhat symptoms are you experiencing?",
                    'action': 'ask_symptoms',
                    'options': None
                }
            elif previous_stage == 'doctor_selection':
                doctors = Doctor.objects.filter(
                    specialization__name=self.state['data'].get('suggested_specialization', 'General Physician'),
                    is_active=True
                )
                return {
                    'message': response_text + "\n\nPlease select a doctor:",
                    'action': 'select_doctor',
                    'options': self._get_doctor_options(doctors)
                }
            elif previous_stage == 'date_selection':
                return {
                    'message': response_text + "\n\nWhen would you like to schedule your appointment?",
                    'action': 'select_date',
                    'options': self._get_date_options(self.state['data']['doctor_id'])
                }

        return {
            'message': response_text,
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
        response_text = self.claude.generate_contextual_response(
            message, intent, self.state['stage'], self.state['data']
        )

        # Re-present the current stage options
        stage = self.state['stage']

        if stage == 'doctor_selection':
            doctors = Doctor.objects.filter(is_active=True)
            return {
                'message': response_text + "\n\nHere are the available doctors:",
                'action': 'select_doctor',
                'options': self._get_doctor_options(doctors)
            }
        elif stage == 'date_selection':
            return {
                'message': response_text + "\n\nPlease select a date:",
                'action': 'select_date',
                'options': self._get_date_options(self.state['data']['doctor_id'])
            }
        elif stage == 'time_selection':
            date = datetime.strptime(self.state['data']['appointment_date'], '%Y-%m-%d').date()
            slots = self._get_available_slots(self.state['data']['doctor_id'], date)
            return {
                'message': response_text + "\n\nHere are the available time slots:",
                'action': 'select_time',
                'options': slots
            }
        else:
            return {
                'message': response_text,
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
            return appointment
            
        except Exception as e:
            print(f"ERROR creating appointment: {str(e)}")
            import traceback
            traceback.print_exc()
            return None