"""
Voice Intelligence Service
Converts voice inputs to structured JSON actions and generates natural language responses from DB results.
"""

import json
import re
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import google.generativeai as genai
from django.conf import settings

# Configure Gemini AI
genai.configure(api_key=settings.ANTHROPIC_API_KEY)


class VoiceIntelligenceService:
    """
    Voice Intelligence Assistant that:
    1. Understands voice inputs (with error correction and mixed language support)
    2. Identifies user intent
    3. Converts to structured JSON actions for database operations
    4. Generates natural language responses from database results
    """

    def __init__(self, clinic_name: str = "MedCare Clinic"):
        self.clinic_name = clinic_name
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    # ========================
    # VOICE UNDERSTANDING & CORRECTION
    # ========================

    def understand_voice_input(self, voice_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Corrects and understands voice input with mixed language support.

        Args:
            voice_text: Raw voice input (may have errors, mixed languages)
            context: Current conversation context (stage, collected info, etc.)

        Returns:
            {
                "corrected_text": "cleaned and corrected text",
                "detected_language": "en/hi/ta/ml/mixed",
                "extracted_entities": {...},
                "confidence": "high/medium/low"
            }
        """
        context_str = json.dumps(context or {}, indent=2)

        prompt = f"""
You are a Voice Intelligence Assistant. Analyze this voice input and correct any errors.

VOICE INPUT: "{voice_text}"

CONTEXT: {context_str}

TASK:
1. Correct spelling mistakes, unclear audio, incomplete speech
2. Convert Indian-style English/Malayalam/Tamil/Hindi mixed speech to standard English
3. Extract entities: names, phone numbers, dates, times, doctor names, symptoms
4. Assess confidence level

Return JSON:
{{
    "corrected_text": "cleaned text in proper English",
    "detected_language": "en/hi/ta/ml/mixed",
    "extracted_entities": {{
        "name": "if present",
        "phone": "if present (10 digits)",
        "date": "if present",
        "time": "if present",
        "doctor_name": "if present",
        "symptoms": ["list of symptoms if present"]
    }},
    "confidence": "high/medium/low",
    "needs_clarification": false
}}
"""

        try:
            response = self.model.generate_content(prompt)
            result = self._extract_json_from_response(response.text)
            return result
        except Exception as e:
            # Fallback: return original text with low confidence
            return {
                "corrected_text": voice_text,
                "detected_language": "unknown",
                "extracted_entities": {},
                "confidence": "low",
                "needs_clarification": True
            }

    # ========================
    # INTENT IDENTIFICATION
    # ========================

    def identify_intent(self, voice_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Identifies user intent from voice input.

        Returns:
            {
                "intent": "appointment_booking/appointment_lookup/appointment_cancel/
                           appointment_reschedule/general_query/support_request",
                "sub_intent": "create/modify/confirm/check_status",
                "confidence": "high/medium/low",
                "requires_database": true/false
            }
        """
        context_str = json.dumps(context or {}, indent=2)

        prompt = f"""
You are a Voice Intelligence Assistant. Identify the user's intent.

USER SPEECH: "{voice_text}"
CONTEXT: {context_str}

INTENTS:
- appointment_booking: User wants to book/create new appointment
- appointment_lookup: User wants to check existing appointment
- appointment_cancel: User wants to cancel appointment
- appointment_reschedule: User wants to change appointment date/time
- doctor_query: User asking about doctors/specialists
- general_query: General questions about clinic/services
- support_request: User needs help/clarification

Return JSON:
{{
    "intent": "primary_intent",
    "sub_intent": "specific action if applicable",
    "confidence": "high/medium/low",
    "requires_database": true/false,
    "extracted_params": {{
        "key": "value pairs relevant to intent"
    }}
}}
"""

        try:
            response = self.model.generate_content(prompt)
            result = self._extract_json_from_response(response.text)
            return result
        except Exception as e:
            return {
                "intent": "unknown",
                "sub_intent": None,
                "confidence": "low",
                "requires_database": False,
                "extracted_params": {}
            }

    # ========================
    # DATABASE ACTION GENERATION
    # ========================

    def generate_database_action(
        self,
        intent: Dict[str, Any],
        understood_input: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Converts intent and extracted information into structured database action.

        Returns JSON action format:
        {
            "action": "query_database",
            "query_type": "appointment_lookup/create_appointment/check_availability/...",
            "parameters": {...}
        }
        """
        intent_type = intent.get('intent', 'unknown')
        entities = understood_input.get('extracted_entities', {})
        intent_params = intent.get('extracted_params', {})

        # Merge entities and intent params
        all_params = {**entities, **intent_params}

        # Map intent to query type
        query_type_mapping = {
            'appointment_booking': 'create_appointment',
            'appointment_lookup': 'appointment_lookup',
            'appointment_cancel': 'cancel_appointment',
            'appointment_reschedule': 'reschedule_appointment',
            'doctor_query': 'get_doctors',
            'general_query': None,  # No DB needed
            'support_request': None
        }

        query_type = query_type_mapping.get(intent_type)

        if not query_type or not intent.get('requires_database'):
            # No database action needed - generate direct response
            return {
                "action": "respond",
                "query_type": None,
                "parameters": None,
                "direct_response": self._generate_general_response(
                    intent_type,
                    understood_input.get('corrected_text')
                )
            }

        # Build database action
        db_action = {
            "action": "query_database",
            "query_type": query_type,
            "parameters": self._format_parameters(query_type, all_params, context)
        }

        return db_action

    def _format_parameters(
        self,
        query_type: str,
        raw_params: Dict[str, Any],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Format parameters based on query type requirements.
        """
        formatted = {}
        context = context or {}

        if query_type == 'create_appointment':
            formatted = {
                "patient_name": raw_params.get('name') or context.get('patient_name'),
                "phone": self._clean_phone(raw_params.get('phone') or context.get('phone')),
                "doctor_name": raw_params.get('doctor_name') or context.get('doctor_name'),
                "doctor_id": context.get('doctor_id'),
                "date": self._parse_date(raw_params.get('date') or context.get('appointment_date')),
                "time": self._parse_time(raw_params.get('time') or context.get('appointment_time')),
                "symptoms": raw_params.get('symptoms', [])
            }

        elif query_type == 'appointment_lookup':
            formatted = {
                "phone": self._clean_phone(raw_params.get('phone')),
                "name": raw_params.get('name'),
                "appointment_id": raw_params.get('appointment_id')
            }

        elif query_type == 'cancel_appointment':
            formatted = {
                "appointment_id": raw_params.get('appointment_id') or context.get('appointment_id'),
                "phone": self._clean_phone(raw_params.get('phone')) or context.get('phone')
            }

        elif query_type == 'reschedule_appointment':
            formatted = {
                "appointment_id": raw_params.get('appointment_id') or context.get('appointment_id'),
                "phone": self._clean_phone(raw_params.get('phone')) or context.get('phone'),
                "new_date": self._parse_date(raw_params.get('date')),
                "new_time": self._parse_time(raw_params.get('time'))
            }

        elif query_type == 'get_doctors':
            formatted = {
                "doctor_name": raw_params.get('doctor_name'),
                "specialization": raw_params.get('specialization'),
                "symptoms": raw_params.get('symptoms', [])
            }

        # Remove None values
        formatted = {k: v for k, v in formatted.items() if v is not None}

        return formatted

    # ========================
    # NATURAL LANGUAGE RESPONSE GENERATION
    # ========================

    def generate_voice_response(
        self,
        db_result: Dict[str, Any],
        query_type: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Converts database results into natural, conversational voice response.

        Args:
            db_result: Database query result
            query_type: Type of query that was executed
            context: Conversation context

        Returns:
            Natural language text suitable for voice output
        """
        status = db_result.get('status', 'error')

        if status == 'success':
            return self._generate_success_response(db_result, query_type, context)
        elif status == 'error':
            return self._generate_error_response(db_result, query_type)
        else:
            return self._generate_default_response(db_result, query_type)

    def _generate_success_response(
        self,
        db_result: Dict[str, Any],
        query_type: str,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate success response based on query type."""

        data = db_result.get('data', {})

        if query_type == 'create_appointment':
            return self._format_appointment_confirmation(data)

        elif query_type == 'appointment_lookup':
            return self._format_appointment_details(data)

        elif query_type == 'cancel_appointment':
            return f"Your appointment has been cancelled successfully. Is there anything else I can help you with?"

        elif query_type == 'reschedule_appointment':
            new_date = data.get('new_date', '')
            new_time = data.get('new_time', '')
            return f"Perfect! I've rescheduled your appointment to {new_date} at {new_time}. You'll receive a confirmation message shortly."

        elif query_type == 'get_doctors':
            return self._format_doctor_list(data)

        else:
            message = db_result.get('message', 'Operation completed successfully.')
            return f"{message} How else can I assist you today?"

    def _format_appointment_confirmation(self, data: Dict[str, Any]) -> str:
        """Format appointment booking confirmation."""
        doctor_name = data.get('doctor_name', 'the doctor')
        date = data.get('appointment_date', '')
        time = data.get('appointment_time', '')
        patient_name = data.get('patient_name', '')
        booking_id = data.get('booking_id', '')

        response = f"Excellent news, {patient_name}! Your appointment with Dr. {doctor_name} is confirmed for "
        response += f"{self._format_date_naturally(date)} at {time}. "

        if booking_id:
            response += f"Your booking ID is {booking_id}. "

        response += "You'll receive a confirmation message on your phone. Is there anything else I can help you with?"

        return response

    def _format_appointment_details(self, data: Dict[str, Any]) -> str:
        """Format appointment lookup details."""
        if isinstance(data, list) and len(data) > 0:
            appointments = data
            if len(appointments) == 1:
                apt = appointments[0]
                doctor = apt.get('doctor_name', 'the doctor')
                date = apt.get('appointment_date', '')
                time = apt.get('appointment_time', '')
                status = apt.get('status', 'scheduled')

                return f"I found your appointment with Dr. {doctor} on {self._format_date_naturally(date)} at {time}. The status is {status}. Would you like to reschedule or cancel this appointment?"
            else:
                response = f"I found {len(appointments)} appointments for you. "
                for i, apt in enumerate(appointments[:3], 1):
                    doctor = apt.get('doctor_name', 'the doctor')
                    date = apt.get('appointment_date', '')
                    response += f"{i}. Dr. {doctor} on {self._format_date_naturally(date)}. "
                return response + "Which one would you like to know more about?"
        else:
            return "I couldn't find any appointments with that information. Would you like to book a new appointment?"

    def _format_doctor_list(self, data: Dict[str, Any]) -> str:
        """Format list of available doctors."""
        doctors = data.get('doctors', [])

        if not doctors:
            return "I'm sorry, I couldn't find any doctors matching your requirements. Would you like me to suggest our general physicians?"

        if len(doctors) == 1:
            doctor = doctors[0]
            name = doctor.get('name', '')
            specialization = doctor.get('specialization', '')
            return f"I found Dr. {name}, who is our {specialization} specialist. Would you like to book an appointment with Dr. {name}?"
        else:
            response = f"I found {len(doctors)} doctors for you. "
            for i, doctor in enumerate(doctors[:3], 1):
                name = doctor.get('name', '')
                specialization = doctor.get('specialization', '')
                response += f"{i}. Dr. {name}, {specialization}. "
            return response + "Which doctor would you prefer?"

    def _generate_error_response(self, db_result: Dict[str, Any], query_type: str) -> str:
        """Generate friendly error response."""
        error_message = db_result.get('message', 'Something went wrong')

        # Friendly error mapping
        if 'not found' in error_message.lower():
            return "I'm sorry, I couldn't find that information. Could you please provide more details?"
        elif 'invalid' in error_message.lower():
            return "It seems there's an issue with the information provided. Could you please repeat that?"
        elif 'unavailable' in error_message.lower():
            return "I'm sorry, that time slot is not available. Would you like me to suggest alternative times?"
        else:
            return f"I apologize, but I encountered an issue: {error_message}. Let me help you with that another way."

    def _generate_default_response(self, db_result: Dict[str, Any], query_type: str) -> str:
        """Generate default response."""
        message = db_result.get('message', 'I processed your request.')
        return f"{message} Is there anything else you need help with?"

    def _generate_general_response(self, intent_type: str, user_text: str) -> str:
        """Generate response for non-database queries."""

        if intent_type == 'general_query':
            return f"Thank you for asking about {self.clinic_name}. How can I assist you with your appointment today?"
        elif intent_type == 'support_request':
            return "I'm here to help you! You can book appointments, check existing bookings, or reschedule. What would you like to do?"
        else:
            return "I'm listening. How can I help you with your medical appointment today?"

    # ========================
    # UTILITY FUNCTIONS
    # ========================

    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """Extract JSON from AI response text."""
        try:
            # Try direct JSON parse
            return json.loads(text)
        except:
            # Try to find JSON in text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass

        # Return empty dict if parsing fails
        return {}

    def _clean_phone(self, phone: Optional[str]) -> Optional[str]:
        """Extract and clean 10-digit phone number."""
        if not phone:
            return None

        # Remove all non-digits
        digits = re.sub(r'\D', '', str(phone))

        # Return 10-digit number
        if len(digits) == 10:
            return digits
        elif len(digits) == 11 and digits.startswith('1'):
            return digits[1:]
        elif len(digits) > 10:
            return digits[-10:]

        return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format."""
        if not date_str:
            return None

        # If already in correct format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            return date_str

        # Try various date formats
        formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%m/%d/%Y',
            '%B %d, %Y', '%b %d, %Y', '%d %B %Y', '%d %b %Y'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d')
            except:
                continue

        return None

    def _parse_time(self, time_str: Optional[str]) -> Optional[str]:
        """Parse time string to HH:MM AM/PM format."""
        if not time_str:
            return None

        # If already in correct format
        if re.match(r'^\d{1,2}:\d{2}\s*(AM|PM)$', time_str, re.IGNORECASE):
            return time_str.upper()

        # Try various time formats
        formats = [
            '%I:%M %p', '%I:%M%p', '%H:%M', '%I %p', '%I%p'
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt.strftime('%I:%M %p')
            except:
                continue

        return None

    def _format_date_naturally(self, date_str: str) -> str:
        """Convert date to natural language (e.g., 'tomorrow', 'Monday, Nov 14')."""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.now().date()
            date_only = date_obj.date()

            if date_only == today:
                return "today"
            elif date_only == today + timedelta(days=1):
                return "tomorrow"
            elif date_only == today + timedelta(days=2):
                return "day after tomorrow"
            else:
                return date_obj.strftime('%A, %B %d')
        except:
            return date_str

    # ========================
    # CLARIFICATION QUESTIONS
    # ========================

    def generate_clarification_question(
        self,
        missing_info: list,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Generate natural clarification question for missing information.

        Args:
            missing_info: List of missing fields (e.g., ['phone', 'date'])
            context: Current conversation context

        Returns:
            Natural language clarification question
        """
        if not missing_info:
            return "Is there anything else I can help you with?"

        # Map fields to natural questions
        questions = {
            'name': "May I have your name, please?",
            'phone': "Could you please provide your phone number?",
            'date': "What date would you prefer for your appointment?",
            'time': "What time works best for you?",
            'doctor_name': "Which doctor would you like to see?",
            'appointment_id': "Could you provide your appointment ID or booking number?"
        }

        # Get first missing field
        field = missing_info[0]
        return questions.get(field, f"Could you please provide your {field}?")
