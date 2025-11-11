import anthropic
from django.conf import settings
from doctors.models import Specialization, Doctor
import json
import google.generativeai as genai
from django.conf import settings
from doctors.models import Specialization
import json


class ClaudeService:
    """
    Service to interact with Google Gemini AI for chatbot conversations
    Enhanced with intelligent intent detection and context awareness
    """

    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "gemini-2.5-flash"

    def analyze_symptoms(self, symptoms_text):
        """
        Analyze patient symptoms and suggest appropriate doctor specialization
        Optimized for voice input with common transcription errors
        """
        specializations = Specialization.objects.all()
        spec_info = "\n".join([
            f"- {spec.name}: {spec.description or spec.keywords}"
            for spec in specializations
        ])

        prompt = f"""You are an expert medical triage assistant helping patients find the right doctor specialization.

IMPORTANT: The patient's input may come from voice transcription, so there might be:
- Casual/conversational language (e.g., "leg pain", "my leg hurts", "pain in leg")
- Transcription errors or incomplete sentences
- Simple symptom descriptions without medical terms
- Multiple symptoms mentioned together

Available Specializations in our system:
{spec_info}

Patient's symptoms (from voice input): "{symptoms_text}"

YOUR TASK:
1. Analyze the symptoms carefully, considering voice transcription patterns
2. Match to the MOST appropriate specialization from the list above
3. Be flexible with matching - "leg pain" = Orthopedic, "heart" = Cardiology, etc.
4. If uncertain, default to "General Physician"

Return ONLY valid JSON (no markdown, no extra text):
{{
    "specialization": "exact specialization name from the list above",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation in one sentence"
}}

Examples:
- "leg pain" → {{"specialization": "Orthopedic", "confidence": "high", "reasoning": "Leg pain indicates musculoskeletal issue"}}
- "fever and cough" → {{"specialization": "General Physician", "confidence": "high", "reasoning": "Common flu symptoms"}}
- "chest pain" → {{"specialization": "Cardiology", "confidence": "high", "reasoning": "Chest pain requires cardiac evaluation"}}
"""

        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)

            response_text = response.text.strip()
            print(f"[GEMINI] Raw response: {response_text[:200]}")

            # Clean up response - remove markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()

            # Remove any leading/trailing whitespace
            response_text = response_text.strip()

            # Try to parse JSON
            try:
                result = json.loads(response_text)
                print(f"[GEMINI] Parsed result: {result}")
                return result
            except json.JSONDecodeError as je:
                print(f"[GEMINI] JSON decode error: {je}")
                # Fallback: try to extract specialization from text
                for spec in specializations:
                    if spec.name.lower() in response_text.lower():
                        print(f"[GEMINI] Found specialization in text: {spec.name}")
                        return {
                            "specialization": spec.name,
                            "confidence": "medium",
                            "reasoning": "Matched from AI response"
                        }

                print(f"[GEMINI] No match found, using default")
                return {
                    "specialization": "General Physician",
                    "confidence": "low",
                    "reasoning": "Default recommendation"
                }

        except Exception as e:
            print(f"[GEMINI] API Error: {str(e)}")
            import traceback
            print(f"[GEMINI] Traceback: {traceback.format_exc()}")
            return {
                "specialization": "General Physician",
                "confidence": "low",
                "reasoning": "Error in AI analysis, using default"
            }

    def generate_conversational_response(self, user_message, context):
        """
        Generate conversational chatbot response
        """
        system_prompt = """You are a friendly medical appointment booking assistant. 
Your role is to help patients book appointments with doctors in a natural, conversational way.

Guidelines:
- Be warm, empathetic, and professional
- Keep responses concise and clear
- Guide patients step by step through the booking process
- Acknowledge symptoms before suggesting doctors
- Always confirm information before proceeding
- Use simple, non-medical language
"""

        conversation_history = context.get('conversation_history', [])
        stage = context.get('stage', 'greeting')

        user_prompt = f"""Current booking stage: {stage}
User says: "{user_message}"

{self._get_stage_instruction(stage, context)}"""

        # Build conversation text (Gemini expects a full conversation string)
        conversation_text = system_prompt + "\n\n"
        for msg in conversation_history[-5:]:
            conversation_text += f"{msg['role'].capitalize()}: {msg['content']}\n"
        conversation_text += f"User: {user_prompt}\nAssistant:"

        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(conversation_text)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating Gemini response: {str(e)}")
            return "I'm sorry, I'm having trouble processing your request. Could you try again?"

    def _get_stage_instruction(self, stage, context):
        """Get specific stage instructions"""
        instructions = {
            'greeting': "Welcome the patient and ask how you can help them book an appointment.",
            'symptoms': "Ask about their symptoms or health concern to help find the right doctor.",
            'doctor_selection': f"Available doctors: {context.get('doctors', [])}. Help them choose.",
            'date_selection': "Show available dates and help them pick one.",
            'time_selection': "Show available time slots for the selected date.",
            'details': "Collect patient details: full name, phone number, email (optional).",
            'confirmation': "Confirm all booking details and provide the booking ID."
        }
        return instructions.get(stage, "")

    def extract_information(self, text, info_type):
        """
        Extract name, phone, email, or age from user text
        """
        prompt = f"""Extract the {info_type} from this text: "{text}"

Return ONLY the {info_type} value, nothing else. If not found, return "NOT_FOUND"."""

        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            result = response.text.strip()
            return None if result == "NOT_FOUND" else result
        except Exception as e:
            print(f"Error extracting {info_type}: {str(e)}")
            return None

    def detect_intent(self, user_message, current_stage, conversation_context):
        """
        Intelligently detect user intent: proceed, change, go_back, clarify, correction
        This makes the bot understand corrections and changes naturally
        """
        prompt = f"""You are analyzing a patient's message in a medical appointment booking conversation.

Current Stage: {current_stage}
Current Context: {json.dumps(conversation_context, indent=2)}

Patient's Message: "{user_message}"

Analyze the patient's intent. They might be:
1. "proceed" - Providing requested information normally
2. "change_doctor" - Wanting to change the selected doctor
3. "change_date" - Wanting to change the selected date
4. "change_time" - Wanting to change the selected time
5. "correction" - Correcting previously provided information (name, phone, email, etc.)
6. "go_back" - Wanting to go back to a previous step
7. "clarify" - Asking for clarification or help
8. "cancel" - Wanting to cancel the booking

Look for correction patterns like:
- "sorry, [field] is [value]" (e.g., "sorry name is vishnu", "sorry my name is vishnu")
- "actually, [field] is [value]" (e.g., "actually my phone is 1234567890")
- "no, [field] is [value]" (e.g., "no my name is john")
- "change [field] to [value]" (e.g., "change name to vishnu")
- "update [field] to [value]" (e.g., "update phone to 1234567890")
- "correction: [field] is [value]"
- Just providing a corrected value after realizing a mistake

For "change_X" intents, look for phrases like:
- "different doctor", "another doctor", "change doctor"
- "different date", "another date", "change date"
- "different time", "another time", "change time"

For "go_back", look for:
- "go back", "previous", "earlier step", "back"

For "cancel", look for:
- "cancel", "stop", "nevermind", "forget it", "don't want"

Return ONLY a JSON object:
{{
    "intent": "proceed|change_doctor|change_date|change_time|correction|go_back|clarify|cancel",
    "confidence": "high|medium|low",
    "extracted_value": "the value they want to change to, if any",
    "field": "name|phone|email|null (only for correction intent)",
    "reasoning": "brief explanation"
}}"""

        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            result_text = response.text.strip()

            # Clean up response (remove markdown formatting)
            if result_text.startswith('```json'):
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif result_text.startswith('```'):
                result_text = result_text.split('```')[1].split('```')[0].strip()

            result = json.loads(result_text)
            return result
        except Exception as e:
            print(f"Error detecting intent: {str(e)}")
            # Default to proceed
            return {
                "intent": "proceed",
                "confidence": "low",
                "extracted_value": None,
                "field": None,
                "reasoning": "Error in detection, defaulting to proceed"
            }

    def generate_contextual_response(self, user_message, intent, stage, context):
        """
        Generate intelligent contextual response based on detected intent
        """
        system_prompt = """You are an intelligent medical appointment booking assistant.
You can understand when patients want to change their mind, correct information, or go back.

Guidelines:
- Be empathetic and understanding when patients change their mind
- Confirm what they want to change before proceeding
- Use natural, conversational language
- Be concise but friendly
- Always acknowledge their intent before acting on it
"""

        prompt = f"""Current Stage: {stage}
Patient's Intent: {intent['intent']} (Confidence: {intent['confidence']})
Reasoning: {intent['reasoning']}

Current Booking Context:
{json.dumps(context, indent=2)}

Patient says: "{user_message}"

Generate a helpful, natural response that:
1. Acknowledges their intent
2. Confirms what they want to do
3. Guides them to the next step

Keep it conversational and brief (2-3 sentences max)."""

        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(system_prompt + "\n\n" + prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating contextual response: {str(e)}")
            return "I understand. Let me help you with that."
