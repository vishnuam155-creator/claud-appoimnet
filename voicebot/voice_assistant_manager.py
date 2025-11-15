"""
Voice Assistant Manager - AI-Powered Natural Conversational Flow
Enhanced with Gemini AI for superior accuracy and intelligence

This module handles the conversational flow for voice-based appointment booking,
following comprehensive personality and tone guidelines for natural, empathetic interactions.
"""

import json
import re
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from difflib import SequenceMatcher
import google.generativeai as genai
from django.conf import settings

from doctors.models import Doctor, DoctorSchedule, Specialization
from appointments.models import Appointment
from chatbot.claude_service import ClaudeService
from chatbot.date_parser import DateParser
from .voicebot_config import (
    CLINIC_NAME, PERSONALITY_GUIDELINES, VOICE_GUIDELINES,
    STAGE_PROMPTS, SPECIAL_SITUATIONS, INTENT_RESPONSES,
    AI_EXTRACTION_PROMPTS, get_greeting, format_phone_for_voice,
    get_confirmation_summary, get_booking_success_message
)


class VoiceAssistantManager:
    """
    AI-Powered Voice Assistant for Appointment Booking
    Uses Gemini AI for intelligent natural language understanding
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

        # Configure Gemini
        genai.configure(api_key=settings.ANTHROPIC_API_KEY)
        self.gemini_model = "gemini-2.5-flash"

    def process_voice_message(self, message, session_data):
        """
        Process voice input with AI intelligence and symptom change detection

        Args:
            message: User's voice input (transcribed text)
            session_data: Current session state

        Returns:
            dict: Response with message, stage, data, action
        """
        current_stage = session_data.get('stage', 'greeting')

        # Check for symptom changes after doctor selection
        if current_stage in ['date_selection', 'time_selection', 'phone_collection'] and message:
            if self._detect_symptom_change(message, current_stage):
                # User is mentioning new symptoms - offer to reconsider doctor
                return self._handle_mid_conversation_symptom_change(message, session_data)

        # Check if waiting for doctor reconfirmation after symptom change
        if session_data.get('awaiting_doctor_reconfirmation'):
            message_lower = message.lower()

            if any(keyword in message_lower for keyword in ['new doctor', 'different doctor', 'another doctor', 're-evaluate', 'find doctor', 'change doctor']):
                # User wants to find a new doctor based on symptoms
                session_data.pop('awaiting_doctor_reconfirmation', None)
                session_data.pop('doctor_id', None)
                session_data.pop('doctor_name', None)
                session_data['stage'] = 'doctor_selection'

                symptom_message = session_data.pop('new_symptoms', message)
                return self._analyze_symptoms_and_suggest_ai(symptom_message, session_data)

            elif any(keyword in message_lower for keyword in ['continue', 'current', 'same', 'yes', 'okay', 'ok', 'vishnu']):
                # User wants to continue with current doctor
                session_data.pop('awaiting_doctor_reconfirmation', None)
                session_data.pop('new_symptoms', None)

                return {
                    'message': f"Alright, let's continue with Dr. {session_data.get('doctor_name')}. What date would you prefer for your appointment?",
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }

        # Detect user intent using Gemini AI
        if message and current_stage != 'greeting':
            intent = self._detect_intent_with_ai(message, current_stage, session_data)

            # Handle special intents
            if intent.get('intent') == 'cancel':
                return self._handle_cancellation(session_data)
            elif intent.get('intent') == 'go_back':
                return self._handle_go_back(session_data)
            elif intent.get('intent') == 'correction':
                return self._handle_correction(intent, session_data)
            elif intent.get('intent') in ['change_doctor', 'change_date', 'change_time']:
                return self._handle_change_request(intent, session_data)

        # Route to appropriate stage handler
        handlers = {
            'greeting': self._handle_greeting,
            'patient_name': self._handle_patient_name_ai,
            'doctor_selection': self._handle_doctor_selection_ai,
            'date_selection': self._handle_date_selection_ai,
            'time_selection': self._handle_time_selection_ai,
            'phone_collection': self._handle_phone_collection_ai,
            'confirmation': self._handle_confirmation_ai,
        }

        handler = handlers.get(current_stage, self._handle_greeting)
        return handler(message, session_data)

    def _detect_intent_with_ai(self, message, stage, session_data):
        """Use Gemini AI to detect user intent"""
        return self.claude_service.detect_intent(message, stage, session_data)

    def _handle_greeting(self, message, session_data):
        """Initial greeting with AI intelligence - warm and welcoming"""

        # Check if user already provided their name using AI
        if message and len(message.strip()) > 2:
            name_extracted = self._extract_name_with_ai(message)
            if name_extracted:
                session_data['patient_name'] = name_extracted
                session_data['stage'] = 'doctor_selection'

                # Use Gemini AI to generate natural greeting with name
                greeting_msg = self._generate_ai_response(
                    context=f"Patient just introduced themselves. Their name is {name_extracted}.",
                    intent="Greet them warmly and ask how you can help with their appointment.",
                    fallback=f"Nice to meet you, {name_extracted}! How can I help you today? Do you have any symptoms you'd like to discuss, or do you know which doctor you'd like to see?"
                )

                return {
                    'message': greeting_msg,
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }

        # Standard greeting - use AI to generate natural welcome
        session_data['stage'] = 'patient_name'
        greeting_msg = self._generate_ai_response(
            context="New patient just connected for appointment booking.",
            intent="Give a warm welcome and ask for their name in a friendly, conversational way.",
            fallback=f"Hello! Welcome to {CLINIC_NAME}. I'm {self.ASSISTANT_NAME}, your AI assistant. I'm here to help you book an appointment. May I have your name, please?"
        )

        return {
            'message': greeting_msg,
            'stage': 'patient_name',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_patient_name_ai(self, message, session_data):
        """Collect patient name using AI extraction - warm and patient"""

        if not message or len(message.strip()) < 2:
            return {
                'message': STAGE_PROMPTS['patient_name']['retry'],
                'stage': 'patient_name',
                'data': session_data,
                'action': 'continue'
            }

        # Use AI to extract name
        patient_name = self._extract_name_with_ai(message)

        if not patient_name:
            return {
                'message': STAGE_PROMPTS['patient_name']['unclear'],
                'stage': 'patient_name',
                'data': session_data,
                'action': 'continue'
            }

        session_data['patient_name'] = patient_name
        session_data['stage'] = 'doctor_selection'

        # Personalized success message
        success_msg = STAGE_PROMPTS['patient_name']['success'].format(name=patient_name)
        ask_msg = STAGE_PROMPTS['doctor_selection']['ask']

        return {
            'message': f"{success_msg} {ask_msg}",
            'stage': 'doctor_selection',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_doctor_selection_ai(self, message, session_data):
        """Handle doctor selection with AI - name or symptoms - empathetic and helpful"""

        if not message:
            return {
                'message': STAGE_PROMPTS['doctor_selection']['retry'],
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Check if user is selecting from alternative doctors
        if session_data.get('alternative_doctors'):
            # User may say doctor name or number
            alternatives = session_data['alternative_doctors']
            message_lower = message.lower().strip()

            # Check for number selection (1, 2, etc.)
            if message_lower in ['1', 'one', 'first']:
                selected_doctor = alternatives[0]
            elif message_lower in ['2', 'two', 'second'] and len(alternatives) > 1:
                selected_doctor = alternatives[1]
            else:
                # Check for name match
                selected_doctor = None
                for alt in alternatives:
                    if alt['name'].lower() in message_lower or message_lower in alt['name'].lower():
                        selected_doctor = alt
                        break

            if selected_doctor:
                session_data['doctor_id'] = selected_doctor['id']
                session_data['doctor_name'] = selected_doctor['name']
                session_data['stage'] = 'date_selection'
                session_data.pop('alternative_doctors', None)

                # Parse ISO date string for formatting
                from datetime import datetime as dt
                next_date_formatted = dt.fromisoformat(selected_doctor['next_available']).strftime('%B %d, %Y')

                days_text = "tomorrow" if selected_doctor['days_away'] == 1 else f"in {selected_doctor['days_away']} days"

                return {
                    'message': f"Great choice! I'll book you with Dr. {selected_doctor['name']}. They have availability {days_text} on {next_date_formatted}. Would you like to book for that date, or would you prefer a different date?",
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }

        # Check if user is confirming a suggested doctor (from symptom analysis)
        if session_data.get('suggested_doctors'):
            # Try to confirm the suggested doctor
            confirmed_doctor = self._confirm_suggested_doctor(message, session_data)

            if confirmed_doctor:
                # Doctor confirmed, move to date selection
                session_data['doctor_id'] = confirmed_doctor.id
                session_data['doctor_name'] = confirmed_doctor.name
                session_data['stage'] = 'date_selection'
                session_data.pop('suggested_doctors', None)  # Clear suggestions

                # Use Gemini AI to generate a natural confirmation response
                try:
                    model = genai.GenerativeModel(self.gemini_model)
                    prompt = f"""Generate a natural, friendly confirmation message for a patient who just confirmed booking with {confirmed_doctor.name}.

Then ask about their preferred date for the appointment.

Keep it conversational and warm. Maximum 2 sentences.

Example: "Perfect! I'll book you with Dr. {confirmed_doctor.name}. What date works best for you? You can say tomorrow, a specific date, or a day of the week."
"""
                    response = model.generate_content(prompt)
                    ai_message = response.text.strip()
                except Exception as e:
                    print(f"AI response generation error: {e}")
                    ai_message = f"Perfect! I'll book you with Dr. {confirmed_doctor.name}. What date would work best for you? You can say tomorrow, a specific date, or a day of the week."

                return {
                    'message': ai_message,
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }

        # Use AI to determine if this is a doctor name or symptoms
        selection_type = self._classify_doctor_input(message)

        if selection_type == 'doctor_name':
            # Try to match doctor by name with AI enhancement
            doctor = self._find_doctor_by_name_ai(message)

            if doctor:
                session_data['doctor_id'] = doctor.id
                session_data['doctor_name'] = doctor.name
                session_data['stage'] = 'date_selection'

                doctor_found_msg = STAGE_PROMPTS['doctor_selection']['doctor_found'].format(
                    doctor_name=doctor.name,
                    specialization=doctor.specialization.name,
                    fee=doctor.consultation_fee
                )

                return {
                    'message': doctor_found_msg,
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }
            else:
                return {
                    'message': STAGE_PROMPTS['doctor_selection']['doctor_not_found'],
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }
        else:
            # Treat as symptoms and analyze with AI
            return self._analyze_symptoms_and_suggest_ai(message, session_data)

    def _analyze_symptoms_and_suggest_ai(self, message, session_data):
        """Analyze symptoms using Gemini AI and suggest doctor - with full context"""

        try:
            # Get all available specializations for context
            all_specializations = Specialization.objects.all()
            available_spec_names = [spec.name for spec in all_specializations]

            # Use Gemini to analyze symptoms
            analysis = self.claude_service.analyze_symptoms(message)
            specialization_name = analysis.get('specialization', '').lower()
            confidence = analysis.get('confidence', 'low')
            reasoning = analysis.get('reasoning', '')

            if not specialization_name or specialization_name == 'general physician':
                # If AI couldn't determine or defaulted to general physician
                # Try to find general physician first
                general_physician = Specialization.objects.filter(
                    name__icontains='general'
                ).first()

                if general_physician:
                    specialization_name = general_physician.name.lower()
                else:
                    # Provide available specializations
                    available_specs_text = ", ".join(available_spec_names)
                    return {
                        'message': STAGE_PROMPTS['doctor_selection']['symptoms_unclear'] + f" We have these specializations available: {available_specs_text}.",
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
                for spec in all_specializations:
                    keywords = spec.keywords.lower() if spec.keywords else ""
                    if any(keyword in message.lower() for keyword in keywords.split(',')):
                        specialization = spec
                        break

            if not specialization:
                # Specialization not found - show available ones
                available_specs_text = ", ".join(available_spec_names)
                error_msg = STAGE_PROMPTS['doctor_selection']['no_specialization_match'].format(
                    suggested_spec=specialization_name.title(),
                    available_specs=available_specs_text
                )
                return {
                    'message': error_msg,
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }

            # Get available doctors for this specialization
            doctors = Doctor.objects.filter(
                specialization=specialization,
                is_active=True
            ).order_by('consultation_fee')

            if not doctors.exists():
                return {
                    'message': f"I'm sorry, we don't have any {specialization.name} doctors available at the moment. Would you like to try booking with a different type of doctor?",
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }

            # Suggest doctor(s) with AI-generated response
            suggested_doctor = doctors.first()

            session_data['suggested_doctors'] = [
                {'id': doc.id, 'name': doc.name, 'fee': float(doc.consultation_fee) if doc.consultation_fee else 0}
                for doc in doctors[:3]
            ]
            session_data['suggested_specialization'] = specialization.name

            # Generate intelligent response
            if doctors.count() == 1:
                message_text = f"Based on your symptoms - {reasoning} - I recommend Dr. {suggested_doctor.name}, our {specialization.name}. The consultation fee is {suggested_doctor.consultation_fee} rupees. Would you like to book an appointment with Dr. {suggested_doctor.name}? Just say 'yes' or 'book it'."
            else:
                other_doctors = [f"Dr. {doc.name} for {doc.consultation_fee} rupees" for doc in doctors[1:3]]
                other_doctors_text = ", or ".join(other_doctors) if other_doctors else ""

                message_text = f"Based on your symptoms, I recommend seeing a {specialization.name}. I suggest Dr. {suggested_doctor.name} who charges {suggested_doctor.consultation_fee} rupees. "
                if other_doctors_text:
                    message_text += f"We also have {other_doctors_text}. "
                message_text += f"Which doctor would you like to book with? You can say the doctor's name."

            return {
                'message': message_text,
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }

        except Exception as e:
            print(f"Error analyzing symptoms with AI: {e}")

            # Get available specializations to help user
            try:
                all_specializations = Specialization.objects.all()
                available_spec_names = [spec.name for spec in all_specializations]
                available_specs_text = ", ".join(available_spec_names)

                error_msg = STAGE_PROMPTS['doctor_selection']['symptom_analysis_error'].format(
                    available_specs=available_specs_text
                )
            except Exception:
                error_msg = STAGE_PROMPTS['doctor_selection']['symptoms_unclear']

            return {
                'message': error_msg,
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }

    def _handle_date_selection_ai(self, message, session_data):
        """Handle date selection with AI parsing - flexible and understanding"""

        if not message:
            return {
                'message': STAGE_PROMPTS['date_selection']['retry'],
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Use AI to parse date from natural language
        parsed_date = self._parse_date_with_ai(message)

        if not parsed_date:
            return {
                'message': STAGE_PROMPTS['date_selection']['unclear'],
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Validate date
        today = timezone.now().date()

        if parsed_date < today:
            return {
                'message': STAGE_PROMPTS['date_selection']['date_passed'],
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        if parsed_date > today + timedelta(days=90):
            return {
                'message': STAGE_PROMPTS['date_selection']['too_far'],
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Check doctor availability
        doctor_id = session_data.get('doctor_id')

        # If no doctor_id yet (still in suggestion phase), try to confirm doctor first
        if not doctor_id and session_data.get('suggested_doctors'):
            # Check if message is confirming a doctor
            confirmed_doctor = self._confirm_suggested_doctor(message, session_data)
            if confirmed_doctor:
                session_data['doctor_id'] = confirmed_doctor.id
                session_data['doctor_name'] = confirmed_doctor.name
                doctor_id = confirmed_doctor.id
            else:
                return {
                    'message': STAGE_PROMPTS['date_selection']['no_doctor_selected'],
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }

        available_slots = self._get_available_slots(doctor_id, parsed_date)

        if not available_slots:
            # Try to find next available date (90 days search)
            next_available = self._find_next_available_date(doctor_id, parsed_date, max_days=90)

            if next_available:
                next_date_formatted = next_available.strftime('%B %d, %Y')
                current_date_formatted = parsed_date.strftime('%B %d, %Y')
                days_diff = (next_available - parsed_date).days

                no_slots_msg = f"I'm sorry, Dr. {session_data.get('doctor_name', 'the doctor')} doesn't have any available slots on {current_date_formatted}. "

                if days_diff <= 7:
                    no_slots_msg += f"However, I found availability on {next_date_formatted}, which is in {days_diff} days. "
                    no_slots_msg += "Would you like to book for that date instead? Just say 'yes' or 'book it'."
                else:
                    no_slots_msg += f"The next available date is {next_date_formatted}, which is in {days_diff} days. "
                    no_slots_msg += "Would you like to book for that date, or would you prefer to see a different doctor who might be available sooner?"

                # Store the suggested date for easy confirmation
                session_data['suggested_date'] = next_available.isoformat()

                return {
                    'message': no_slots_msg,
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }
            else:
                # No availability found in 90 days - suggest alternative doctors
                doctor_name = session_data.get('doctor_name', 'this doctor')

                try:
                    current_doctor = Doctor.objects.get(id=doctor_id)
                    specialization_name = current_doctor.specialization.name if current_doctor.specialization else "this specialty"

                    alternatives = self._get_alternative_doctors_with_availability(
                        doctor_id,
                        current_doctor.specialization_id if current_doctor.specialization else None,
                        parsed_date
                    )

                    if alternatives:
                        alt_msg = f"Unfortunately, Dr. {doctor_name} doesn't have any availability in the next 3 months. "
                        alt_msg += f"However, we have other excellent {specialization_name} doctors available:\n\n"

                        for idx, alt in enumerate(alternatives[:2], 1):
                            days_text = "tomorrow" if alt['days_away'] == 1 else f"in {alt['days_away']} days"
                            # Parse ISO date string for formatting
                            from datetime import datetime as dt
                            date_formatted = dt.fromisoformat(alt['next_available']).strftime('%B %d')
                            alt_msg += f"{idx}. Dr. {alt['name']} - Available {days_text} ({date_formatted}), "
                            alt_msg += f"consultation fee {alt['fee']} rupees\n"

                        alt_msg += "\nWhich doctor would you like to book with? You can say the doctor's name or the number."

                        # Store alternatives for easy selection (remove date objects for JSON serialization)
                        session_data['alternative_doctors'] = [
                            {k: v for k, v in alt.items() if k != 'next_available_date_obj'}
                            for alt in alternatives
                        ]
                        session_data['stage'] = 'doctor_selection'

                        return {
                            'message': alt_msg,
                            'stage': 'doctor_selection',
                            'data': session_data,
                            'action': 'continue'
                        }
                    else:
                        # No alternatives either
                        return {
                            'message': f"I apologize, but Dr. {doctor_name} and other {specialization_name} doctors are fully booked for the next few months. Would you like to consider a different type of specialist, or shall I help you with something else?",
                            'stage': 'doctor_selection',
                            'data': session_data,
                            'action': 'continue'
                        }
                except Exception as e:
                    print(f"Error finding alternatives: {e}")
                    return {
                        'message': STAGE_PROMPTS['date_selection']['no_availability'],
                        'stage': 'date_selection',
                        'data': session_data,
                        'action': 'continue'
                    }

        session_data['appointment_date'] = parsed_date.isoformat()
        session_data['available_slots'] = available_slots
        session_data['stage'] = 'time_selection'

        # Format slots for voice
        time_options = self._format_time_slots_for_voice(available_slots)
        date_formatted = parsed_date.strftime('%B %d, %Y')

        slots_msg = STAGE_PROMPTS['time_selection']['slots_shown'].format(
            date=date_formatted,
            time_slots=time_options
        )

        return {
            'message': slots_msg,
            'stage': 'time_selection',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_time_selection_ai(self, message, session_data):
        """Handle time slot selection with AI - clear and helpful"""

        if not message:
            return {
                'message': STAGE_PROMPTS['time_selection']['retry'],
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Use AI to extract time from message
        selected_time = self._extract_time_with_ai(message)

        if not selected_time:
            return {
                'message': STAGE_PROMPTS['time_selection']['unclear'],
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Check if time is available
        available_slots = session_data.get('available_slots', [])

        # Find matching slot with flexible matching
        matched_slot = self._match_time_slot(selected_time, available_slots)

        if not matched_slot:
            # Check if time exists but is booked
            booked_slot = None
            for slot in available_slots:
                if self._times_match(selected_time, slot['time']) and not slot['available']:
                    booked_slot = slot
                    break

            if booked_slot:
                # Suggest alternatives
                alt_slots = [s for s in available_slots if s['available']][:3]
                if alt_slots:
                    alt_times = ", ".join([s['time'] for s in alt_slots])
                    booked_msg = STAGE_PROMPTS['time_selection']['time_booked'].format(
                        time=selected_time,
                        alternatives=alt_times
                    )
                    return {
                        'message': booked_msg,
                        'stage': 'time_selection',
                        'data': session_data,
                        'action': 'continue'
                    }

            # Time not found in available slots
            time_slots_formatted = self._format_time_slots_for_voice(available_slots)
            not_available_msg = STAGE_PROMPTS['time_selection']['time_not_available'].format(
                time_slots=time_slots_formatted
            )
            return {
                'message': not_available_msg,
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        session_data['appointment_time'] = matched_slot['time']
        session_data['stage'] = 'phone_collection'

        success_msg = STAGE_PROMPTS['time_selection']['success'].format(
            time=matched_slot['time']
        )

        return {
            'message': success_msg,
            'stage': 'phone_collection',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_phone_collection_ai(self, message, session_data):
        """Collect phone number with AI extraction - clear and reassuring"""

        if not message:
            return {
                'message': STAGE_PROMPTS['phone_collection']['retry'],
                'stage': 'phone_collection',
                'data': session_data,
                'action': 'continue'
            }

        # Use AI to extract phone number
        phone = self._extract_phone_with_ai(message)

        if not phone:
            return {
                'message': STAGE_PROMPTS['phone_collection']['unclear'],
                'stage': 'phone_collection',
                'data': session_data,
                'action': 'continue'
            }

        # Validate phone
        if len(phone) != 10 or not phone.isdigit():
            return {
                'message': STAGE_PROMPTS['phone_collection']['invalid'],
                'stage': 'phone_collection',
                'data': session_data,
                'action': 'continue'
            }

        session_data['phone'] = phone
        session_data['stage'] = 'confirmation'

        # Prepare summary using configuration
        doctor = Doctor.objects.get(id=session_data['doctor_id'])
        date_str = datetime.fromisoformat(session_data['appointment_date']).strftime('%B %d, %Y')

        # Use configured helper function
        summary = get_confirmation_summary(
            session_data=session_data,
            doctor_name=doctor.name,
            specialization=doctor.specialization.name,
            date_str=date_str,
            time=session_data['appointment_time'],
            phone=phone
        )

        return {
            'message': summary,
            'stage': 'confirmation',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_confirmation_ai(self, message, session_data):
        """Handle final confirmation with AI intent detection - warm and professional"""

        if not message:
            return {
                'message': STAGE_PROMPTS['confirmation']['retry'],
                'stage': 'confirmation',
                'data': session_data,
                'action': 'continue'
            }

        # Use AI to detect confirmation intent
        intent = self._detect_confirmation_intent(message)

        if intent == 'confirm':
            # Create appointment
            try:
                appointment = self._create_appointment(session_data)

                if appointment:
                    session_data['stage'] = 'completed'
                    session_data['appointment_id'] = appointment.id

                    doctor = Doctor.objects.get(id=session_data['doctor_id'])
                    date_str = datetime.fromisoformat(session_data['appointment_date']).strftime('%B %d, %Y')

                    # Use configured success message
                    success_msg = get_booking_success_message(
                        appointment_id=appointment.id,
                        patient_name=session_data.get('patient_name', 'there'),
                        doctor_name=doctor.name,
                        date_str=date_str,
                        time=session_data['appointment_time'],
                        phone=session_data['phone'],
                        clinic_name=CLINIC_NAME
                    )

                    return {
                        'message': success_msg,
                        'stage': 'completed',
                        'data': session_data,
                        'action': 'booking_complete'
                    }
                else:
                    return {
                        'message': STAGE_PROMPTS['confirmation']['booking_error'],
                        'stage': 'confirmation',
                        'data': session_data,
                        'action': 'error'
                    }

            except Exception as e:
                print(f"Error creating appointment: {e}")
                return {
                    'message': STAGE_PROMPTS['confirmation']['booking_error'],
                    'stage': 'confirmation',
                    'data': session_data,
                    'action': 'error'
                }

        elif intent == 'change':
            return {
                'message': STAGE_PROMPTS['confirmation']['ask_what_to_change'],
                'stage': 'confirmation',
                'data': session_data,
                'action': 'continue'
            }

        else:
            return {
                'message': STAGE_PROMPTS['confirmation']['unclear'],
                'stage': 'confirmation',
                'data': session_data,
                'action': 'continue'
            }

    # ========== AI-Powered Helper Methods ==========

    def _generate_ai_response(self, context, intent, fallback="I'm here to help you.", max_words=50):
        """
        Generate natural, context-aware responses using Gemini AI

        Args:
            context: Current conversation context
            intent: What the AI should accomplish with this response
            fallback: Fallback message if AI generation fails
            max_words: Maximum words for the response

        Returns:
            AI-generated natural response string
        """
        try:
            model = genai.GenerativeModel(self.gemini_model)
            prompt = f"""You are MediBot, a warm and friendly AI medical receptionist.

Context: {context}

Task: {intent}

Important guidelines:
- Be warm, friendly, and professional
- Keep response under {max_words} words
- Sound natural and conversational (like talking to a real person)
- Don't use formal or robotic language
- Make the patient feel comfortable and valued
- Use contractions (I'm, you're, etc.) for natural speech

Generate a natural, friendly response:"""

            response = model.generate_content(prompt)
            ai_response = response.text.strip()

            # Remove quotes if AI added them
            ai_response = ai_response.replace('"', '').replace("'", '').strip()

            return ai_response

        except Exception as e:
            print(f"AI response generation error: {e}")
            return fallback

    def _extract_name_with_ai(self, message):
        """Extract patient name using Gemini AI"""
        try:
            model = genai.GenerativeModel(self.gemini_model)
            prompt = f"""Extract the person's name from this message: "{message}"

Rules:
- Look for patterns like "my name is X", "I am X", "I'm X", "this is X", or just the name itself
- Return ONLY the name in proper case (e.g., "John Smith")
- If multiple names, return the full name
- If no clear name found, return "NOT_FOUND"

Examples:
- "my name is john" → "John"
- "I am vishnu kumar" → "Vishnu Kumar"
- "sarah" → "Sarah"
- "hello" → "NOT_FOUND"

Name:"""

            response = model.generate_content(prompt)
            result = response.text.strip()

            if result == "NOT_FOUND" or len(result) < 2:
                return None

            # Clean up the result
            result = result.replace('"', '').replace("'", '').strip()
            return ' '.join(word.capitalize() for word in result.split())

        except Exception as e:
            print(f"AI name extraction error: {e}")
            # Fallback to regex
            match = re.search(r'(?:my name is|i am|i\'m|this is|call me)\s+([a-zA-Z\s]+)', message.lower())
            if match:
                return match.group(1).strip().title()
            return None

    def _classify_doctor_input(self, message):
        """Use AI to classify if input is doctor name or symptoms"""
        try:
            model = genai.GenerativeModel(self.gemini_model)
            prompt = f"""Classify this message as either "doctor_name" or "symptoms":

Message: "{message}"

Rules:
- If it mentions a doctor's name (e.g., "Dr. Smith", "John Smith", "Dr. Patel"), return "doctor_name"
- If it describes health issues, symptoms, or medical conditions, return "symptoms"
- Common symptoms: fever, pain, cough, headache, stomach ache, etc.

Return ONLY: doctor_name OR symptoms"""

            response = model.generate_content(prompt)
            result = response.text.strip().lower()

            if 'doctor_name' in result or 'doctor' in result:
                return 'doctor_name'
            else:
                return 'symptoms'

        except Exception as e:
            print(f"AI classification error: {e}")
            # Fallback: check for common symptom keywords
            symptom_keywords = ['pain', 'fever', 'cough', 'cold', 'ache', 'sick', 'hurt', 'problem', 'issue']
            if any(keyword in message.lower() for keyword in symptom_keywords):
                return 'symptoms'
            return 'doctor_name'

    def _find_doctor_by_name_ai(self, message):
        """Find doctor by name with AI enhancement"""
        try:
            # First, use AI to extract the doctor's name
            model = genai.GenerativeModel(self.gemini_model)
            prompt = f"""Extract the doctor's name from this message: "{message}"

Rules:
- Remove prefixes like "Dr.", "Doctor", "I want", "I need", "book"
- Return ONLY the doctor's name (first and/or last name)
- If no clear doctor name, return "NOT_FOUND"

Examples:
- "Dr. John Smith" → "John Smith"
- "I want to see Dr. Patel" → "Patel"
- "book with sarah wilson" → "Sarah Wilson"

Name:"""

            response = model.generate_content(prompt)
            extracted_name = response.text.strip().replace('"', '').replace("'", '')

            if extracted_name == "NOT_FOUND":
                return None

            # Now search for doctor with fuzzy matching
            return self._find_doctor_by_name(extracted_name)

        except Exception as e:
            print(f"AI doctor name extraction error: {e}")
            # Fallback to direct fuzzy matching
            return self._find_doctor_by_name(message)

    def _find_doctor_by_name(self, message):
        """Fuzzy matching for doctor names"""
        cleaned = message.lower().strip()
        cleaned = re.sub(r'^(?:doctor|dr\.?|i want|i need|book)\s+', '', cleaned)

        doctors = Doctor.objects.filter(is_active=True)
        best_match = None
        best_score = 0

        for doctor in doctors:
            score = 0
            doctor_name_lower = doctor.name.lower()

            # Parse name into parts for flexible matching
            name_parts = doctor.name.split()
            first_name = name_parts[0].lower() if name_parts else ""
            last_name = name_parts[-1].lower() if len(name_parts) > 1 else ""

            if cleaned == doctor_name_lower:
                score = 100
            elif cleaned == first_name or cleaned == last_name:
                score = 95
            elif doctor_name_lower in cleaned or cleaned in doctor_name_lower:
                score = 90
            elif first_name in cleaned or last_name in cleaned:
                score = 85
            else:
                similarity = SequenceMatcher(None, cleaned, doctor_name_lower).ratio()
                if similarity >= 0.7:
                    score = int(similarity * 80)

            if score > best_score:
                best_score = score
                best_match = doctor

        return best_match if best_score >= 70 else None

    def _confirm_suggested_doctor(self, message, session_data):
        """Check if user is confirming a suggested doctor - enhanced for natural speech"""
        message_lower = message.lower().strip()

        # Comprehensive confirmation words for natural conversation
        confirmation_phrases = [
            'yes', 'yeah', 'yep', 'yup', 'okay', 'ok', 'k', 'sure', 'book', 'book it',
            'confirm', 'sounds good', 'that works', 'good', 'fine', 'perfect',
            'go ahead', 'please', 'vishnu', 'confirmed', 'definitely', 'absolutely',
            'that\'s fine', 'looks good', 'proceed', 'right', 'correct'
        ]

        # Check for confirmation words (prioritize longer phrases)
        confirmation_phrases_sorted = sorted(confirmation_phrases, key=len, reverse=True)
        is_confirming = any(phrase in message_lower for phrase in confirmation_phrases_sorted)

        if is_confirming:
            suggested_doctors = session_data.get('suggested_doctors', [])
            if suggested_doctors:
                # Confirm first suggested doctor
                doctor_id = suggested_doctors[0]['id']
                return Doctor.objects.get(id=doctor_id)

        # Check if they mentioned a specific doctor name from suggestions
        suggested_doctors = session_data.get('suggested_doctors', [])
        for doc_info in suggested_doctors:
            doctor_name_parts = doc_info['name'].lower().split()
            # Match if any part of the doctor's name is in the message
            if any(part in message_lower for part in doctor_name_parts if len(part) > 2):
                return Doctor.objects.get(id=doc_info['id'])

        return None

    def _parse_date_with_ai(self, message):
        """Parse date using AI with comprehensive natural language understanding"""
        # First try the existing parser
        parsed = self.date_parser.parse(message)
        if parsed:
            print(f"Date parsed by DateParser: {parsed}")
            return parsed

        # If that fails, use Gemini AI with enhanced prompt
        try:
            model = genai.GenerativeModel(self.gemini_model)
            today = timezone.now().date()
            current_weekday = today.strftime('%A')

            prompt = f"""You are a date parser for a medical appointment booking system.

Today's date: {today.strftime('%Y-%m-%d')} ({today.strftime('%A, %B %d, %Y')})
Current day of week: {current_weekday}

Patient said: "{message}"

Extract the appointment date from what the patient said and return it in YYYY-MM-DD format ONLY.

IMPORTANT RULES:
1. If patient says a day of the week (Monday, Tuesday, etc.), find the NEXT occurrence of that day
2. "Wednesday" means the next Wednesday from today
3. "coming Wednesday" or "this Wednesday" means the next Wednesday
4. "next Wednesday" means the Wednesday after the coming Wednesday (7 days later if today is not Wednesday, or 14 days if it is)
5. "tomorrow" means {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
6. "day after tomorrow" means {(today + timedelta(days=2)).strftime('%Y-%m-%d')}
7. For month+day like "December 15", use the upcoming occurrence (this year if not passed, else next year)
8. For just a number like "15th", assume the current or next month

EXAMPLES:
- "tomorrow" → {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
- "Wednesday" → (calculate next Wednesday from {today})
- "coming Wednesday" → (calculate next Wednesday from {today})
- "this Wednesday" → (calculate next Wednesday from {today})
- "next Wednesday" → (calculate Wednesday after next from {today})
- "next Monday" → (calculate next Monday from {today})
- "December 15" → 2025-12-15 (if not passed) or 2026-12-15
- "15th" → (assume current or next month)
- "day after tomorrow" → {(today + timedelta(days=2)).strftime('%Y-%m-%d')}

RESPONSE FORMAT:
- Return ONLY the date in YYYY-MM-DD format
- If unclear or no date mentioned, return "NOT_FOUND"
- Do NOT include any explanation, just the date

Date:"""

            print(f"Sending to Gemini AI for date parsing: {message}")
            response = model.generate_content(prompt)
            result = response.text.strip()
            print(f"Gemini AI date parsing result: {result}")

            if result == "NOT_FOUND" or not result:
                print("Gemini could not parse date")
                return None

            # Clean up the result (remove any extra text)
            # Extract YYYY-MM-DD pattern
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', result)
            if date_match:
                result = date_match.group(1)

            # Parse YYYY-MM-DD format
            parsed_date = datetime.strptime(result, '%Y-%m-%d').date()
            print(f"Successfully parsed date: {parsed_date}")
            return parsed_date

        except Exception as e:
            print(f"AI date parsing error: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_time_with_ai(self, message):
        """Extract time using AI"""
        try:
            model = genai.GenerativeModel(self.gemini_model)
            prompt = f"""Extract the time from this message: "{message}"

Return in 12-hour format like "10:00 AM" or "02:30 PM".
If no time found, return "NOT_FOUND".

Examples:
- "10 am" → "10:00 AM"
- "two thirty pm" → "02:30 PM"
- "eleven" → "11:00 AM"
- "3:30" → "03:30 PM"

Time:"""

            response = model.generate_content(prompt)
            result = response.text.strip()

            if result == "NOT_FOUND":
                return None

            return result

        except Exception as e:
            print(f"AI time extraction error: {e}")
            # Fallback to regex
            return self._parse_time_from_voice(message)

    def _parse_time_from_voice(self, message):
        """Fallback regex time parsing"""
        patterns = [
            r'(\d{1,2})\s*(?::|\.)\s*(\d{2})\s*(am|pm|a\.m\.|p\.m\.)',
            r'(\d{1,2})\s*(am|pm|a\.m\.|p\.m\.)',
            r'(\d{1,2})\s*(?::|\.)\s*(\d{2})',
        ]

        message_lower = message.lower().replace('.', '').replace(':', ' ')

        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                groups = match.groups()
                hour = int(groups[0])
                minute = groups[1] if len(groups) > 2 and groups[1] and groups[1].isdigit() else '00'
                period = groups[-1] if len(groups) > 1 and groups[-1] and groups[-1] in ['am', 'pm'] else None

                if period:
                    if period == 'pm' and hour != 12:
                        hour += 12
                    elif period == 'am' and hour == 12:
                        hour = 0

                return f"{hour:02d}:{minute} {'AM' if hour < 12 else 'PM'}"

        return None

    def _match_time_slot(self, selected_time, available_slots):
        """Match time with flexible matching"""
        for slot in available_slots:
            if slot['available'] and self._times_match(selected_time, slot['time']):
                return slot
        return None

    def _times_match(self, time1, time2):
        """Check if two time strings match (flexible)"""
        # Normalize times
        t1 = time1.upper().replace('.', '').replace(':', ' ').strip()
        t2 = time2.upper().replace('.', '').replace(':', ' ').strip()

        # Direct match
        if t1 == t2:
            return True

        # Extract hour from both
        try:
            h1 = int(re.search(r'(\d{1,2})', t1).group(1))
            h2 = int(re.search(r'(\d{1,2})', t2).group(1))

            # Check if hours match
            return h1 == h2
        except:
            return False

    def _extract_phone_with_ai(self, message):
        """Extract phone number using AI"""
        try:
            model = genai.GenerativeModel(self.gemini_model)
            prompt = f"""Extract the 10-digit phone number from this message: "{message}"

Return ONLY the 10 digits (no spaces, dashes, or formatting).
If no valid 10-digit number found, return "NOT_FOUND".

Examples:
- "nine eight seven six five four three two one zero" → "9876543210"
- "my number is 98765 43210" → "9876543210"
- "1234567890" → "1234567890"

Phone:"""

            response = model.generate_content(prompt)
            result = response.text.strip()

            if result == "NOT_FOUND" or len(result) != 10:
                # Fallback to regex
                return self._extract_phone_number(message)

            return result

        except Exception as e:
            print(f"AI phone extraction error: {e}")
            return self._extract_phone_number(message)

    def _extract_phone_number(self, message):
        """Fallback regex phone extraction"""
        digits = re.sub(r'\D', '', message)

        if len(digits) == 10:
            return digits

        if len(digits) > 10:
            match = re.search(r'(\d{10})', digits)
            if match:
                return match.group(1)

        return None

    def _detect_confirmation_intent(self, message):
        """Detect if user is confirming or wanting to change - enhanced for natural conversation"""
        message_lower = message.lower().strip()

        # Comprehensive confirmation phrases (common in natural speech)
        confirm_words = [
            'yes', 'yeah', 'yep', 'yup', 'correct', 'confirm', 'book', 'book it',
            'okay', 'ok', 'k', 'sure', 'right', 'perfect', 'good', 'fine',
            'sounds good', 'that works', 'that\'s fine', 'looks good', 'proceed',
            'go ahead', 'continue', 'please', 'vishnu', 'confirmed', 'definitely',
            'absolutely', 'exactly', 'great', 'awesome', 'nice', 'affirmative'
        ]

        # Change/rejection phrases
        change_words = [
            'no', 'nope', 'nah', 'change', 'wrong', 'different', 'modify',
            'update', 'fix', 'wait', 'hold on', 'not right', 'incorrect',
            'that\'s not', 'not correct', 'redo', 'restart', 'again'
        ]

        # Check for confirmation (prioritize longer phrases first)
        confirm_words_sorted = sorted(confirm_words, key=len, reverse=True)
        for word in confirm_words_sorted:
            if word in message_lower:
                return 'confirm'

        # Check for change/rejection
        for word in change_words:
            if word in message_lower:
                return 'change'

        return 'unclear'

    # ========== Intent Handlers ==========

    def _handle_cancellation(self, session_data):
        """Handle booking cancellation - understanding and professional"""
        session_data['stage'] = 'completed'
        return {
            'message': INTENT_RESPONSES['cancel'],
            'stage': 'completed',
            'data': session_data,
            'action': 'cancelled'
        }

    def _handle_go_back(self, session_data):
        """Handle going back to previous stage"""
        stage_order = ['greeting', 'patient_name', 'doctor_selection', 'date_selection', 'time_selection', 'phone_collection', 'confirmation']
        current_stage = session_data.get('stage', 'greeting')

        try:
            current_index = stage_order.index(current_stage)
            if current_index > 0:
                previous_stage = stage_order[current_index - 1]
                session_data['stage'] = previous_stage

                return {
                    'message': f"Okay, going back. {self._get_stage_prompt(previous_stage, session_data)}",
                    'stage': previous_stage,
                    'data': session_data,
                    'action': 'continue'
                }
        except:
            pass

        return {
            'message': "We're already at the beginning. What would you like to do?",
            'stage': current_stage,
            'data': session_data,
            'action': 'continue'
        }

    def _handle_correction(self, intent, session_data):
        """Handle corrections to previously entered data"""
        field = intent.get('field')
        value = intent.get('extracted_value')

        if field and value:
            session_data[field] = value
            return {
                'message': f"Got it, I've updated your {field} to {value}. What else would you like to change, or should we continue?",
                'stage': session_data.get('stage', 'confirmation'),
                'data': session_data,
                'action': 'continue'
            }
        else:
            return {
                'message': "I understand you want to make a correction. What would you like to change?",
                'stage': session_data.get('stage', 'confirmation'),
                'data': session_data,
                'action': 'continue'
            }

    def _handle_change_request(self, intent, session_data):
        """Handle requests to change doctor/date/time - flexible and helpful"""
        change_type = intent.get('intent')

        if change_type == 'change_doctor':
            session_data['stage'] = 'doctor_selection'
            session_data.pop('doctor_id', None)
            session_data.pop('doctor_name', None)
            return {
                'message': INTENT_RESPONSES['change_doctor'],
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }
        elif change_type == 'change_date':
            session_data['stage'] = 'date_selection'
            session_data.pop('appointment_date', None)
            return {
                'message': INTENT_RESPONSES['change_date'],
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }
        elif change_type == 'change_time':
            session_data['stage'] = 'time_selection'
            session_data.pop('appointment_time', None)

            # Re-fetch available slots
            doctor_id = session_data.get('doctor_id')
            date = datetime.fromisoformat(session_data.get('appointment_date')).date()
            available_slots = self._get_available_slots(doctor_id, date)
            session_data['available_slots'] = available_slots

            time_options = self._format_time_slots_for_voice(available_slots)
            change_time_msg = INTENT_RESPONSES['change_time'].format(time_slots=time_options)

            return {
                'message': change_time_msg,
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        return {
            'message': STAGE_PROMPTS['confirmation']['ask_what_to_change'],
            'stage': session_data.get('stage', 'confirmation'),
            'data': session_data,
            'action': 'continue'
        }

    def _get_stage_prompt(self, stage, session_data):
        """Get prompt for a specific stage"""
        prompts = {
            'patient_name': "What's your name?",
            'doctor_selection': "Which doctor would you like to see?",
            'date_selection': "What date would you like?",
            'time_selection': "What time works for you?",
            'phone_collection': "What's your phone number?",
            'confirmation': "Let me confirm your details..."
        }
        return prompts.get(stage, "How can I help you?")

    # ========== Database Operations ==========

    def _get_available_slots(self, doctor_id, date):
        """Get available time slots for doctor on specific date"""
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            weekday = date.strftime('%A')

            schedules = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=weekday
            )

            if not schedules.exists():
                return []

            existing_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                status__in=['pending', 'confirmed']
            ).values_list('appointment_time', flat=True)

            booked_times = [time.strftime('%I:%M %p') for time in existing_appointments]

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

    def _find_next_available_date(self, doctor_id, start_date, max_days=90):
        """
        Find next available date for doctor with extended search range (90 days)

        Args:
            doctor_id: Doctor ID
            start_date: Starting date for search
            max_days: Maximum days to search ahead (default: 90)

        Returns:
            Next available date or None
        """
        current_date = start_date + timedelta(days=1)
        max_date = start_date + timedelta(days=max_days)

        while current_date <= max_date:
            slots = self._get_available_slots(doctor_id, current_date)
            if any(slot['available'] for slot in slots):
                return current_date
            current_date += timedelta(days=1)

        return None

    def _get_alternative_doctors_with_availability(self, current_doctor_id, specialization_id=None, date_from=None):
        """
        Find alternative doctors with availability when current doctor is fully booked

        Args:
            current_doctor_id: Current doctor being considered
            specialization_id: Preferred specialization (optional)
            date_from: Check availability from this date (optional)

        Returns:
            List of dicts with doctor info and next available date
        """
        # Get current doctor's specialization if not provided
        if not specialization_id:
            try:
                current_doctor = Doctor.objects.get(id=current_doctor_id)
                specialization_id = current_doctor.specialization_id
            except Doctor.DoesNotExist:
                return []

        # Find other doctors with same specialization
        alternative_doctors = Doctor.objects.filter(
            specialization_id=specialization_id,
            is_active=True
        ).exclude(id=current_doctor_id).order_by('consultation_fee')[:3]

        if not date_from:
            date_from = timezone.now().date()

        doctors_with_availability = []

        for doctor in alternative_doctors:
            # Check next available date for each doctor (30-day window for alternatives)
            next_date = self._find_next_available_date(doctor.id, date_from, max_days=30)

            if next_date:
                doctors_with_availability.append({
                    'id': doctor.id,
                    'name': doctor.name,
                    'fee': float(doctor.consultation_fee) if doctor.consultation_fee else 0,
                    'specialization': doctor.specialization.name if doctor.specialization else '',
                    'next_available': next_date.isoformat() if next_date else None,
                    'next_available_date_obj': next_date,  # Keep date object for internal use
                    'days_away': (next_date - date_from).days
                })

        # Sort by soonest availability
        doctors_with_availability.sort(key=lambda x: x['days_away'])

        return doctors_with_availability

    def _detect_symptom_change(self, message, current_stage):
        """
        Detect if user is mentioning new symptoms that might require different doctor

        Returns:
            Boolean indicating if symptoms are mentioned
        """
        symptom_keywords = [
            'pain', 'ache', 'hurt', 'symptom', 'feel', 'sick', 'ill',
            'fever', 'cold', 'cough', 'headache', 'stomach', 'chest',
            'back', 'leg', 'arm', 'throat', 'nose', 'ear', 'eye',
            'dizzy', 'nausea', 'vomit', 'diarrhea', 'constipation',
            'rash', 'itch', 'swelling', 'bleeding', 'tired', 'weak'
        ]

        message_lower = message.lower()

        # Check if any symptom keywords are present
        has_symptoms = any(keyword in message_lower for keyword in symptom_keywords)

        # Additional check: if message contains "I have" or "I feel" or "my"
        symptom_phrases = ['i have', 'i feel', 'i am', 'my ', 'got ', 'experiencing', 'also']
        has_symptom_phrase = any(phrase in message_lower for phrase in symptom_phrases)

        return has_symptoms and has_symptom_phrase

    def _handle_mid_conversation_symptom_change(self, message, session_data):
        """
        Handle when user mentions new symptoms after already selecting a doctor
        """
        current_doctor_name = session_data.get('doctor_name', 'the current doctor')

        response_msg = f"I hear you mentioning additional symptoms. Just to make sure we're booking you with the right specialist, "
        response_msg += f"would you like me to re-evaluate which doctor is best for you based on all your symptoms, or would you still prefer to continue with Dr. {current_doctor_name}? "
        response_msg += "You can say 'find new doctor' or 'continue with current doctor'."

        session_data['awaiting_doctor_reconfirmation'] = True
        session_data['new_symptoms'] = message

        return {
            'message': response_msg,
            'stage': session_data.get('stage', 'doctor_selection'),
            'data': session_data,
            'action': 'continue'
        }

    def _format_time_slots_for_voice(self, slots):
        """Format time slots for natural voice output"""
        available = [s['time'] for s in slots if s['available']][:5]

        if not available:
            return "Unfortunately, there are no available slots"

        if len(available) == 1:
            return available[0]
        elif len(available) == 2:
            return f"{available[0]} and {available[1]}"
        else:
            return ", ".join(available[:-1]) + f", and {available[-1]}"

    def _create_appointment(self, session_data):
        """Create appointment in database"""
        try:
            doctor = Doctor.objects.get(id=session_data['doctor_id'])
            appointment_date = datetime.fromisoformat(session_data['appointment_date']).date()

            time_str = session_data['appointment_time']
            appointment_time = datetime.strptime(time_str, '%I:%M %p').time()

            appointment = Appointment.objects.create(
                doctor=doctor,
                patient_name=session_data['patient_name'],
                patient_phone=session_data['phone'],
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                status='confirmed',
                booking_method='voice_assistant'
            )

            # Send SMS
            try:
                from twilio_service import send_sms
                send_sms(
                    to=session_data['phone'],
                    message=f"Appointment confirmed! Dr. {doctor.name} on {appointment_date.strftime('%B %d, %Y')} at {time_str}. ID: {appointment.id}"
                )
            except Exception as e:
                print(f"SMS sending failed: {e}")

            return appointment

        except Exception as e:
            print(f"Error creating appointment: {e}")
            return None
