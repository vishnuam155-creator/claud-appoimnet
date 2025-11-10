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
        Generate conversational chatbot response with empathetic, human-like personality
        """
        system_prompt = """You are a warm, caring senior customer support specialist at a medical clinic.
Your personality is like a helpful, experienced friend who genuinely cares about each patient's wellbeing.

Your Communication Style:
- Speak naturally like a real person having a conversation
- Show genuine empathy and understanding for their health concerns
- Be patient and encouraging, especially if they seem worried
- Use friendly, conversational language (avoid robotic phrases)
- Ask thoughtful follow-up questions to understand their needs better
- Acknowledge their feelings ("I understand that must be concerning")
- Provide reassurance when appropriate
- Remember details they share and reference them naturally

Voice Conversation Guidelines:
- Keep responses brief and clear for voice interaction (2-3 sentences max)
- Speak in a warm, conversational tone
- Use natural speech patterns with occasional verbal nods ("I see", "Got it", "Understood")
- Avoid long lists - present options conversationally
- Confirm information naturally ("So that's John Smith, is that correct?")
- Be patient if they need to correct information

Empathy Examples:
- "I understand how uncomfortable that must be. Let me help you find the right doctor."
- "Don't worry, we'll get you taken care of. I'm here to help."
- "That sounds concerning. I'm glad you're getting it checked out."
- "I appreciate you sharing that. Let's find you a great doctor."
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

    def ask_followup_question(self, symptoms_text):
        """
        Generate intelligent follow-up questions based on symptoms
        This makes the conversation more thorough like a real healthcare professional
        """
        prompt = f"""You are a caring medical assistant speaking with a patient about their symptoms.

Patient's symptoms: "{symptoms_text}"

Based on these symptoms, ask 1-2 brief, natural follow-up questions to better understand their condition.
This helps match them with the right doctor.

Examples of good follow-up questions:
- "How long have you been experiencing this?"
- "Is the pain constant or does it come and go?"
- "Have you noticed any other symptoms?"
- "Does anything make it feel better or worse?"

Keep it conversational, empathetic, and brief (1-2 sentences).
Show you care about getting them the right help.

Your follow-up question:"""

        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating follow-up question: {str(e)}")
            return None

    def generate_contextual_response(self, user_message, intent, stage, context):
        """
        Generate intelligent contextual response based on detected intent
        Enhanced with Gemini-like empathetic understanding
        """
        system_prompt = """You are a caring, intelligent senior customer support specialist.
You understand that patients may change their mind, need to correct information, or feel uncertain.

Your Empathetic Approach:
- Completely normal and okay when they change their mind - never make them feel bad
- Respond with understanding and encouragement ("No problem at all!")
- Acknowledge their feelings if they seem hesitant or worried
- Make the process feel easy and stress-free
- Be patient and supportive, like a good friend helping them
- Use warm, natural language that puts them at ease
- Validate their concerns before moving forward

When They Change Their Mind:
- "No worries at all! Let's find you a different option."
- "Of course! Take all the time you need to decide."
- "Absolutely, I understand. Let me show you other options."

When They Correct Information:
- "Thanks for catching that! Let me update it right away."
- "Got it, I'll fix that for you."
- "No problem! I've corrected that information."

Guidelines:
- Keep responses brief and conversational (voice-friendly)
- Always acknowledge their intent warmly before acting
- Make them feel heard and understood
- Project calm, helpful confidence
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
