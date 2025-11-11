"""
Voice Assistant Manager - AI-Powered Natural Conversational Flow
Enhanced with Gemini AI for superior accuracy and intelligence
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


class VoiceAssistantManager:
    """
    AI-Powered Senior Booking Specialist for Appointment Booking
    Acts like a professional senior booking specialist with comprehensive intelligence
    Uses Gemini AI for intelligent natural language understanding and decision-making
    """

    ASSISTANT_NAME = "MediBot Senior Booking Specialist"
    SPECIALIST_ROLE = "Senior Medical Booking Specialist"

    # Conversation stages
    STAGES = {
        'greeting': 'greeting',
        'patient_name': 'patient_name',
        'urgency_assessment': 'urgency_assessment',
        'doctor_selection': 'doctor_selection',
        'date_selection': 'date_selection',
        'time_selection': 'time_selection',
        'phone_collection': 'phone_collection',
        'confirmation': 'confirmation',
        'completed': 'completed'
    }

    # Booking type classification
    BOOKING_TYPES = {
        'urgent': 'Urgent Care',
        'routine': 'Routine Checkup',
        'follow_up': 'Follow-up Consultation',
        'emergency': 'Emergency'
    }

    def __init__(self, session_id):
        self.session_id = session_id
        self.claude_service = ClaudeService()
        self.date_parser = DateParser()

        # Configure Gemini
        genai.configure(api_key=settings.ANTHROPIC_API_KEY)
        self.gemini_model = "gemini-2.5-flash"

        # Senior specialist attributes
        self.urgency_keywords = {
            'emergency': ['emergency', 'urgent', 'severe', 'critical', 'acute', 'immediately', 'asap', 'now'],
            'high_priority': ['pain', 'bleeding', 'fever', 'can\'t breathe', 'chest pain', 'difficulty breathing'],
            'moderate': ['soon', 'this week', 'few days', 'uncomfortable'],
            'routine': ['checkup', 'routine', 'regular', 'follow up', 'follow-up', 'general']
        }

        # Comprehensive symptom-to-specialization mapping for robust fallback
        self.symptom_specialization_map = {
            # Orthopedic keywords
            'orthopedic': ['bone', 'fracture', 'joint', 'leg pain', 'leg', 'ankle', 'knee', 'hip', 'back pain',
                          'spine', 'shoulder', 'elbow', 'wrist', 'foot', 'arthritis', 'sprain', 'muscle pain'],
            # Cardiology keywords
            'cardiology': ['heart', 'chest pain', 'chest', 'cardiac', 'palpitation', 'heart attack',
                          'blood pressure', 'hypertension', 'breathing difficulty'],
            # General Physician keywords
            'general physician': ['fever', 'cold', 'cough', 'flu', 'headache', 'body ache', 'weakness',
                                 'fatigue', 'general', 'checkup', 'tired'],
            # Dermatology keywords
            'dermatology': ['skin', 'rash', 'acne', 'allergy', 'itch', 'dermat', 'hair', 'scalp'],
            # ENT keywords
            'ent': ['ear', 'nose', 'throat', 'tonsil', 'hearing', 'sinus', 'voice'],
            # Pediatrics keywords
            'pediatrics': ['child', 'baby', 'infant', 'kid', 'pediatric', 'vaccination'],
            # Gynecology keywords
            'gynecology': ['pregnancy', 'period', 'menstrual', 'gynec', 'women', 'obstetric'],
            # Neurology keywords
            'neurology': ['brain', 'neurolog', 'migraine', 'seizure', 'paralysis', 'nerve', 'numbness'],
            # Gastroenterology keywords
            'gastroenterology': ['stomach', 'abdomen', 'digestion', 'gastric', 'liver', 'intestine'],
            # Ophthalmology keywords
            'ophthalmology': ['eye', 'vision', 'sight', 'ophthal', 'blind'],
            # Dentistry keywords
            'dentistry': ['tooth', 'teeth', 'dental', 'gum', 'mouth', 'cavity'],
        }

    def _normalize_voice_input(self, message):
        """
        Normalize voice input to handle common transcription issues
        """
        if not message:
            return message

        # Common voice transcription fixes
        message = message.strip()

        # Handle common transcription patterns
        replacements = {
            'yeah yeah': 'yes',
            'ok ok': 'okay',
            'uh ': '',
            'um ': '',
            'ah ': '',
        }

        message_lower = message.lower()
        for pattern, replacement in replacements.items():
            message_lower = message_lower.replace(pattern, replacement)

        return message_lower.strip()

    def process_voice_message(self, message, session_data):
        """
        Process voice input with AI intelligence
        Handles voice transcription normalization and robust understanding

        Args:
            message: User's voice input (transcribed text)
            session_data: Current session state

        Returns:
            dict: Response with message, stage, data, action
        """
        # Normalize voice input
        if message:
            message = self._normalize_voice_input(message)
            print(f"[VOICEBOT] Normalized input: '{message}'")

        current_stage = session_data.get('stage', 'greeting')

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
            'urgency_assessment': self._handle_urgency_assessment,
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
        """Initial greeting with senior specialist professionalism"""

        # Check if user already provided their name using AI
        if message and len(message.strip()) > 2:
            name_extracted = self._extract_name_with_ai(message)
            if name_extracted:
                session_data['patient_name'] = name_extracted
                session_data['stage'] = 'urgency_assessment'

                return {
                    'message': f"Good day {name_extracted}! I'm {self.SPECIALIST_ROLE}, and I'll personally assist you with your appointment booking today. With years of experience in healthcare scheduling, I'm here to ensure you get the best care at the most suitable time. Before we proceed, I'd like to understand your medical needs better. Could you please describe what brings you in today? Are you experiencing any specific symptoms, or is this a routine visit?",
                    'stage': 'urgency_assessment',
                    'data': session_data,
                    'action': 'continue'
                }

        # Standard greeting
        session_data['stage'] = 'patient_name'
        return {
            'message': f"Good day! I'm your {self.SPECIALIST_ROLE}, and I'm here to provide you with expert assistance in booking your medical appointment. Think of me as your personal healthcare scheduling expert who will carefully review all doctor details, their specializations, experience, and available time slots to find the perfect match for your needs. May I have your name to begin?",
            'stage': 'patient_name',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_patient_name_ai(self, message, session_data):
        """Collect patient name using AI extraction"""

        if not message or len(message.strip()) < 2:
            return {
                'message': "I didn't quite catch that. Could you please tell me your name again?",
                'stage': 'patient_name',
                'data': session_data,
                'action': 'continue'
            }

        # Use AI to extract name
        patient_name = self._extract_name_with_ai(message)

        if not patient_name:
            return {
                'message': "I'm sorry, I couldn't understand the name. Could you please say your name clearly?",
                'stage': 'patient_name',
                'data': session_data,
                'action': 'continue'
            }

        session_data['patient_name'] = patient_name
        session_data['stage'] = 'urgency_assessment'

        return {
            'message': f"It's a pleasure to assist you, {patient_name}. As your dedicated booking specialist, I want to ensure we find the most appropriate doctor and time slot for your specific needs. To do this effectively, I need to understand what brings you in today. Could you please tell me: Are you experiencing any symptoms or health concerns? Or perhaps this is a routine checkup or follow-up appointment? This will help me match you with the right specialist and prioritize your booking appropriately.",
            'stage': 'urgency_assessment',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_urgency_assessment(self, message, session_data):
        """
        Senior specialist urgency assessment and booking type classification
        Determines priority and helps match with appropriate doctor and time slots
        """
        if not message:
            return {
                'message': "I didn't catch that. Please tell me what brings you in today - are you experiencing symptoms, or is this a routine visit?",
                'stage': 'urgency_assessment',
                'data': session_data,
                'action': 'continue'
            }

        # Assess urgency level using AI and keywords
        urgency_level = self._assess_urgency_level(message)
        booking_type = self._classify_booking_type(message, urgency_level)

        session_data['symptoms_description'] = message
        session_data['urgency_level'] = urgency_level
        session_data['booking_type'] = booking_type

        # Provide empathetic response based on urgency
        if urgency_level == 'emergency':
            return {
                'message': f"I understand this is urgent, {session_data['patient_name']}. For emergency situations, I strongly recommend you visit the emergency room or call emergency services immediately. However, if you'd still like to book an urgent appointment, I'll do my best to find you the earliest available slot with an experienced specialist. Shall we proceed with the booking?",
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }
        elif urgency_level == 'high_priority':
            session_data['stage'] = 'doctor_selection'
            return {
                'message': f"I understand you're experiencing discomfort, and I want to help you get care as quickly as possible. I'll prioritize finding you an appointment with one of our most experienced doctors at the earliest available time. Let me analyze your symptoms and match you with the right specialist. Please give me a moment...",
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }
        elif urgency_level == 'moderate':
            session_data['stage'] = 'doctor_selection'
            return {
                'message': f"Thank you for sharing that with me. I'll help you find a suitable appointment within the next few days. Based on what you've described, I'll recommend doctors who specialize in this area and have good availability. Let me check our specialists...",
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }
        else:  # routine
            session_data['stage'] = 'doctor_selection'
            return {
                'message': f"Perfect! For a {booking_type.lower()}, I'll help you find the right doctor and a convenient time that fits your schedule. Would you like to see a specific doctor, or shall I recommend someone based on your needs?",
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }

    def _handle_doctor_selection_ai(self, message, session_data):
        """
        Handle doctor selection with senior specialist intelligence
        Comprehensive checking of doctor experience, specialization, and availability
        """

        if not message:
            return {
                'message': "I didn't hear anything. Could you please tell me which doctor you'd like to see, or let me recommend based on your symptoms?",
                'stage': 'doctor_selection',
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

                # Provide comprehensive doctor details like a senior specialist
                doctor_details = self._get_comprehensive_doctor_details(doctor)

                return {
                    'message': f"Excellent choice! Let me provide you with complete details about Dr. {doctor.name}. {doctor_details} Based on my review, Dr. {doctor.name} is well-qualified for your needs. Now, what date would you like to schedule your appointment? I can check availability for today, tomorrow, specific dates, or days of the week.",
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }
            else:
                return {
                    'message': "I've thoroughly checked our database, but I couldn't find a doctor with that exact name. Could you please spell the name differently, or would you prefer that I recommend an experienced specialist based on your symptoms? As a senior booking specialist, I can match you with the most suitable doctor.",
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }
        else:
            # Treat as symptoms and analyze with AI - or from urgency assessment
            # Check if we already have symptoms from urgency assessment
            if session_data.get('symptoms_description') and not message.lower() in ['yes', 'ok', 'okay', 'sure', 'proceed']:
                # New symptoms mentioned, update
                session_data['symptoms_description'] = message

            return self._analyze_symptoms_and_suggest_ai(
                session_data.get('symptoms_description', message),
                session_data
            )

    def _analyze_symptoms_and_suggest_ai(self, message, session_data):
        """
        Analyze symptoms using multiple methods for robust understanding
        1. AI Analysis with Gemini
        2. Keyword matching from comprehensive symptom map
        3. Database keyword matching
        """
        message_lower = message.lower()

        # Method 1: Try AI analysis first
        specialization_name = None
        confidence = 'low'
        reasoning = ''

        try:
            print(f"[VOICEBOT] Analyzing symptoms with AI: {message}")
            analysis = self.claude_service.analyze_symptoms(message)
            specialization_name = analysis.get('specialization', '').lower()
            confidence = analysis.get('confidence', 'low')
            reasoning = analysis.get('reasoning', '')
            print(f"[VOICEBOT] AI Analysis result: {specialization_name}, confidence: {confidence}")
        except Exception as e:
            print(f"[VOICEBOT] AI analysis failed: {e}")
            specialization_name = None

        # Method 2: Keyword matching from symptom map (robust fallback)
        if not specialization_name or confidence == 'low':
            print(f"[VOICEBOT] Using keyword matching for: {message_lower}")
            matched_specs = []
            for spec_name, keywords in self.symptom_specialization_map.items():
                match_count = sum(1 for keyword in keywords if keyword.lower() in message_lower)
                if match_count > 0:
                    matched_specs.append((spec_name, match_count))

            if matched_specs:
                # Sort by match count and get the best match
                matched_specs.sort(key=lambda x: x[1], reverse=True)
                specialization_name = matched_specs[0][0]
                confidence = 'high' if matched_specs[0][1] > 1 else 'medium'
                reasoning = f"Matched {matched_specs[0][1]} keywords from your symptoms"
                print(f"[VOICEBOT] Keyword match found: {specialization_name} (matches: {matched_specs[0][1]})")

        # If still no match, default to General Physician
        if not specialization_name:
            specialization_name = 'general physician'
            confidence = 'medium'
            reasoning = "I'll recommend a general physician who can assess your condition"
            print(f"[VOICEBOT] Using default: General Physician")

        # Find matching specialization in database
        specialization = Specialization.objects.filter(
            name__icontains=specialization_name
        ).first()

        # Method 3: Try alternate names and database keyword matching
        if not specialization:
            print(f"[VOICEBOT] Exact match not found, trying alternates...")
            # Try partial matches
            all_specs = Specialization.objects.all()
            for spec in all_specs:
                spec_name_lower = spec.name.lower()
                # Check if any word from specialization_name is in spec.name
                spec_words = specialization_name.split()
                if any(word in spec_name_lower for word in spec_words):
                    specialization = spec
                    print(f"[VOICEBOT] Found partial match: {spec.name}")
                    break

                # Check database keywords
                if spec.keywords:
                    keywords = spec.keywords.lower()
                    if any(keyword.strip() in message_lower for keyword in keywords.split(',')):
                        specialization = spec
                        print(f"[VOICEBOT] Found via database keywords: {spec.name}")
                        break

        if not specialization:
            print(f"[VOICEBOT] No specialization found in database")
            return {
                'message': f"I understand you're experiencing {message}. While I think you might need a {specialization_name}, I don't have that exact specialization available. Let me suggest our General Physician who can evaluate your condition. Alternatively, you can tell me which type of doctor you'd prefer - for example, 'orthopedic', 'cardiologist', or 'dermatologist'?",
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }

        print(f"[VOICEBOT] Found specialization: {specialization.name}")

        # Get available doctors for this specialization
        # Senior specialist logic: prioritize by experience for urgent cases
        urgency_level = session_data.get('urgency_level', 'routine')

        if urgency_level in ['emergency', 'high_priority']:
            # Prioritize by experience for urgent cases
            doctors = Doctor.objects.filter(
                specialization=specialization,
                is_active=True
            ).order_by('-experience_years', 'consultation_fee')
        else:
            # Balance between experience and cost for routine cases
            doctors = Doctor.objects.filter(
                specialization=specialization,
                is_active=True
            ).order_by('consultation_fee', '-experience_years')

        if not doctors.exists():
            print(f"[VOICEBOT] No doctors found for {specialization.name}")
            return {
                'message': f"I'm sorry, we don't have any {specialization.name} doctors available at the moment. Would you like to try booking with a different type of doctor?",
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Suggest doctor(s) with comprehensive AI-generated response
        suggested_doctor = doctors.first()
        print(f"[VOICEBOT] Suggesting doctor: {suggested_doctor.name}")

        session_data['suggested_doctors'] = [
            {'id': doc.id, 'name': doc.name, 'fee': str(doc.consultation_fee), 'experience': doc.experience_years}
            for doc in doctors[:3]
        ]
        session_data['suggested_specialization'] = specialization.name

        # Get comprehensive details about suggested doctor
        doctor_details = self._get_comprehensive_doctor_details(suggested_doctor)

        # Generate intelligent response as senior specialist
        if doctors.count() == 1:
            message_text = f"After carefully analyzing your symptoms - {reasoning} - I strongly recommend Dr. {suggested_doctor.name}. {doctor_details} Dr. {suggested_doctor.name} is our specialist in {specialization.name} and is well-suited for your case. Would you like to proceed with booking an appointment with Dr. {suggested_doctor.name}? Just say 'yes' to continue."
        else:
            # Provide detailed comparison
            urgency_note = ""
            if urgency_level in ['emergency', 'high_priority']:
                urgency_note = f"Given the urgency of your situation, I've prioritized our most experienced doctors. "

            message_text = f"Based on my thorough analysis of your symptoms, I recommend seeing a {specialization.name}. {urgency_note}"
            message_text += f"I particularly recommend Dr. {suggested_doctor.name}. {doctor_details} "

            if doctors.count() > 1:
                other_doctors_list = []
                for doc in doctors[1:3]:
                    other_doctors_list.append(
                        f"Dr. {doc.name} ({doc.experience_years} years experience, {doc.consultation_fee} rupees)"
                    )

                if other_doctors_list:
                    message_text += f"We also have excellent alternatives: {', or '.join(other_doctors_list)}. "

            message_text += f"Which doctor would you like me to book for you? You can say the doctor's name."

        print(f"[VOICEBOT] Recommendation complete")
        return {
            'message': message_text,
            'stage': 'doctor_selection',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_date_selection_ai(self, message, session_data):
        """Handle date selection with AI parsing"""

        if not message:
            return {
                'message': "I didn't catch the date. Could you tell me when you'd like to book? You can say 'tomorrow', 'next Monday', or mention a specific date.",
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Use AI to parse date from natural language
        parsed_date = self._parse_date_with_ai(message)

        if not parsed_date:
            return {
                'message': "I couldn't understand that date. Could you try saying it differently? For example, 'tomorrow', 'December 15th', or 'next Friday'.",
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Validate date
        today = timezone.now().date()

        if parsed_date < today:
            return {
                'message': "That date has already passed. Please choose a date from today onwards. What date would you like?",
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
                    'message': "I noticed you mentioned a date, but we haven't selected a doctor yet. Which doctor would you like to book with?",
                    'stage': 'doctor_selection',
                    'data': session_data,
                    'action': 'continue'
                }

        available_slots = self._get_available_slots(doctor_id, parsed_date)

        if not available_slots:
            # Suggest next available date
            next_available = self._find_next_available_date(doctor_id, parsed_date)
            if next_available:
                next_date_formatted = next_available.strftime('%B %d, %Y')
                return {
                    'message': f"I'm sorry, the doctor isn't available on {parsed_date.strftime('%B %d, %Y')}. However, the next available date is {next_date_formatted}. Would you like to book on that date instead?",
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }
            else:
                return {
                    'message': "Unfortunately, the doctor doesn't have any availability in the next few weeks. Would you like to try a different doctor or check dates further out?",
                    'stage': 'date_selection',
                    'data': session_data,
                    'action': 'continue'
                }

        session_data['appointment_date'] = parsed_date.isoformat()
        session_data['available_slots'] = available_slots
        session_data['stage'] = 'time_selection'

        # Format slots for voice with professional context
        time_options = self._format_time_slots_for_voice(available_slots)
        date_formatted = parsed_date.strftime('%B %d, %Y')

        # Add intelligent recommendation based on urgency
        urgency_level = session_data.get('urgency_level', 'routine')
        recommendation = ""

        if urgency_level in ['emergency', 'high_priority'] and available_slots:
            earliest_slot = next((slot for slot in available_slots if slot['available']), None)
            if earliest_slot:
                recommendation = f" As this is a priority case, I recommend taking the earliest slot at {earliest_slot['time']} to ensure you receive timely care."

        return {
            'message': f"Excellent! {date_formatted} is available. I've checked all the time slots for you. The doctor has the following times open: {time_options}.{recommendation} Which time works best for your schedule?",
            'stage': 'time_selection',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_time_selection_ai(self, message, session_data):
        """Handle time slot selection with AI"""

        if not message:
            return {
                'message': "I didn't catch the time. What time would you prefer? You can say something like '10 AM' or '2:30 PM'.",
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        # Use AI to extract time from message
        selected_time = self._extract_time_with_ai(message)

        if not selected_time:
            return {
                'message': "I couldn't understand that time. Could you say it again? For example, 'ten AM' or 'two thirty PM'.",
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
                    return {
                        'message': f"I'm sorry, {selected_time} is already booked. Here are some available times: {alt_times}. Which one works better for you?",
                        'stage': 'time_selection',
                        'data': session_data,
                        'action': 'continue'
                    }

            return {
                'message': "That time slot isn't available. Let me tell you the available times again: " + self._format_time_slots_for_voice(available_slots) + ". Which time would you like?",
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        session_data['appointment_time'] = matched_slot['time']
        session_data['stage'] = 'phone_collection'

        # Add professional note based on urgency
        urgency_level = session_data.get('urgency_level', 'routine')
        urgency_note = ""
        if urgency_level == 'high_priority':
            urgency_note = " Given the urgency, I've prioritized this time slot for you."
        elif urgency_level == 'emergency':
            urgency_note = " This is the earliest available slot I could secure for you."

        return {
            'message': f"Perfect! I've successfully reserved {matched_slot['time']} for your appointment.{urgency_note} Now, to complete your booking and send you a confirmation message, I'll need your 10-digit mobile number. What's your contact number?",
            'stage': 'phone_collection',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_phone_collection_ai(self, message, session_data):
        """Collect phone number with AI extraction"""

        if not message:
            return {
                'message': "I didn't catch your phone number. Could you say your 10-digit mobile number again?",
                'stage': 'phone_collection',
                'data': session_data,
                'action': 'continue'
            }

        # Use AI to extract phone number
        phone = self._extract_phone_with_ai(message)

        if not phone:
            return {
                'message': "I couldn't understand that phone number. Please say your 10-digit mobile number clearly, digit by digit if needed.",
                'stage': 'phone_collection',
                'data': session_data,
                'action': 'continue'
            }

        # Validate phone
        if len(phone) != 10 or not phone.isdigit():
            return {
                'message': "That doesn't seem like a valid 10-digit phone number. Could you say it again? Make sure it's a 10-digit number.",
                'stage': 'phone_collection',
                'data': session_data,
                'action': 'continue'
            }

        session_data['phone'] = phone
        session_data['stage'] = 'confirmation'

        # Prepare summary
        doctor = Doctor.objects.get(id=session_data['doctor_id'])
        date_str = datetime.fromisoformat(session_data['appointment_date']).strftime('%B %d, %Y')

        # Format phone number for speaking (e.g., "98765 43210")
        phone_formatted = f"{phone[:5]} {phone[5:]}"

        summary = f"Perfect! Let me confirm your appointment details as your senior booking specialist. Your name is {session_data['patient_name']}. You're booking with Dr. {doctor.name}, who is a {doctor.specialization.name} with {doctor.experience_years} years of experience. The appointment is scheduled for {date_str} at {session_data['appointment_time']}. Your contact number is {phone_formatted}. The consultation fee will be {doctor.consultation_fee} rupees. Is everything correct? Say 'yes' to confirm or tell me what needs to be changed."

        return {
            'message': summary,
            'stage': 'confirmation',
            'data': session_data,
            'action': 'continue'
        }

    def _handle_confirmation_ai(self, message, session_data):
        """Handle final confirmation with AI intent detection"""

        if not message:
            return {
                'message': "I didn't hear you. Please say 'yes' to confirm the booking or tell me what you'd like to change.",
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

                    return {
                        'message': f"Excellent news! As your senior booking specialist, I've successfully confirmed your appointment. Your booking ID is {appointment.id}. You'll receive an SMS confirmation shortly at {session_data['phone']}. To recap: you have an appointment with Dr. {doctor.name}, {doctor.specialization.name}, on {date_str} at {session_data['appointment_time']}. The consultation fee is {doctor.consultation_fee} rupees. Please arrive 10 minutes early. Is there anything else I can help you with today?",
                        'stage': 'completed',
                        'data': session_data,
                        'action': 'booking_complete'
                    }
                else:
                    return {
                        'message': "I'm sorry, there was an error creating your appointment. This might be a technical issue. Could you please try again, or would you like to contact our support team?",
                        'stage': 'confirmation',
                        'data': session_data,
                        'action': 'error'
                    }

            except Exception as e:
                print(f"Error creating appointment: {e}")
                return {
                    'message': "I apologize, but something went wrong while booking your appointment. The issue has been logged. Would you like to try again?",
                    'stage': 'confirmation',
                    'data': session_data,
                    'action': 'error'
                }

        elif intent == 'change':
            return {
                'message': "No problem! What would you like to change? You can say 'change doctor', 'change date', 'change time', 'change phone number', or 'change name'.",
                'stage': 'confirmation',
                'data': session_data,
                'action': 'continue'
            }

        else:
            return {
                'message': "I didn't quite understand. Could you please say 'yes' to confirm the booking, or tell me specifically what you'd like to change?",
                'stage': 'confirmation',
                'data': session_data,
                'action': 'continue'
            }

    # ========== Senior Specialist Intelligence Methods ==========

    def _assess_urgency_level(self, message):
        """
        Assess urgency level from patient's message
        Uses keyword matching and AI for intelligent assessment
        """
        message_lower = message.lower()

        # Check for emergency keywords
        for keyword in self.urgency_keywords['emergency']:
            if keyword in message_lower:
                return 'emergency'

        # Check for high priority keywords
        for keyword in self.urgency_keywords['high_priority']:
            if keyword in message_lower:
                return 'high_priority'

        # Check for moderate keywords
        for keyword in self.urgency_keywords['moderate']:
            if keyword in message_lower:
                return 'moderate'

        # Check for routine keywords
        for keyword in self.urgency_keywords['routine']:
            if keyword in message_lower:
                return 'routine'

        # Default to moderate if uncertain
        return 'moderate'

    def _classify_booking_type(self, message, urgency_level):
        """
        Classify the type of booking based on message and urgency
        """
        message_lower = message.lower()

        if urgency_level == 'emergency':
            return self.BOOKING_TYPES['emergency']
        elif 'follow' in message_lower or 'followup' in message_lower:
            return self.BOOKING_TYPES['follow_up']
        elif urgency_level in ['high_priority', 'moderate']:
            return self.BOOKING_TYPES['urgent']
        else:
            return self.BOOKING_TYPES['routine']

    def _get_comprehensive_doctor_details(self, doctor):
        """
        Get comprehensive doctor details like a senior specialist would provide
        Includes experience, qualifications, specialization, and fee
        """
        details = []

        # Experience
        if doctor.experience_years > 0:
            exp_text = f"Dr. {doctor.name} brings {doctor.experience_years} years of valuable medical experience"
            details.append(exp_text)

        # Qualification
        if doctor.qualification:
            details.append(f"with qualifications in {doctor.qualification}")

        # Specialization
        details.append(f"specializing in {doctor.specialization.name}")

        # Consultation fee
        details.append(f"The consultation fee is {doctor.consultation_fee} rupees")

        # Combine details naturally
        if len(details) == 4:
            return f"{details[0]} {details[1]}, {details[2]}. {details[3]}."
        elif len(details) == 3:
            return f"{details[0]}, {details[1]}. {details[2]}."
        else:
            return ". ".join(details) + "."

    def _check_doctor_comprehensive_availability(self, doctor, urgency_level):
        """
        Comprehensive availability check for doctor
        Checks schedules, leaves, and current bookings
        """
        from doctors.models import DoctorLeave
        from django.utils import timezone

        today = timezone.now().date()

        # Check if doctor is on leave
        on_leave = DoctorLeave.objects.filter(
            doctor=doctor,
            start_date__lte=today,
            end_date__gte=today
        ).exists()

        if on_leave:
            return {
                'available': False,
                'reason': 'on_leave',
                'message': f"Dr. {doctor.name} is currently on leave"
            }

        # Check schedule availability
        has_schedule = doctor.schedules.filter(is_active=True).exists()

        if not has_schedule:
            return {
                'available': False,
                'reason': 'no_schedule',
                'message': f"Dr. {doctor.name} doesn't have an active schedule"
            }

        return {
            'available': True,
            'reason': 'available',
            'message': f"Dr. {doctor.name} is available"
        }

    # ========== AI-Powered Helper Methods ==========

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
            name_parts = doctor.name.lower().split()
            first_name = name_parts[0] if name_parts else ""
            last_name = name_parts[-1] if len(name_parts) > 1 else ""

            if cleaned == doctor_name_lower:
                score = 100
            elif cleaned == first_name or (last_name and cleaned == last_name):
                score = 95
            elif doctor_name_lower in cleaned or cleaned in doctor_name_lower:
                score = 90
            elif first_name in cleaned or (last_name and last_name in cleaned):
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
        """Check if user is confirming a suggested doctor"""
        message_lower = message.lower()

        # Check for confirmation words
        if any(word in message_lower for word in ['yes', 'okay', 'ok', 'sure', 'book', 'confirm']):
            suggested_doctors = session_data.get('suggested_doctors', [])
            if suggested_doctors:
                # Confirm first suggested doctor
                doctor_id = suggested_doctors[0]['id']
                return Doctor.objects.get(id=doctor_id)

        # Check if they mentioned a doctor name from suggestions
        suggested_doctors = session_data.get('suggested_doctors', [])
        for doc_info in suggested_doctors:
            if doc_info['name'].lower() in message_lower:
                return Doctor.objects.get(id=doc_info['id'])

        return None

    def _parse_date_with_ai(self, message):
        """Parse date using AI + existing parser"""
        # First try the existing parser
        parsed = self.date_parser.parse_date(message)
        if parsed:
            return parsed

        # If that fails, use AI
        try:
            model = genai.GenerativeModel(self.gemini_model)
            today = timezone.now().date()
            prompt = f"""Today's date is {today.strftime('%Y-%m-%d')} ({today.strftime('%A, %B %d, %Y')}).

Extract the date from this message: "{message}"

Return the date in YYYY-MM-DD format ONLY. If no valid date found, return "NOT_FOUND".

Examples:
- "tomorrow" → {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
- "next monday" → (calculate next Monday from today)
- "december 15" → 2025-12-15 (or 2024-12-15 if before today's date, use 2025)
- "15th" → (assume current month/next month)

Date:"""

            response = model.generate_content(prompt)
            result = response.text.strip()

            if result == "NOT_FOUND":
                return None

            # Parse YYYY-MM-DD format
            return datetime.strptime(result, '%Y-%m-%d').date()

        except Exception as e:
            print(f"AI date parsing error: {e}")
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
        """Detect if user is confirming or wanting to change"""
        message_lower = message.lower().strip()

        confirm_words = ['yes', 'correct', 'confirm', 'book', 'okay', 'ok', 'sure', 'right', 'perfect']
        change_words = ['no', 'change', 'wrong', 'different', 'modify', 'update', 'fix']

        if any(word in message_lower for word in confirm_words):
            return 'confirm'
        elif any(word in message_lower for word in change_words):
            return 'change'
        else:
            return 'unclear'

    # ========== Intent Handlers ==========

    def _handle_cancellation(self, session_data):
        """Handle booking cancellation"""
        session_data['stage'] = 'completed'
        return {
            'message': "I understand. Your booking has been cancelled. If you'd like to book an appointment later, just come back anytime. Is there anything else I can help you with?",
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
        """Handle requests to change doctor/date/time"""
        change_type = intent.get('intent')

        if change_type == 'change_doctor':
            session_data['stage'] = 'doctor_selection'
            session_data.pop('doctor_id', None)
            session_data.pop('doctor_name', None)
            return {
                'message': "No problem! Which doctor would you like to book with instead? You can tell me their name or describe your symptoms.",
                'stage': 'doctor_selection',
                'data': session_data,
                'action': 'continue'
            }
        elif change_type == 'change_date':
            session_data['stage'] = 'date_selection'
            session_data.pop('appointment_date', None)
            return {
                'message': "Sure! What date would you prefer for your appointment?",
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
            return {
                'message': f"Of course! Here are the available times: {time_options}. Which time works better for you?",
                'stage': 'time_selection',
                'data': session_data,
                'action': 'continue'
            }

        return {
            'message': "What would you like to change?",
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
        """Create appointment in database with comprehensive details"""
        try:
            doctor = Doctor.objects.get(id=session_data['doctor_id'])
            appointment_date = datetime.fromisoformat(session_data['appointment_date']).date()

            time_str = session_data['appointment_time']
            appointment_time = datetime.strptime(time_str, '%I:%M %p').time()

            # Get symptoms and booking type
            symptoms = session_data.get('symptoms_description', 'Not specified')
            booking_type = session_data.get('booking_type', 'Routine Checkup')
            urgency_level = session_data.get('urgency_level', 'routine')

            # Add urgency note to symptoms if high priority
            if urgency_level in ['emergency', 'high_priority']:
                symptoms = f"[{urgency_level.upper()}] {symptoms}"

            appointment = Appointment.objects.create(
                doctor=doctor,
                patient_name=session_data['patient_name'],
                patient_phone=session_data['phone'],
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                symptoms=symptoms,
                notes=f"Booking Type: {booking_type}. Booked via voice assistant by Senior Booking Specialist.",
                status='confirmed',
                session_id=self.session_id
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
