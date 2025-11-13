"""
Enhanced Voice Assistant Manager - Optimized for Continuous Flow
Fixes:
1. Extended availability search (30 → 90 days)
2. Alternative doctor suggestions when no availability
3. Better symptom context switching
4. Improved conversation flow
5. Graceful fallbacks
"""

# This file provides fixes for voice_assistant_manager.py

# ============================================================================
# FIX 1: Extended Availability Search (90 days instead of 30)
# ============================================================================

def _find_next_available_date_enhanced(self, doctor_id, start_date, max_days=90):
    """
    Find next available date for doctor with extended search range

    Args:
        doctor_id: Doctor ID
        start_date: Starting date for search
        max_days: Maximum days to search ahead (default: 90)

    Returns:
        Next available date or None
    """
    current_date = start_date + timedelta(days=1)
    max_date = start_date + timedelta(days=max_days)

    # Track checked dates for reporting
    checked_dates = 0

    while current_date <= max_date:
        slots = self._get_available_slots(doctor_id, current_date)
        if any(slot['available'] for slot in slots):
            return current_date
        current_date += timedelta(days=1)
        checked_dates += 1

    return None


# ============================================================================
# FIX 2: Alternative Doctor Suggestions When No Availability
# ============================================================================

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
    from doctors.models import Doctor
    from datetime import datetime, timedelta

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
        # Check next available date for each doctor
        next_date = self._find_next_available_date_enhanced(doctor.id, date_from, max_days=30)

        if next_date:
            doctors_with_availability.append({
                'id': doctor.id,
                'name': doctor.name,
                'fee': doctor.consultation_fee,
                'next_available': next_date,
                'days_away': (next_date - date_from).days
            })

    # Sort by soonest availability
    doctors_with_availability.sort(key=lambda x: x['days_away'])

    return doctors_with_availability


# ============================================================================
# FIX 3: Enhanced Date Selection with Better No-Availability Handling
# ============================================================================

def _handle_date_selection_ai_enhanced(self, message, session_data):
    """
    Enhanced date selection with better handling of no availability
    Offers alternative doctors when current doctor is fully booked
    """

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

    if not doctor_id and session_data.get('suggested_doctors'):
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
        # ENHANCED: Try to find next available date (90 days search)
        next_available = self._find_next_available_date_enhanced(
            doctor_id,
            parsed_date,
            max_days=90
        )

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
            # ENHANCED: No availability found - suggest alternative doctors
            doctor_name = session_data.get('doctor_name', 'this doctor')

            # Get alternative doctors
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
                        alt_msg += f"{idx}. Dr. {alt['name']} - Available {days_text} ({alt['next_available'].strftime('%B %d')}), "
                        alt_msg += f"consultation fee {alt['fee']} rupees\n"

                    alt_msg += "\nWhich doctor would you like to book with? You can say the doctor's name or number."

                    # Store alternatives for easy selection
                    session_data['alternative_doctors'] = alternatives
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
                        'message': f"I apologize, but Dr. {doctor_name} and other {specialization_name} doctors are fully booked for the next few months. Would you like to consider a different type of specialist, or shall I take your contact information for a callback when slots open up?",
                        'stage': 'date_selection',
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

    # Slots available - proceed normally
    session_data['appointment_date'] = parsed_date.isoformat()
    session_data['available_slots'] = available_slots
    session_data['stage'] = 'time_selection'

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


# ============================================================================
# FIX 4: Detect and Handle Symptom Changes After Doctor Selection
# ============================================================================

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
    symptom_phrases = ['i have', 'i feel', 'i am', 'my ', 'got ', 'experiencing']
    has_symptom_phrase = any(phrase in message_lower for phrase in symptom_phrases)

    return has_symptoms and has_symptom_phrase


def _handle_mid_conversation_symptom_change(self, message, session_data):
    """
    Handle when user mentions new symptoms after already selecting a doctor
    """
    current_doctor_name = session_data.get('doctor_name', 'the current doctor')

    response_msg = f"I hear you mentioning new symptoms. Just to make sure we're booking you with the right specialist, "
    response_msg += f"would you like me to re-evaluate which doctor is best for you, or would you still prefer to continue with Dr. {current_doctor_name}? "
    response_msg += "You can say 'find new doctor' or 'continue with current doctor'."

    session_data['awaiting_doctor_reconfirmation'] = True
    session_data['new_symptoms'] = message

    return {
        'message': response_msg,
        'stage': session_data.get('stage', 'doctor_selection'),
        'data': session_data,
        'action': 'continue'
    }


# ============================================================================
# FIX 5: Enhanced Intent Detection with Symptom Change Handling
# ============================================================================

def process_voice_message_enhanced(self, message, session_data):
    """
    Enhanced voice message processing with better symptom change detection
    """
    current_stage = session_data.get('stage', 'greeting')

    # Check for symptom changes after doctor selection
    if current_stage in ['date_selection', 'time_selection', 'phone_collection'] and message:
        if self._detect_symptom_change(message, current_stage):
            # User is mentioning new symptoms - offer to reconsider doctor
            return self._handle_mid_conversation_symptom_change(message, session_data)

    # Check if waiting for doctor reconfirmation
    if session_data.get('awaiting_doctor_reconfirmation'):
        message_lower = message.lower()

        if any(keyword in message_lower for keyword in ['new doctor', 'different doctor', 'another doctor', 're-evaluate', 'find doctor']):
            # User wants to find a new doctor based on symptoms
            session_data.pop('awaiting_doctor_reconfirmation', None)
            session_data.pop('doctor_id', None)
            session_data.pop('doctor_name', None)
            session_data['stage'] = 'doctor_selection'

            symptom_message = session_data.pop('new_symptoms', message)
            return self._analyze_symptoms_and_suggest_ai(symptom_message, session_data)

        elif any(keyword in message_lower for keyword in ['continue', 'current', 'same', 'yes', 'okay', 'ok']):
            # User wants to continue with current doctor
            session_data.pop('awaiting_doctor_reconfirmation', None)
            session_data.pop('new_symptoms', None)

            return {
                'message': f"Alright, let's continue with Dr. {session_data.get('doctor_name')}. What date would you prefer for your appointment?",
                'stage': 'date_selection',
                'data': session_data,
                'action': 'continue'
            }

    # Detect user intent using AI
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
        'date_selection': self._handle_date_selection_ai_enhanced,  # Use enhanced version
        'time_selection': self._handle_time_selection_ai,
        'phone_collection': self._handle_phone_collection_ai,
        'confirmation': self._handle_confirmation_ai,
    }

    handler = handlers.get(current_stage, self._handle_greeting)
    return handler(message, session_data)


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

"""
To apply these fixes to voice_assistant_manager.py:

1. Replace the existing `_find_next_available_date` method with `_find_next_available_date_enhanced`

2. Add the new method `_get_alternative_doctors_with_availability`

3. Replace the existing `_handle_date_selection_ai` method with `_handle_date_selection_ai_enhanced`

4. Add the new methods:
   - `_detect_symptom_change`
   - `_handle_mid_conversation_symptom_change`

5. Replace the existing `process_voice_message` method with `process_voice_message_enhanced`

These changes will:
- Extend availability search from 30 to 90 days
- Suggest alternative doctors when current doctor is unavailable
- Handle symptom changes gracefully after doctor selection
- Improve continuous conversation flow
- Prevent the conversation from getting stuck
"""
