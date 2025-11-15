"""
REST API views for Patient Booking
All template-based views have been removed - this is a pure REST API module
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
from datetime import datetime
import json
import uuid
import base64
import logging
import traceback
from chatbot.conversation_manager import ConversationManager
from chatbot.voice_service import voice_service
from chatbot.voice_assistant_manager import VoiceAssistantManager

# Setup logger
logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAPIView(View):
    """
    API endpoint for chatbot conversation
    Enhanced with better error handling and response validation
    """

    def post(self, request):
        try:
            # Parse request body
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid JSON format',
                    'message': 'Please send valid JSON data.'
                }, status=400)

            # Validate required fields
            user_message = data.get('message', '').strip()
            if not user_message:
                return JsonResponse({
                    'success': False,
                    'error': 'Message is required',
                    'message': 'Please provide a message.'
                }, status=400)

            # Get or generate session ID
            session_id = data.get('session_id')
            if not session_id:
                session_id = str(uuid.uuid4())
                logger.info(f"Generated new session ID: {session_id}")
            else:
                logger.info(f"Using existing session ID: {session_id}")

            # Log incoming message
            logger.info(f"[{session_id}] User message: {user_message}")

            # Process message through conversation manager
            try:
                manager = ConversationManager(session_id)
                response = manager.process_message(user_message)
            except Exception as conv_error:
                logger.error(f"Conversation manager error: {conv_error}")
                logger.error(traceback.format_exc())
                return JsonResponse({
                    'success': False,
                    'error': f'Conversation processing error: {str(conv_error)}',
                    'message': 'Sorry, I had trouble processing your message. Please try again.'
                }, status=500)

            # Validate response structure
            if not isinstance(response, dict):
                logger.error(f"Invalid response type: {type(response)}")
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid response format',
                    'message': 'Sorry, something went wrong. Please try again.'
                }, status=500)

            # Ensure required fields exist
            bot_message = response.get('message', 'I apologize, but I encountered an error.')
            action = response.get('action', 'error')
            options = response.get('options', None)
            booking_id = response.get('booking_id', None)
            stage = response.get('stage', None)

            # Log bot response
            logger.info(f"[{session_id}] Bot response: {bot_message[:100]}...")
            logger.info(f"[{session_id}] Action: {action}, Stage: {stage}")

            # Build successful response
            api_response = {
                'success': True,
                'session_id': session_id,
                'message': bot_message,
                'action': action,
                'options': options if options else [],
                'booking_id': booking_id,
                'stage': stage,
                'timestamp': datetime.now().isoformat()
            }

            return JsonResponse(api_response)

        except Exception as e:
            # Catch-all error handler
            logger.error(f"Unexpected error in ChatbotAPIView: {e}")
            logger.error(traceback.format_exc())

            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Sorry, an unexpected error occurred. Please try again or contact support.',
                'session_id': session_id if 'session_id' in locals() else None
            }, status=500)
    
    def get(self, request):
        """Return API info"""
        return JsonResponse({
            'message': 'Chatbot API - Use POST method to send messages',
            'endpoint': '/api/chatbot/',
            'required_fields': ['message', 'session_id (optional)']
        })


@method_decorator(csrf_exempt, name='dispatch')
class VoiceAPIView(View):
    """
    API endpoint for voice interactions
    Handles speech-to-text and text-to-speech requests
    """

    def post(self, request):
        """Handle voice transcription and synthesis requests"""
        try:
            data = json.loads(request.body)
            action = data.get('action')  # 'transcribe' or 'synthesize'

            if action == 'transcribe':
                # Handle speech-to-text
                audio_data_base64 = data.get('audio_data')
                audio_format = data.get('audio_format', 'webm')

                if not audio_data_base64:
                    return JsonResponse({
                        'success': False,
                        'error': 'No audio data provided'
                    }, status=400)

                # Decode base64 audio
                audio_data = base64.b64decode(audio_data_base64)

                # Transcribe audio
                result = voice_service.transcribe_audio(audio_data, audio_format)

                return JsonResponse(result)

            elif action == 'synthesize':
                # Handle text-to-speech
                text = data.get('text')
                language_code = data.get('language', 'en-IN')

                if not text:
                    return JsonResponse({
                        'success': False,
                        'error': 'No text provided'
                    }, status=400)

                # Synthesize speech
                result = voice_service.synthesize_speech(text, language_code)

                return JsonResponse(result)

            elif action == 'voice_guidance':
                # Get voice guidance for a specific stage
                stage = data.get('stage', 'greeting')
                guidance = voice_service.get_voice_guidance(stage)

                return JsonResponse({
                    'success': True,
                    'guidance': guidance
                })

            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action. Use "transcribe", "synthesize", or "voice_guidance"'
                }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Voice processing error'
            }, status=500)

    def get(self, request):
        """Return voice API info"""
        return JsonResponse({
            'message': 'Voice API - Use POST method for voice operations',
            'endpoint': '/api/voice/',
            'actions': ['transcribe', 'synthesize', 'voice_guidance'],
            'supported_languages': ['en-IN', 'hi-IN', 'en-US']
        })


@method_decorator(csrf_exempt, name='dispatch')
class VoiceAssistantAPIView(View):
    """
    API endpoint for voice assistant conversation
    Pure voice-based booking flow without UI elements
    """

    # Store sessions in memory (in production, use Django cache or Redis)
    sessions = {}

    def post(self, request):
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

            # Process message through voice assistant manager
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
            'message': 'Voice Assistant API - Use POST method to interact',
            'endpoint': '/api/voice-assistant/',
            'required_fields': ['message', 'session_id (optional)', 'session_data (optional)']
        })


@csrf_exempt
def chatbot_reset_session(request):
    """
    Reset/clear a chatbot session
    POST: Clear session data
    """
    if request.method == 'POST':
        try:
            from django.core.cache import cache
            data = json.loads(request.body)
            session_id = data.get('session_id')

            if not session_id:
                return JsonResponse({
                    'success': False,
                    'error': 'session_id is required'
                }, status=400)

            # Clear session from cache
            cache_key = f"chat_session_{session_id}"
            cache.delete(cache_key)

            logger.info(f"Session reset: {session_id}")

            return JsonResponse({
                'success': True,
                'message': 'Session cleared successfully',
                'session_id': session_id
            })

        except Exception as e:
            logger.error(f"Error resetting session: {e}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)

    return JsonResponse({
        'message': 'Session Reset API - Use POST method',
        'required_fields': ['session_id']
    })


@csrf_exempt
def chatbot_debug_session(request, session_id):
    """
    Debug endpoint to view session state
    GET: View current session data
    """
    try:
        from django.core.cache import cache

        cache_key = f"chat_session_{session_id}"
        state = cache.get(cache_key)

        if not state:
            return JsonResponse({
                'success': False,
                'message': 'Session not found',
                'session_id': session_id
            }, status=404)

        # Sanitize conversation history (limit to last 10 messages)
        if 'conversation_history' in state:
            state['conversation_history'] = state['conversation_history'][-10:]

        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'state': state,
            'cache_key': cache_key
        })

    except Exception as e:
        logger.error(f"Error debugging session: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
