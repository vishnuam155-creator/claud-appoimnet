"""
Voice Assistant Manager - Natural Conversational Flow
Handles pure voice-based appointment booking without UI elements
"""

import json
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from difflib import SequenceMatcher

from doctors.models import Doctor, DoctorSchedule, Specialization
from appointments.models import Appointment
from chatbot.claude_service import ClaudeService
from chatbot.date_parser import DateParser


class VoiceAssistantManager:
    """
    Manages voice-only conversation flow for appointment booking
    No UI elements, purely conversational responses
    """

    ASSISTANT_NAME = "MediBot"

    # Conversation stages
    STAGES = {
        'greeting': 'greeting',
        'patient_name': 'patient_name',
        'doctor_selection': 'doctor_selection',
        'date_selection': 'date_selection',
        'time_selection': 'time_selection',
        'phone_collection': 'phone_collection',
        'confirmation': 'confirmation',
        'completed': 'completed'
    }

    def __init__(self, session_id):
        self.session_id = session_id
        self.claude_service = ClaudeService()
        self.date_parser = DateParser()

    def process_voice_message(self, message, session_data):
        """
        Process voice input and return voice-optimized response

        Args:
            message: User's voice input (transcribed text)
            session_data: Current session state

        Returns:
            dict: {
                'message': str - Voice response text,
                'stage': str - Current conversation stage,
                'data': dict - Updated session data,
                'action': str - Special action if any
            }
        """
        current_stage = session_data.get('stage', 'greeting')

        # Route to appropriate stage handler
        handlers = {
            'greeting': self._handle_greeting,
            'patient_name': self._handle_patient_name,
            'doctor_selection': self._handle_doctor_selection_voice,
            'date_selection': self._handle_date_selection_voice,
            'time_selection': self._handle_time_selection_voice,
            'phone_collection': self._handle_phone_collection,
            'confirmation': self._handle_confirmation_voice,
        }

        handler = handlers.get(current_stage, self._handle_greeting)
        return handler(message, session_data)

    def _handle_greeting(self, message, session_data):
        """Initial greeting and ask for patient name"""

        # Check if user already provided their name in first message
        if message and len(message.strip()) > 2:
            # Try to extract name from message
            name_match = re.search(r'(?:my name is|i am|i\'m|this is)\s+([a-zA-Z\s]+)', message.lower())
            if name_match:
                patient_name = name_match.group(1).strip().title()
                session_data['patient_name'] = patient_name
                session_data['stage'] = 'doctor_selection'

                return {
                    'message': f"Hello {patient_name}! Nice to meet you. I'm {self.ASSISTANT_NAME}, your voice assistant. I'm here to help you book a medical appointment. Could you tell me which doctor you'd like to see, or describe your symptoms and I'll suggest the right doctor for you?",
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }

        # Standard greeting
        session_data['stage'] = 'patient_name'
        return {
            'message': f"Hello! I'm {self.ASSISTANT_NAME}, your voice medical assistant. I'm here to help you book an appointment. May I know your name please?",
            'stage': 'patient_name',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_patient_name(self, message, session_data):
        """Collect patient name and move to doctor selection"""

        if not message or len(message.strip()) < 2:
            return {
                'message': "I didn't quite catch that. Could you please tell me your name?",
                'stage': 'patient_name',
                'data': session_data,
                'action': 'continue'
            }

        # Extract name from message
        name = message.strip()

        # Remove common prefixes
        name = re.sub(r'^(?:my name is|i am|i\'m|this is)\s+', '', name, flags=re.IGNORECASE).strip()

        # Capitalize properly
        patient_name = ' '.join(word.capitalize() for word in name.split())

        session_data['patient_name'] = patient_name
        session_data['stage'] = 'doctor_selection'

        return {
            'message': f"Great to meet you, {patient_name}! Now, which doctor would you like to book an appointment with? You can tell me the doctor's name, or describe your symptoms and I'll suggest the best doctor for you.",
            'stage': 'doctor_selection',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_doctor_selection_voice(self, message, session_data):
        """Handle doctor selection via voice - name or symptoms"""

        if not message:
            return {
                'message': "I didn't hear anything. Could you please tell me which doctor you'd like to see, or describe your symptoms?",
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }

        # First, try to match doctor by name
        doctor = self._find_doctor_by_name(message)

        if doctor:
            session_data['doctor_id'] = doctor.id
            session_data['doctor_name'] = doctor.full_name
            session_data['stage'] = 'date_selection'

            return {
                'message': f"Perfect! I found Dr. {doctor.full_name}, {doctor.specialization.name}. What date would you like to book? You can say something like 'tomorrow', 'next Monday', or a specific date.",
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        # If no doctor found by name, analyze as symptoms
        return self._analyze_symptoms_and_suggest(message, session_data)

    def _analyze_symptoms_and_suggest(self, message, session_data):
        """Analyze symptoms using AI and suggest doctor"""

        try:
            # Use Claude/Gemini to analyze symptoms
            analysis = self.claude_service.analyze_symptoms(message)
            specialization_name = analysis.get('specialization', '').lower()

            if not specialization_name:
                return {
                    'message': "I understand you're not feeling well, but I couldn't quite determine the right specialization. Could you describe your symptoms in more detail? For example, 'I have a fever and cough' or 'I have stomach pain'.",
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }

            # Find matching specialization
            specialization = Specialization.objects.filter(
                name__icontains=specialization_name
            ).first()

            if not specialization:
                # Try keyword match
                all_specs = Specialization.objects.all()
                for spec in all_specs:
                    keywords = spec.keywords.lower() if spec.keywords else ""
                    if any(keyword in message.lower() for keyword in keywords.split(',')):
                        specialization = spec
                        break

            if not specialization:
                return {
                    'message': "I'm having trouble matching your symptoms to a specialization. Could you tell me which type of doctor you need? For example, 'general physician', 'cardiologist', 'dermatologist', etc.",
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }

            # Get available doctors for this specialization
            doctors = Doctor.objects.filter(
                specialization=specialization,
                is_available=True
            ).order_by('consultation_fee')

            if not doctors.exists():
                return {
                    'message': f"I'm sorry, we don't have any {specialization.name} doctors available right now. Would you like to try a different specialization?",
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }

            # Suggest first available doctor
            suggested_doctor = doctors.first()

            session_data['suggested_doctors'] = [
                {'id': doc.id, 'name': doc.full_name} for doc in doctors
            ]
            session_data['stage'] = 'doctor_selection'  # Keep in same stage for confirmation

            # Create natural response
            if doctors.count() == 1:
                message_text = f"Based on your symptoms, I recommend Dr. {suggested_doctor.full_name}, our {specialization.name}. They charge {suggested_doctor.consultation_fee} rupees per consultation. Would you like to book with Dr. {suggested_doctor.full_name}? Just say 'yes' or tell me if you'd prefer a different doctor."
            else:
                other_doctors = ", ".join([f"Dr. {doc.full_name}" for doc in doctors[1:3]])
                message_text = f"Based on your symptoms, I recommend Dr. {suggested_doctor.full_name}, our {specialization.name}. They charge {suggested_doctor.consultation_fee} rupees per consultation. We also have {other_doctors}. Which doctor would you like to book with?"

            return {
                'message': message_text,
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }

        except Exception as e:
            print(f"Error analyzing symptoms: {e}")
            return {
                'message': "I'm having trouble analyzing your symptoms. Could you tell me which doctor you'd like to see by name?",
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }

    def _find_doctor_by_name(self, message):
        """
        Intelligent doctor name matching from voice input
        Handles variations, prefixes, and fuzzy matching
        """

        # Clean the message
        cleaned = message.lower().strip()

        # Remove common prefixes
        cleaned = re.sub(r'^(?:doctor|dr\.?|i want|i need|book)\s+', '', cleaned)

        # Get all available doctors
        doctors = Doctor.objects.filter(is_available=True)

        best_match = None
        best_score = 0

        for doctor in doctors:
            score = 0
            doctor_name_lower = doctor.full_name.lower()
            first_name = doctor.first_name.lower()
            last_name = doctor.last_name.lower()

            # Exact full name match
            if cleaned == doctor_name_lower:
                score = 100

            # Exact first or last name match
            elif cleaned == first_name or cleaned == last_name:
                score = 95

            # Full name appears in message
            elif doctor_name_lower in cleaned or cleaned in doctor_name_lower:
                score = 90

            # First or last name appears in message
            elif first_name in cleaned or last_name in cleaned:
                score = 85

            # Fuzzy matching using SequenceMatcher
            else:
                similarity = SequenceMatcher(None, cleaned, doctor_name_lower).ratio()
                if similarity >= 0.7:  # 70% similarity threshold
                    score = int(similarity * 80)

            if score > best_score:
                best_score = score
                best_match = doctor

        # Return match if score is good enough
        if best_score >= 70:
            return best_match

        return None

    def _handle_date_selection_voice(self, message, session_data):
        """Handle date selection via voice"""

        if not message:
            return {
                'message': "I didn't catch that. What date would you like? You can say 'tomorrow', 'next Monday', or a specific date.",
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Parse date from natural language
        parsed_date = self.date_parser.parse_date(message)

        if not parsed_date:
            return {
                'message': "I couldn't understand that date. Could you try again? For example, say 'tomorrow', 'December 15', or 'next Friday'.",
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Validate date
        today = timezone.now().date()

        if parsed_date < today:
            return {
                'message': "That date is in the past. Please choose a date from today onwards.",
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        if parsed_date > today + timedelta(days=90):
            return {
                'message': "We can only book appointments up to 90 days in advance. Please choose an earlier date.",
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Check if doctor has availability on this date
        doctor_id = session_data.get('doctor_id')
        available_slots = self._get_available_slots(doctor_id, parsed_date)

        if not available_slots:
            # Suggest next available date
            next_available = self._find_next_available_date(doctor_id, parsed_date)
            if next_available:
                return {
                    'message': f"I'm sorry, the doctor is not available on {parsed_date.strftime('%B %d, %Y')}. The next available date is {next_available.strftime('%B %d, %Y')}. Would you like to book on that date instead?",
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }
            else:
                return {
                    'message': "The doctor doesn't have any availability in the next few weeks. Would you like to try a different doctor or a different date?",
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }

        session_data['appointment_date'] = parsed_date.isoformat()
        session_data['available_slots'] = available_slots
        session_data['stage'] = 'time_selection'

        # Format slots for voice
        time_options = self._format_time_slots_for_voice(available_slots)

        return {
            'message': f"Great! {parsed_date.strftime('%B %d, %Y')} works. The doctor has the following time slots available: {time_options}. Which time works best for you?",
            'stage': 'time_selection',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_time_selection_voice(self, message, session_data):
        """Handle time slot selection via voice"""

        if not message:
            return {
                'message': "I didn't catch that. What time would you like? You can say something like '10 AM' or '2:30 PM'.",
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Extract time from message
        selected_time = self._parse_time_from_voice(message)

        if not selected_time:
            return {
                'message': "I couldn't understand that time. Could you say it again? For example, '10 AM' or '2:30 PM'.",
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Check if time is available
        available_slots = session_data.get('available_slots', [])

        # Find matching slot
        matched_slot = None
        for slot in available_slots:
            slot_time = slot['time']
            # Compare with selected time
            if slot_time.startswith(selected_time) or selected_time in slot_time:
                if slot['available']:
                    matched_slot = slot
                    break

        if not matched_slot:
            # Check if time exists but is booked
            booked_slot = None
            for slot in available_slots:
                if slot['time'].startswith(selected_time) or selected_time in slot['time']:
                    booked_slot = slot
                    break

            if booked_slot and not booked_slot['available']:
                # Suggest alternative
                alt_slots = [s for s in available_slots if s['available']][:3]
                if alt_slots:
                    alt_times = ", ".join([s['time'] for s in alt_slots])
                    return {
                        'message': f"I'm sorry, {selected_time} is already booked. Here are some available times: {alt_times}. Which one works for you?",
                        'stage': 'time_selection',
                        'data': session_data,
                        'action': 'continue'
                    }

            return {
                'message': "That time slot isn't available. Let me tell you the available times again. " + self._format_time_slots_for_voice(available_slots) + ". Which time would you like?",
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        session_data['appointment_time'] = matched_slot['time']
        session_data['stage'] = 'phone_collection'

        return {
            'message': f"Perfect! I've reserved {matched_slot['time']} for you. Now, what's your phone number so we can send you a confirmation?",
            'stage': 'phone_collection',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_phone_collection(self, message, session_data):
        """Collect phone number"""

        if not message:
            return {
                'message': "I didn't catch your phone number. Could you say it again?",
                'stage': 'phone_collection',
                'data': session_data,
                'action': 'continue'
            }

        # Extract phone number from message
        phone = self._extract_phone_number(message)

        if not phone:
            return {
                'message': "I couldn't understand that phone number. Please say your 10-digit mobile number clearly.",
                'stage': 'phone_collection',
                'data': session_data,
                'action': 'continue'
            }

        # Validate phone
        if len(phone) != 10 or not phone.isdigit():
            return {
                'message': "That doesn't seem like a valid 10-digit phone number. Could you say it again?",
                'stage': 'phone_collection',
                'data': session_data,
                'action': 'continue'
            }

        session_data['phone'] = phone
        session_data['stage'] = 'confirmation'

        # Prepare summary
        doctor = Doctor.objects.get(id=session_data['doctor_id'])
        date_str = datetime.fromisoformat(session_data['appointment_date']).strftime('%B %d, %Y')

        summary = f"Great! Let me confirm your appointment details. Patient name: {session_data['patient_name']}. Doctor: Dr. {doctor.full_name}. Date: {date_str}. Time: {session_data['appointment_time']}. Phone number: {phone}. Is this correct? Say 'yes' to confirm or 'no' to make changes."

        return {
            'message': summary,
            'stage': 'confirmation',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_confirmation_voice(self, message, session_data):
        """Handle final confirmation and booking"""

        if not message:
            return {
                'message': "I didn't hear you. Please say 'yes' to confirm the booking or 'no' to make changes.",
                'stage': 'confirmation',
                'data': session_data,
                'action': 'continue'
            }

        message_lower = message.lower().strip()

        # Check for confirmation
        if any(word in message_lower for word in ['yes', 'correct', 'confirm', 'book', 'ok', 'okay', 'sure']):
            # Create appointment
            try:
                appointment = self._create_appointment(session_data)

                if appointment:
                    session_data['stage'] = 'completed'
                    session_data['appointment_id'] = appointment.id

                    return {
                        'message': f"Perfect! Your appointment has been booked successfully. Your booking ID is {appointment.id}. You'll receive an SMS confirmation shortly at {session_data['phone']}. Is there anything else I can help you with?",
                        'stage': 'completed',
                        'data': session_data,
                        'action': 'booking_complete'
                    }
                else:
                    return {
                        'message': "I'm sorry, there was an error creating your appointment. Please try again or contact our support.",
                        'stage': 'confirmation',
                        'data': session_data,
                        'action': 'error'
                    }

            except Exception as e:
                print(f"Error creating appointment: {e}")
                return {
                    'message': "I'm sorry, something went wrong while booking your appointment. Please try again.",
                    'stage': 'confirmation',
                    'data': session_data,
                    'action': 'error'
                }

        # Check for changes/corrections
        elif any(word in message_lower for word in ['no', 'change', 'wrong', 'different', 'modify']):
            return {
                'message': "No problem! What would you like to change? You can say 'change doctor', 'change date', 'change time', or 'change phone number'.",
                'stage': 'confirmation',
                'data': session_data,
                'action': 'continue'
            }

        else:
            return {
                'message': "I didn't quite understand. Please say 'yes' to confirm the booking or tell me what you'd like to change.",
                'stage': 'confirmation',
                'data': session_data,
                'action': 'continue'
            }

    # Helper methods

    def _get_available_slots(self, doctor_id, date):
        """Get available time slots for doctor on specific date"""

        try:
            doctor = Doctor.objects.get(id=doctor_id)
            weekday = date.strftime('%A')

            # Get doctor's schedule for this weekday
            schedules = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=weekday
            )

            if not schedules.exists():
                return []

            # Get existing appointments for this date
            existing_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                status__in=['pending', 'confirmed']
            ).values_list('appointment_time', flat=True)

            booked_times = [time.strftime('%I:%M %p') for time in existing_appointments]

            # Generate slots
            all_slots = []
            for schedule in schedules:
                slots = self._generate_time_slots(schedule, booked_times)
                all_slots.extend(slots)

            return all_slots

        except Exception as e:
            print(f"Error getting slots: {e}")
            return []

    def _generate_time_slots(self, schedule, booked_times):
        """Generate time slots from schedule"""

        slots = []
        current_time = datetime.combine(datetime.today(), schedule.start_time)
        end_time = datetime.combine(datetime.today(), schedule.end_time)

        while current_time < end_time:
            time_str = current_time.strftime('%I:%M %p')
            is_available = time_str not in booked_times

            slots.append({
                'time': time_str,
                'available': is_available
            })

            current_time += timedelta(minutes=schedule.slot_duration)

        return slots

    def _find_next_available_date(self, doctor_id, start_date):
        """Find next available date for doctor"""

        current_date = start_date + timedelta(days=1)
        max_date = start_date + timedelta(days=30)

        while current_date <= max_date:
            slots = self._get_available_slots(doctor_id, current_date)
            if any(slot['available'] for slot in slots):
                return current_date
            current_date += timedelta(days=1)

        return None

    def _format_time_slots_for_voice(self, slots):
        """Format time slots for voice output"""

        available = [s['time'] for s in slots if s['available']][:5]  # First 5 slots

        if not available:
            return "Unfortunately, there are no available slots"

        if len(available) == 1:
            return available[0]
        elif len(available) == 2:
            return f"{available[0]} and {available[1]}"
        else:
            return ", ".join(available[:-1]) + f", and {available[-1]}"

    def _parse_time_from_voice(self, message):
        """Extract time from voice message"""

        # Patterns for time
        patterns = [
            r'(\d{1,2})\s*(?::|\.)\s*(\d{2})\s*(am|pm|a\.m\.|p\.m\.)',  # 10:30 AM
            r'(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)',  # 10 AM
            r'(\d{1,2})\s*(?::|\.)\s*(\d{2})',  # 10:30
        ]

        message_lower = message.lower().replace('.', '').replace(':', ' ')

        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = groups[1] if len(groups) > 2 and groups[1].isdigit() else '00'
                period = groups[-1] if len(groups) > 1 and groups[-1] in ['am', 'pm'] else None

                # Convert to 12-hour format
                if period:
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0

                return f"{hour:02d}:{minute}"

        return None

    def _extract_phone_number(self, message):
        """Extract phone number from message"""

        # Remove all non-digits
        digits = re.sub(r'\D', '', message)

        # Look for 10-digit number
        if len(digits) == 10:
            return digits

        # If longer, try to extract 10 digits
        if len(digits) > 10:
            # Try to find 10 consecutive digits
            match = re.search(r'(\d{10})', digits)
            if match:
                return match.group(1)

        return None

    def _create_appointment(self, session_data):
        """Create appointment in database"""

        try:
            doctor = Doctor.objects.get(id=session_data['doctor_id'])
            appointment_date = datetime.fromisoformat(session_data['appointment_date']).date()

            # Parse time
            time_str = session_data['appointment_time']
            appointment_time = datetime.strptime(time_str, '%I:%M %p').time()

            # Create appointment
            appointment = Appointment.objects.create(
                doctor=doctor,
                patient_name=session_data['patient_name'],
                patient_phone=session_data['phone'],
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='confirmed',
                booking_method='voice_assistant'
            )

            # Send SMS (if twilio is configured)
            try:
                from twilio_service import send_sms
                send_sms(
                    to=session_data['phone'],
                    message=f"Appointment confirmed with Dr. {doctor.full_name} on {appointment_date.strftime('%B %d, %Y')} at {time_str}. Booking ID: {appointment.id}"
                )
            except Exception as e:
                print(f"SMS sending failed: {e}")

            return appointment

        except Exception as e:
            print(f"Error creating appointment: {e}")
            return None
