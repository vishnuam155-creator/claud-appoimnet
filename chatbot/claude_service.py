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
        Uses intelligent keyword matching first, then AI as backup
        """
        specializations = Specialization.objects.all()

        # STEP 1: Try keyword-based matching first (more reliable)
        keyword_match = self._match_by_keywords(symptoms_text, specializations)
        if keyword_match and keyword_match['confidence'] == 'high':
            print(f"[Keyword Match] Found: {keyword_match['specialization']} (Score: {keyword_match.get('score', 0)})")
            return keyword_match

        # STEP 2: If no strong keyword match, use AI
        spec_info = "\n".join([
            f"- {spec.name}: {spec.keywords or spec.description}"
            for spec in specializations
        ])

        prompt = f"""You are a medical assistant helping patients find the right doctor.

Available Specializations with keywords:
{spec_info}

Patient says: "{symptoms_text}"

Analyze the symptoms and determine which specialization would be most appropriate by matching keywords.
Return your response in JSON format with this structure:
{{
    "specialization": "exact name of the specialization",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation of why this specialization is recommended"
}}

IMPORTANT: Match keywords carefully. For example:
- "leg pain" should match Orthopedic (keywords: leg pain, bone, fracture, joint, back pain)
- "chest pain" should match Cardiologist (keywords: chest pain, heart, blood pressure)
- Only suggest "General Physician" if symptoms are general like fever, cold, flu

Be precise with keyword matching.
"""

        try:
            model = genai.GenerativeModel(self.model)
            response = model.generate_content(prompt)

            response_text = response.text.strip()

            # Try to parse JSON
            try:
                # Clean up markdown formatting if present
                if response_text.startswith('```json'):
                    response_text = response_text.split('```json')[1].split('```')[0].strip()
                elif response_text.startswith('```'):
                    response_text = response_text.split('```')[1].split('```')[0].strip()

                result = json.loads(response_text)

                # If AI result differs from keyword match, prefer keyword match if it exists
                if keyword_match and keyword_match['specialization'] != result['specialization']:
                    print(f"[AI vs Keyword Mismatch] AI: {result['specialization']}, Keyword: {keyword_match['specialization']}")
                    # Prefer keyword match if it has medium confidence or higher
                    if keyword_match.get('score', 0) > 0:
                        print(f"[Using Keyword Match] {keyword_match['specialization']}")
                        return keyword_match

                return result
            except json.JSONDecodeError:
                # Fallback parsing if JSON fails
                for spec in specializations:
                    if spec.name.lower() in response_text.lower():
                        return {
                            "specialization": spec.name,
                            "confidence": "medium",
                            "reasoning": "Matched from AI response"
                        }

                # Last resort: use keyword match if available
                if keyword_match:
                    return keyword_match

                return {
                    "specialization": "General Physician",
                    "confidence": "low",
                    "reasoning": "Default recommendation"
                }

        except Exception as e:
            print(f"Error calling Gemini API: {str(e)}")
            # If AI fails but we have keyword match, use it
            if keyword_match:
                return keyword_match

            return {
                "specialization": "General Physician",
                "confidence": "low",
                "reasoning": "Error in AI analysis, using default"
            }

    def _match_by_keywords(self, symptoms_text, specializations):
        """
        Match symptoms to specialization using keyword matching
        Returns the best match with a confidence score
        """
        symptoms_lower = symptoms_text.lower()

        # Common medical words that shouldn't be matched in isolation
        common_words = {'pain', 'hurt', 'ache', 'problem', 'issue', 'feel', 'feeling', 'have', 'had', 'get', 'getting'}

        # Score each specialization based on keyword matches
        matches = []
        for spec in specializations:
            if not spec.keywords:
                continue

            keywords = [kw.strip().lower() for kw in spec.keywords.split(',')]
            score = 0
            matched_keywords = []

            for keyword in keywords:
                # Check for exact phrase match (highest priority)
                if keyword in symptoms_lower:
                    score += 3  # Higher score for exact match
                    matched_keywords.append(keyword)
                else:
                    # Check for partial word match (only for meaningful words)
                    keyword_words = set(keyword.split())
                    symptoms_words = set(symptoms_lower.split())

                    # Find matching words that are not common/generic
                    meaningful_matches = keyword_words & symptoms_words - common_words

                    if meaningful_matches:
                        score += 1  # Lower score for partial match
                        matched_keywords.append(keyword)

            if score > 0:
                matches.append({
                    'specialization': spec.name,
                    'score': score,
                    'matched_keywords': matched_keywords,
                    'total_keywords': len(keywords)
                })

        # Sort by score (descending)
        matches.sort(key=lambda x: x['score'], reverse=True)

        if not matches:
            return None

        # Get best match
        best_match = matches[0]

        # Determine confidence based on score
        if best_match['score'] >= 3:
            confidence = 'high'
        elif best_match['score'] >= 2:
            confidence = 'medium'
        else:
            confidence = 'low'

        return {
            'specialization': best_match['specialization'],
            'confidence': confidence,
            'reasoning': f"Matched keywords: {', '.join(best_match['matched_keywords'][:3])}",
            'score': best_match['score']
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
        Intelligently detect user intent: proceed, change, go_back, clarify
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
5. "go_back" - Wanting to go back to a previous step
6. "clarify" - Asking for clarification or help
7. "cancel" - Wanting to cancel the booking

Look for phrases like:
- "actually", "wait", "no", "change", "different", "instead", "wrong"
- "go back", "previous", "earlier step"
- "not that one", "other option"

Return ONLY a JSON object:
{{
    "intent": "proceed|change_doctor|change_date|change_time|go_back|clarify|cancel",
    "confidence": "high|medium|low",
    "extracted_value": "the value they want to change to, if any",
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
