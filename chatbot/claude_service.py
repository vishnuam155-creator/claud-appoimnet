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
    """

    def __init__(self):
        # Configure Gemini API
        genai.configure(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "gemini-2.5-flash"

    def analyze_symptoms(self, symptoms_text):
        """
        Analyze patient symptoms and suggest appropriate doctor specialization
        """
        specializations = Specialization.objects.all()
        spec_info = "\n".join([
            f"- {spec.name}: {spec.description or spec.keywords}"
            for spec in specializations
        ])

        prompt = f"""You are a medical assistant helping patients find the right doctor.

Available Specializations:
{spec_info}

Patient says: "{symptoms_text}"

Analyze the symptoms and determine which specialization would be most appropriate.
Return your response in JSON format with this structure:
{{
    "specialization": "exact name of the specialization",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation of why this specialization is recommended"
}}

If no clear match, suggest "General Physician" as default.
"""

        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)

            response_text = response.text.strip()

            # Try to parse JSON
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                for spec in specializations:
                    if spec.name.lower() in response_text.lower():
                        return {
                            "specialization": spec.name,
                            "confidence": "medium",
                            "reasoning": "Matched from AI response"
                        }

                return {
                    "specialization": "General Physician",
                    "confidence": "low",
                    "reasoning": "Default recommendation"
                }

        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
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
