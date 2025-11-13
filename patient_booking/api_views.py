from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import uuid
import base64
from chatbot.conversation_manager import ConversationManager
from chatbot.voice_service import voice_service
from chatbot.voice_assistant_manager import VoiceAssistantManager


class ChatbotAPIView(APIView):
    """
    REST API endpoint for chatbot conversation

    POST /api/chatbot/
    {
        "message": "I have a headache",
        "session_id": "optional-uuid"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Process chatbot message"""
        try:
            user_message = request.data.get('message', '')
            session_id = request.data.get('session_id')

            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())

            # Process message through conversation manager
            manager = ConversationManager(session_id)
            response = manager.process_message(user_message)

            return Response({
                'success': True,
                'session_id': session_id,
                'message': response['message'],
                'action': response['action'],
                'options': response.get('options'),
                'booking_id': response.get('booking_id'),
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Sorry, something went wrong. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """Return API info"""
        return Response({
            'message': 'Chatbot API - Use POST method to send messages',
            'endpoint': '/api/chatbot/',
            'required_fields': ['message', 'session_id (optional)'],
            'example': {
                'message': 'I have a headache',
                'session_id': 'optional-uuid'
            }
        })


class VoiceAPIView(APIView):
    """
    REST API endpoint for voice interactions
    Handles speech-to-text and text-to-speech requests

    POST /api/voice/
    {
        "action": "transcribe|synthesize|voice_guidance",
        "audio_data": "base64-encoded-audio",  // for transcribe
        "text": "text to speak",  // for synthesize
        "language": "en-IN"  // optional
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Handle voice transcription and synthesis requests"""
        try:
            action = request.data.get('action')  # 'transcribe', 'synthesize', or 'voice_guidance'

            if action == 'transcribe':
                # Handle speech-to-text
                audio_data_base64 = request.data.get('audio_data')
                audio_format = request.data.get('audio_format', 'webm')

                if not audio_data_base64:
                    return Response({
                        'success': False,
                        'error': 'No audio data provided'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Decode base64 audio
                audio_data = base64.b64decode(audio_data_base64)

                # Transcribe audio
                result = voice_service.transcribe_audio(audio_data, audio_format)

                return Response(result)

            elif action == 'synthesize':
                # Handle text-to-speech
                text = request.data.get('text')
                language_code = request.data.get('language', 'en-IN')

                if not text:
                    return Response({
                        'success': False,
                        'error': 'No text provided'
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Synthesize speech
                result = voice_service.synthesize_speech(text, language_code)

                return Response(result)

            elif action == 'voice_guidance':
                # Get voice guidance for a specific stage
                stage = request.data.get('stage', 'greeting')
                guidance = voice_service.get_voice_guidance(stage)

                return Response({
                    'success': True,
                    'guidance': guidance
                })

            else:
                return Response({
                    'success': False,
                    'error': 'Invalid action. Use "transcribe", "synthesize", or "voice_guidance"'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Voice processing error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """Return voice API info"""
        return Response({
            'message': 'Voice API - Use POST method for voice operations',
            'endpoint': '/api/voice/',
            'actions': {
                'transcribe': {
                    'description': 'Convert speech to text',
                    'required': ['audio_data'],
                    'optional': ['audio_format']
                },
                'synthesize': {
                    'description': 'Convert text to speech',
                    'required': ['text'],
                    'optional': ['language']
                },
                'voice_guidance': {
                    'description': 'Get voice guidance for a stage',
                    'optional': ['stage']
                }
            },
            'supported_languages': ['en-IN', 'hi-IN', 'en-US']
        })


class VoiceAssistantAPIView(APIView):
    """
    REST API endpoint for voice assistant conversation
    Pure voice-based booking flow without UI elements

    POST /api/voice-assistant/
    {
        "message": "I want to book an appointment",
        "session_id": "optional-uuid",
        "session_data": {}  // optional
    }
    """
    permission_classes = [AllowAny]

    # Store sessions in memory (in production, use Django cache or Redis)
    sessions = {}

    def post(self, request):
        try:
            message = request.data.get('message', '')
            session_id = request.data.get('session_id')
            session_data = request.data.get('session_data', {})

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

            return Response({
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

            return Response({
                'success': False,
                'error': str(e),
                'message': 'Sorry, I encountered an error. Could you please repeat that?'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """Return API info"""
        return Response({
            'message': 'Voice Assistant API - Use POST method to interact',
            'endpoint': '/api/voice-assistant/',
            'required_fields': ['message'],
            'optional_fields': ['session_id', 'session_data'],
            'example': {
                'message': 'I want to book an appointment',
                'session_id': 'optional-uuid'
            }
        })
