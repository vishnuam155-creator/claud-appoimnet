"""
Voice Provider API Views
Handles voice provider selection and configuration
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from chatbot.ai4bharat_voice_service import get_ai4bharat_service
from chatbot.voice_service import VoiceService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class VoiceProviderConfigView(APIView):
    """
    API endpoint to get and set voice provider configuration
    """

    def get(self, request):
        """Get current voice provider configuration"""
        try:
            current_provider = getattr(settings, 'VOICE_PROVIDER', 'browser')

            # Get available providers
            available_providers = [
                {
                    'id': 'browser',
                    'name': 'Browser Speech API',
                    'description': 'Built-in browser speech recognition (Free)',
                    'languages': ['en-IN', 'hi-IN', 'en-US'],
                    'enabled': True
                },
                {
                    'id': 'google',
                    'name': 'Google Cloud Speech',
                    'description': 'Google Cloud Speech-to-Text and TTS',
                    'languages': ['en-IN', 'hi-IN', 'en-US', 'ta-IN', 'te-IN'],
                    'enabled': getattr(settings, 'USE_GOOGLE_CLOUD_SPEECH', False)
                },
                {
                    'id': 'ai4bharat',
                    'name': 'AI4Bharat',
                    'description': 'Indian language AI models for speech',
                    'languages': ['hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa', 'en'],
                    'enabled': bool(getattr(settings, 'AI4BHARAT_API_KEY', ''))
                }
            ]

            return Response({
                'current_provider': current_provider,
                'available_providers': available_providers,
                'asterisk_enabled': getattr(settings, 'ASTERISK_ENABLED', False)
            })

        except Exception as e:
            logger.error(f"Error getting voice provider config: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Set voice provider"""
        try:
            provider = request.data.get('provider')

            if not provider:
                return Response(
                    {'error': 'Provider is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate provider
            valid_providers = ['browser', 'google', 'ai4bharat']
            if provider not in valid_providers:
                return Response(
                    {'error': f'Invalid provider. Must be one of: {", ".join(valid_providers)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Check if provider is available
            if provider == 'google' and not getattr(settings, 'USE_GOOGLE_CLOUD_SPEECH', False):
                return Response(
                    {'error': 'Google Cloud Speech is not configured'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if provider == 'ai4bharat' and not getattr(settings, 'AI4BHARAT_API_KEY', ''):
                return Response(
                    {'error': 'AI4Bharat API key is not configured'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Store in session (for web-based usage)
            request.session['voice_provider'] = provider

            logger.info(f"Voice provider set to: {provider}")

            return Response({
                'success': True,
                'provider': provider,
                'message': f'Voice provider set to {provider}'
            })

        except Exception as e:
            logger.error(f"Error setting voice provider: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AI4BharatLanguageView(APIView):
    """
    API endpoint to get supported languages for AI4Bharat
    """

    def get(self, request):
        """Get supported languages"""
        try:
            ai4bharat_service = get_ai4bharat_service()
            languages = ai4bharat_service.get_supported_languages()

            return Response({
                'languages': languages,
                'default_language': getattr(settings, 'AI4BHARAT_DEFAULT_LANGUAGE', 'hi')
            })

        except Exception as e:
            logger.error(f"Error getting AI4Bharat languages: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AI4BharatSpeechToTextView(APIView):
    """
    API endpoint for AI4Bharat speech-to-text conversion
    """

    def post(self, request):
        """Convert speech to text"""
        try:
            audio_data = request.FILES.get('audio')
            language = request.data.get('language', 'hi')

            if not audio_data:
                return Response(
                    {'error': 'Audio file is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get AI4Bharat service
            ai4bharat_service = get_ai4bharat_service()

            # Convert speech to text
            result = ai4bharat_service.speech_to_text(
                audio_data.read(),
                language=language
            )

            if result['success']:
                return Response({
                    'success': True,
                    'transcript': result['transcript'],
                    'confidence': result.get('confidence', 0.0),
                    'language': result.get('language', language)
                })
            else:
                return Response(
                    {'error': result.get('error', 'Speech recognition failed')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Error in AI4Bharat STT: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AI4BharatTextToSpeechView(APIView):
    """
    API endpoint for AI4Bharat text-to-speech conversion
    """

    def post(self, request):
        """Convert text to speech"""
        try:
            text = request.data.get('text')
            language = request.data.get('language', 'hi')
            voice_gender = request.data.get('voice_gender', 'female')

            if not text:
                return Response(
                    {'error': 'Text is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get AI4Bharat service
            ai4bharat_service = get_ai4bharat_service()

            # Convert text to speech
            result = ai4bharat_service.text_to_speech(
                text,
                language=language,
                voice_gender=voice_gender
            )

            if result['success']:
                from django.http import HttpResponse

                # Return audio file
                response = HttpResponse(
                    result['audio_data'],
                    content_type='audio/wav'
                )
                response['Content-Disposition'] = 'attachment; filename="speech.wav"'
                return response
            else:
                return Response(
                    {'error': result.get('error', 'Text-to-speech failed')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Error in AI4Bharat TTS: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class VoiceProviderTestView(APIView):
    """
    API endpoint to test voice provider connectivity
    """

    def post(self, request):
        """Test voice provider"""
        try:
            provider = request.data.get('provider', 'browser')

            test_results = {
                'provider': provider,
                'timestamp': None,
                'tests': []
            }

            if provider == 'ai4bharat':
                ai4bharat_service = get_ai4bharat_service()

                # Test TTS
                tts_result = ai4bharat_service.text_to_speech(
                    "Hello, this is a test",
                    language='en'
                )

                test_results['tests'].append({
                    'name': 'Text-to-Speech',
                    'success': tts_result['success'],
                    'error': tts_result.get('error', None)
                })

            elif provider == 'google':
                voice_service = VoiceService()

                # Test if Google Cloud is configured
                test_results['tests'].append({
                    'name': 'Configuration Check',
                    'success': getattr(settings, 'USE_GOOGLE_CLOUD_SPEECH', False),
                    'error': None if getattr(settings, 'USE_GOOGLE_CLOUD_SPEECH', False)
                    else 'Google Cloud Speech not enabled'
                })

            elif provider == 'browser':
                test_results['tests'].append({
                    'name': 'Browser API',
                    'success': True,
                    'error': None,
                    'message': 'Browser-based speech API is always available'
                })

            from datetime import datetime
            test_results['timestamp'] = datetime.now().isoformat()

            return Response(test_results)

        except Exception as e:
            logger.error(f"Error testing voice provider: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
