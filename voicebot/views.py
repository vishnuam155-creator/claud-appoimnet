"""
VoiceBot REST API Views - Pure API for Voice Assistant
Gemini 2.5 Flash-powered natural conversational appointment booking

This module provides REST API endpoints for voice-based appointment booking.
No template rendering - pure JSON API for frontend integration.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
from django.utils import timezone
import json
import uuid

from voicebot.voice_assistant_manager import VoiceAssistantManager


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
            # Handle empty request body
            if not request.body or request.body.strip() == b'':
                return JsonResponse({
                    'success': False,
                    'error': 'Empty request body',
                    'message': 'Please send a valid JSON request. Example: {"message": "hello", "session_id": "123"}'
                }, status=400)

            # Check content type to determine parsing method
            content_type = request.META.get('CONTENT_TYPE', '').lower()

            # Support both JSON and form data
            if 'application/json' in content_type:
                # Parse JSON data
                try:
                    data = json.loads(request.body)
                    message = data.get('message', '')
                    session_id = data.get('session_id')
                    session_data = data.get('session_data', {})
                except json.JSONDecodeError as e:
                    print(f"VoiceBot JSON decode error: {e}, Body: {request.body[:100]}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid JSON format',
                        'message': 'Please send valid JSON data. Example: {"message": "I have a headache", "session_id": "voice_123"}'
                    }, status=400)

            elif 'multipart/form-data' in content_type or 'application/x-www-form-urlencoded' in content_type:
                # Parse form data (from frontend FormData or form submission)
                message = request.POST.get('message') or request.POST.get('text', '')
                session_id = request.POST.get('session_id')
                session_data = {}

                # Try to parse session_data if provided as JSON string
                session_data_str = request.POST.get('session_data')
                if session_data_str:
                    try:
                        session_data = json.loads(session_data_str)
                    except:
                        session_data = {}

            else:
                # Try JSON first, then form data as fallback
                try:
                    data = json.loads(request.body)
                    message = data.get('message', '')
                    session_id = data.get('session_id')
                    session_data = data.get('session_data', {})
                except:
                    # Fallback to form data
                    message = request.POST.get('message') or request.POST.get('text', '')
                    session_id = request.POST.get('session_id')
                    session_data = {}

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
        """Return comprehensive API information and usage guide"""
        return JsonResponse({
            'success': True,
            'message': 'Voice Assistant REST API - Google Gemini 2.5 Flash powered natural conversational booking',
            'version': '2.0',
            'timestamp': timezone.now().isoformat(),
            'api_info': {
                'ai_model': 'Google Gemini 2.5 Flash',
                'endpoint': '/voicebot/api/',
                'method': 'POST',
                'content_type': 'application/json',
                'authentication': 'None (can be added)',
                'rate_limit': 'No limit (can be configured)'
            },
            'request_format': {
                'message': {
                    'type': 'string',
                    'required': True,
                    'description': 'User voice input transcribed to text',
                    'example': 'I have a headache'
                },
                'session_id': {
                    'type': 'string',
                    'required': False,
                    'description': 'Session identifier for conversation continuity (auto-generated if not provided)',
                    'example': 'voice_1234567890'
                },
                'session_data': {
                    'type': 'object',
                    'required': False,
                    'description': 'Conversation context (managed automatically)',
                    'example': {}
                }
            },
            'response_format': {
                'success': 'boolean - Operation success status',
                'session_id': 'string - Session identifier',
                'message': 'string - AI response message (for TTS)',
                'stage': 'string - Current conversation stage',
                'action': 'string - Action type (continue/booking_complete/error)',
                'data': 'object - Session data and context'
            },
            'features': [
                'Natural language understanding with Gemini 2.5 Flash AI',
                'Intelligent doctor matching by name or symptoms',
                'Smart date/time parsing (supports natural language)',
                'Context-aware multi-turn conversation flow',
                'Intent detection and automatic correction handling',
                'Mid-conversation symptom change detection',
                'Complete appointment booking workflow',
                'Real-time availability checking',
                'Session-based conversation memory',
                'Error recovery and retry mechanisms'
            ],
            'conversation_stages': [
                {'stage': 'greeting', 'description': 'Initial welcome', 'collects': 'None'},
                {'stage': 'patient_name', 'description': 'Patient name collection', 'collects': 'patient_name'},
                {'stage': 'doctor_selection', 'description': 'Doctor selection by name or symptoms', 'collects': 'doctor_id, doctor_name'},
                {'stage': 'date_selection', 'description': 'Appointment date selection', 'collects': 'appointment_date'},
                {'stage': 'time_selection', 'description': 'Time slot selection', 'collects': 'appointment_time'},
                {'stage': 'phone_collection', 'description': 'Contact number collection', 'collects': 'phone'},
                {'stage': 'confirmation', 'description': 'Final confirmation', 'collects': 'None'},
                {'stage': 'completed', 'description': 'Booking completed', 'collects': 'appointment_id'}
            ],
            'example_usage': {
                'step_1_start_conversation': {
                    'request': {
                        'url': '/voicebot/api/',
                        'method': 'POST',
                        'body': {
                            'message': '',
                            'session_id': None
                        }
                    },
                    'response': {
                        'success': True,
                        'session_id': 'voice_1234567890',
                        'message': 'Hello! Welcome to MediCare Clinic...',
                        'stage': 'patient_name',
                        'action': 'continue'
                    }
                },
                'step_2_provide_name': {
                    'request': {
                        'message': 'My name is John',
                        'session_id': 'voice_1234567890'
                    },
                    'response': {
                        'success': True,
                        'message': 'Nice to meet you, John! How can I help you today?',
                        'stage': 'doctor_selection',
                        'action': 'continue'
                    }
                },
                'step_3_describe_symptoms': {
                    'request': {
                        'message': 'I have a severe headache',
                        'session_id': 'voice_1234567890'
                    },
                    'response': {
                        'success': True,
                        'message': 'Based on your symptoms, I recommend Dr. Smith, our Neurologist...',
                        'stage': 'doctor_selection',
                        'action': 'continue'
                    }
                }
            },
            'frontend_integration': {
                'speech_recognition': 'Use Web Speech API (SpeechRecognition)',
                'text_to_speech': 'Use Web Speech API (SpeechSynthesis)',
                'recommended_libraries': [
                    'react-speech-recognition (React)',
                    'vue-speech (Vue.js)',
                    'Web Speech API (Vanilla JS)'
                ],
                'cors_enabled': True,
                'allowed_origins': ['http://localhost:3000', 'http://localhost:8080']
            },
            'error_handling': {
                'invalid_json': 'Returns 400 with error message',
                'missing_message': 'Returns 400 with error message',
                'ai_processing_error': 'Returns 500 with user-friendly message',
                'session_expired': 'Auto-creates new session'
            }
        })
