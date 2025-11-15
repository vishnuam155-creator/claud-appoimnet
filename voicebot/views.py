"""
VoiceBot Views - AI-Powered Voice Assistant for Medical Appointments
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
import json
import uuid

from voicebot.voice_assistant_manager import VoiceAssistantManager


def voice_assistant_page(request):
    """
    Render the voice assistant interface
    Gemini 2.5 Flash-powered natural conversational appointment booking
    """
    return render(request, 'voicebot/voice_assistant.html')


@method_decorator(csrf_exempt, name='dispatch')
class VoiceAssistantAPIView(View):
    """
    API endpoint for voice assistant conversation
    Pure voice-based booking flow with Gemini AI intelligence
    """

    # Store sessions in memory (in production, use Django cache or Redis)
    sessions = {}

    def post(self, request):
        """Process voice message and return AI-powered response"""
        try:
            data = json.loads(request.body)
            message = data.get('message', '')
            session_id = data.get('session_id')
            session_data = data.get('session_data', {})

            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())

            # Get or create session data
            if session_id not in self.sessions:
                self.sessions[session_id] = {
                    'stage': 'greeting',
                    'data': {}
                }

            # Update session with provided data
            if session_data:
                self.sessions[session_id].update(session_data)

            # Process message through voice assistant manager (Gemini AI)
            manager = VoiceAssistantManager(session_id)
            response = manager.process_voice_message(message, self.sessions[session_id])

            # Update session
            self.sessions[session_id] = response['data']

            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'message': response['message'],
                'stage': response['stage'],
                'action': response['action'],
                'data': response['data']
            })

        except Exception as e:
            import traceback
            print(f"Voice assistant error: {e}")
            print(traceback.format_exc())

            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Sorry, I encountered an error. Could you please repeat that?'
            }, status=500)

    def get(self, request):
        """Return API info"""
        return JsonResponse({
            'message': 'Voice Assistant API - Google Gemini 2.5 Flash powered natural conversational booking',
            'version': '2.0',
            'ai_model': 'Google Gemini 2.5 Flash',
            'endpoint': '/voicebot/api/',
            'method': 'POST',
            'required_fields': {
                'message': 'User voice input (string)',
                'session_id': 'Session identifier (optional, auto-generated)',
                'session_data': 'Conversation context (optional, managed automatically)'
            },
            'features': [
                '🤖 Natural language understanding with Gemini 2.5 Flash AI',
                '👨‍⚕️ Intelligent doctor matching by name or symptoms',
                '📅 Smart date/time parsing (supports natural language)',
                '💬 Context-aware multi-turn conversation flow',
                '🎯 Intent detection and automatic correction handling',
                '🔄 Mid-conversation symptom change detection',
                '📱 Complete appointment booking workflow',
                '✅ Real-time availability checking'
            ],
            'conversation_stages': [
                'greeting', 'patient_name', 'doctor_selection',
                'date_selection', 'time_selection', 'phone_collection',
                'confirmation', 'completed'
            ],
            'example_request': {
                'message': 'I have a headache',
                'session_id': 'voice_1234567890'
            }
        })
