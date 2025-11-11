from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
import json
import uuid
import base64
from chatbot.conversation_manager import ConversationManager
from chatbot.voice_service import voice_service


def chatbot_page(request):
    """Render the chatbot interface"""
    return render(request, 'patient_booking/chatbot.html')


def voice_assistant_page(request):
    """Render the voice AI assistant interface"""
    return render(request, 'patient_booking/voice_assistant.html')


@method_decorator(csrf_exempt, name='dispatch')
class ChatbotAPIView(View):
    """
    API endpoint for chatbot conversation
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '')
            session_id = data.get('session_id')
            
            # Generate session ID if not provided
            if not session_id:
                session_id = str(uuid.uuid4())
            
            # Process message through conversation manager
            manager = ConversationManager(session_id)
            response = manager.process_message(user_message)
            
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'message': response['message'],
                'action': response['action'],
                'options': response.get('options'),
                'booking_id': response.get('booking_id'),
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'Sorry, something went wrong. Please try again.'
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


def home(request):
    """Home page"""
    return render(request, 'patient_booking/home.html')
