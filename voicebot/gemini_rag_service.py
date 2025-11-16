"""
Gemini RAG Service - LLM-powered appointment booking with Retrieval-Augmented Generation
Uses Gemini 2.5 Flash with full conversation context and database retrieval
"""

import google.generativeai as genai
from django.conf import settings
import json
from datetime import datetime, timedelta
from django.utils import timezone


class GeminiRAGService:
    """
    Enhanced Gemini service with RAG capabilities for natural appointment booking
    Acts as a senior booking receptionist with full context awareness
    """

    def __init__(self):
        genai.configure(api_key=settings.ANTHROPIC_API_KEY)
        self.model_name = "gemini-2.5-flash"
        self.model = genai.GenerativeModel(
            self.model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 1024,
            }
        )

    def generate_response_with_context(self, user_message, conversation_history, context, current_stage):
        """
        Generate natural response using RAG pattern

        Args:
            user_message: Current user input
            conversation_history: List of previous messages
            context: Retrieved context from database (doctors, slots, etc.)
            current_stage: Current conversation stage

        Returns:
            Dict with response message and extracted information
        """
        # Build comprehensive prompt with RAG context
        system_prompt = self._build_system_prompt()
        context_prompt = self._build_context_prompt(context)
        conversation_prompt = self._build_conversation_prompt(conversation_history)
        task_prompt = self._build_task_prompt(current_stage, context, user_message)

        full_prompt = f"""{system_prompt}

{context_prompt}

{conversation_prompt}

{task_prompt}"""

        try:
            response = self.model.generate_content(full_prompt)
            response_text = response.text.strip()

            # Parse response if it contains structured data
            return self._parse_response(response_text)

        except Exception as e:
            print(f"Error generating response: {e}")
            import traceback
            traceback.print_exc()
            return {
                'message': "I apologize, I'm having trouble processing that. Could you please repeat?",
                'action': 'continue',
                'extracted_data': {}
            }

    def _build_system_prompt(self):
        """Build system prompt defining the assistant's role"""
        return """You are MediBot, a senior medical appointment booking receptionist powered by AI.

YOUR ROLE AND PERSONALITY:
- You are warm, empathetic, professional, and highly competent
- You act like an experienced receptionist who has been doing this for years
- You understand patients may change their mind at any time - handle this naturally
- You can handle complex conversations where patients might jump between topics
- You remember the entire conversation and can adapt to any changes
- You are proactive in suggesting alternatives when issues arise
- You explain things clearly and make patients feel comfortable

YOUR CAPABILITIES:
- Book appointments by collecting: patient name, phone number, doctor selection, date, and time
- Understand symptoms and recommend appropriate specialists
- Check real-time slot availability and suggest alternatives
- Handle changes to any booking detail at any stage of conversation
- Answer questions about doctors, availability, and booking process
- Provide helpful suggestions when patients are unsure

CONVERSATION GUIDELINES:
1. Be conversational and natural - not robotic or scripted
2. Use short, clear sentences suitable for voice conversation
3. Always acknowledge what the patient said before asking the next question
4. If patient wants to change something, handle it smoothly without restarting
5. If a slot is unavailable, proactively suggest the next available options
6. Remember the full context - if patient mentioned symptoms earlier, use that information
7. Be flexible - patients may provide information out of order
8. Always confirm critical information before finalizing booking

IMPORTANT: Your responses should sound natural and conversational, as if speaking to someone on the phone."""

    def _build_context_prompt(self, context):
        """Build context from retrieved database information"""
        current_booking = context.get('current_booking', {})

        prompt = "\n--- CURRENT BOOKING CONTEXT ---\n"
        prompt += f"Stage: {current_booking.get('stage', 'greeting')}\n"

        if current_booking.get('patient_name'):
            prompt += f"Patient Name: {current_booking['patient_name']}\n"
        if current_booking.get('doctor_name'):
            prompt += f"Selected Doctor: {current_booking['doctor_name']} (ID: {current_booking.get('doctor_id')})\n"
        if current_booking.get('appointment_date'):
            prompt += f"Selected Date: {current_booking['appointment_date']}\n"
        if current_booking.get('appointment_time'):
            prompt += f"Selected Time: {current_booking['appointment_time']}\n"
        if current_booking.get('phone'):
            prompt += f"Phone: {current_booking['phone']}\n"

        # Add doctor context if available
        if context.get('selected_doctor'):
            doc = context['selected_doctor']
            prompt += f"\n--- SELECTED DOCTOR DETAILS ---\n"
            prompt += f"Name: Dr. {doc['name']}\n"
            prompt += f"Specialization: {doc['specialization']}\n"
            prompt += f"Experience: {doc['experience_years']} years\n"
            prompt += f"Consultation Fee: ₹{doc['consultation_fee']}\n"

        # Add availability context
        if context.get('doctor_availability'):
            prompt += f"\n--- DOCTOR AVAILABILITY (Next 7 days) ---\n"
            for avail in context['doctor_availability'][:5]:
                prompt += f"- {avail['day_name']}, {avail['date']}: {avail['available_slots']} slots available\n"

        # Add slot context if date is selected
        if context.get('available_slots'):
            slots = context['available_slots']
            if slots.get('available'):
                available_times = [s['time'] for s in slots['slots'] if s['available']][:10]
                prompt += f"\n--- AVAILABLE TIME SLOTS ---\n"
                prompt += f"Total Slots: {slots['total_slots']}\n"
                prompt += f"Available: {slots['available_count']}\n"
                if available_times:
                    prompt += f"Times: {', '.join(available_times)}\n"
            else:
                prompt += f"\n--- NO SLOTS AVAILABLE ---\n"
                prompt += f"Reason: {slots.get('reason', 'Unknown')}\n"

        # Add available doctors context
        if context.get('doctors'):
            prompt += f"\n--- AVAILABLE DOCTORS ({len(context['doctors'])} total) ---\n"
            for doc in context['doctors'][:10]:  # Show first 10
                prompt += f"- Dr. {doc['name']} ({doc['specialization']}) - ₹{doc['consultation_fee']}\n"

        # Add specializations context
        if context.get('specializations'):
            prompt += f"\n--- AVAILABLE SPECIALIZATIONS ---\n"
            for spec in context['specializations'][:10]:
                prompt += f"- {spec['name']}: {spec['doctor_count']} doctors available\n"
                if spec.get('keywords'):
                    prompt += f"  Keywords: {spec['keywords'][:100]}\n"

        return prompt

    def _build_conversation_prompt(self, conversation_history):
        """Build conversation history for context"""
        if not conversation_history:
            return "\n--- CONVERSATION HISTORY ---\nThis is the start of the conversation.\n"

        prompt = "\n--- CONVERSATION HISTORY ---\n"
        for msg in conversation_history[-10:]:  # Last 10 messages
            role = msg.get('role', 'user').upper()
            content = msg.get('content', '')
            prompt += f"{role}: {content}\n"

        return prompt

    def _build_task_prompt(self, current_stage, context, user_message):
        """Build task-specific prompt based on current stage"""
        booking = context.get('current_booking', {})

        prompt = f"\n--- CURRENT TASK ---\n"
        prompt += f"Patient says: \"{user_message}\"\n\n"

        # Stage-specific instructions
        stage_instructions = {
            'greeting': """Task: Warmly welcome the patient and ask for their name.
If they already provided their name in their message, acknowledge it and move to asking how you can help.""",

            'patient_name': """Task: Collect the patient's name.
If they provided it, acknowledge and ask how you can help them today (symptoms or doctor name).""",

            'doctor_selection': """Task: Help patient select a doctor.
- If they describe symptoms, analyze and recommend appropriate specialization/doctor
- If they mention doctor name, confirm the doctor details
- If they're selecting from previously suggested doctors, confirm selection
- Use the available doctors and specializations from context
- Be helpful and suggest alternatives if needed""",

            'date_selection': """Task: Help patient select an appointment date.
- Check the doctor availability context
- If date mentioned, validate and show available time slots
- If date not available, suggest next available dates from context
- Handle date parsing naturally (tomorrow, next Monday, specific dates, etc.)""",

            'time_selection': """Task: Help patient select a time slot.
- Use the available_slots context
- If time mentioned, confirm if available
- If not available, suggest alternatives from available slots
- Be helpful with time format (10 AM, 2:30 PM, etc.)""",

            'phone_collection': """Task: Collect patient's 10-digit phone number.
- Validate it's exactly 10 digits
- Be patient if they make mistakes""",

            'confirmation': """Task: Confirm all booking details.
- Summarize: patient name, doctor, date, time, phone
- Ask for final confirmation
- Handle any change requests naturally"""
        }

        prompt += stage_instructions.get(current_stage, "Task: Help the patient with their request.")

        # Add change detection instructions
        prompt += """

IMPORTANT - HANDLING CHANGES:
- Patient can change ANY detail at ANY time (doctor, date, time, name, phone)
- If patient wants to change something, acknowledge it positively and help them
- Examples of change requests:
  * "Actually, I want a different doctor"
  * "Can I change the date to next week?"
  * "Wait, I prefer morning slots"
  * "Let me change my number"
- Handle these naturally without making patient feel they made a mistake

RESPONSE FORMAT:
Provide your response as JSON:
{
  "message": "Your natural, conversational response to the patient (2-3 sentences max)",
  "action": "continue|booking_complete|change_detected|need_info",
  "next_stage": "greeting|patient_name|doctor_selection|date_selection|time_selection|phone_collection|confirmation|completed",
  "extracted_data": {
    "patient_name": "if mentioned (e.g., 'John Smith')",
    "doctor_id": "NUMERIC ID ONLY if doctor is selected (e.g., 5, NOT 'Dr. Smith')",
    "doctor_name": "doctor's name if selected (e.g., 'Dr. Michael Brown')",
    "appointment_date": "YYYY-MM-DD format if mentioned (e.g., '2025-11-17')",
    "appointment_time": "HH:MM AM/PM format if mentioned (e.g., '10:00 AM')",
    "phone": "10-digit number only if mentioned (e.g., '9876543210')",
    "intent": "proceed|change_doctor|change_date|change_time|change_phone|cancel|unclear"
  }
}

CRITICAL FOR doctor_id:
- Look up the doctor's numeric ID from the context above
- ONLY put NUMBERS in doctor_id (e.g., 1, 2, 3)
- NEVER put names in doctor_id (NOT "Dr. Smith", use the ID like 5)
- Put the doctor's NAME in doctor_name field
- If you can't find the numeric ID, omit doctor_id and only provide doctor_name

REMEMBER:
- Keep responses conversational and natural
- Don't be too formal or robotic
- Use contractions (I'm, let's, you're, etc.)
- Be warm and friendly
- Address patient by name when you know it"""

        return prompt

    def _parse_response(self, response_text):
        """Parse LLM response, handling both JSON and plain text"""
        try:
            # Try to extract JSON from response
            if '```json' in response_text:
                json_str = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                json_str = response_text.split('```')[1].split('```')[0].strip()
            elif '{' in response_text and '}' in response_text:
                # Find JSON object
                start = response_text.index('{')
                end = response_text.rindex('}') + 1
                json_str = response_text[start:end]
            else:
                # No JSON found, treat as plain text
                return {
                    'message': response_text,
                    'action': 'continue',
                    'extracted_data': {}
                }

            parsed = json.loads(json_str)

            # Ensure required fields exist
            if 'message' not in parsed:
                parsed['message'] = response_text

            if 'action' not in parsed:
                parsed['action'] = 'continue'

            if 'extracted_data' not in parsed:
                parsed['extracted_data'] = {}

            return parsed

        except Exception as e:
            print(f"Error parsing response: {e}")
            # Return plain text response
            return {
                'message': response_text,
                'action': 'continue',
                'extracted_data': {}
            }

    def analyze_intent(self, user_message, conversation_history, current_booking):
        """
        Analyze user intent to detect changes, cancellations, or clarifications

        Returns:
            Dict with intent analysis
        """
        history_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history[-5:]
        ])

        prompt = f"""Analyze the patient's intent in this booking conversation.

CONVERSATION HISTORY:
{history_text}

CURRENT BOOKING STATE:
{json.dumps(current_booking, indent=2)}

PATIENT SAYS: "{user_message}"

Determine the patient's intent:
- "proceed": Normal flow, providing requested information
- "change_doctor": Wants to change/select different doctor
- "change_date": Wants to change appointment date
- "change_time": Wants to change time slot
- "change_phone": Wants to change phone number
- "change_name": Wants to change their name
- "cancel": Wants to cancel booking
- "clarify": Asking question or needs clarification
- "confirm": Confirming booking details

Return JSON:
{{
  "intent": "one of the above intents",
  "confidence": "high|medium|low",
  "reasoning": "brief explanation",
  "extracted_value": "any new value they mentioned (date, time, doctor name, etc.)"
}}"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Parse JSON
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()

            return json.loads(result_text)

        except Exception as e:
            print(f"Error analyzing intent: {e}")
            return {
                'intent': 'proceed',
                'confidence': 'low',
                'reasoning': 'Error in analysis, defaulting to proceed',
                'extracted_value': None
            }
