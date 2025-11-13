"""
Asterisk Telephony API Views
Handles incoming and outgoing calls through Asterisk PBX
"""

import logging
import json
import base64
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse

from voicebot.asterisk_telephony_service import get_asterisk_service
from voicebot.voice_assistant_manager import VoiceAssistantManager
from chatbot.ai4bharat_voice_service import get_ai4bharat_service
from chatbot.voice_service import VoiceService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AsteriskIncomingCallView(APIView):
    """
    API endpoint for Asterisk incoming calls (ARI)
    This endpoint is called by Asterisk when a new call arrives
    """

    def post(self, request):
        """Handle incoming call from Asterisk"""
        try:
            if not getattr(settings, 'ASTERISK_ENABLED', False):
                return Response(
                    {'error': 'Asterisk integration is not enabled'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Get call details from Asterisk
            channel_id = request.data.get('channel_id')
            caller_id = request.data.get('caller_id')
            call_type = request.data.get('type', 'incoming')

            if not channel_id or not caller_id:
                return Response(
                    {'error': 'channel_id and caller_id are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            logger.info(f"Asterisk incoming call: {caller_id} on channel {channel_id}")

            # Get Asterisk service
            asterisk_service = get_asterisk_service()

            # Handle the call
            result = asterisk_service.handle_incoming_call_ari(channel_id, caller_id)

            if result['success']:
                return Response({
                    'success': True,
                    'session_id': result['session_id'],
                    'channel_id': result['channel_id'],
                    'message': 'Call connected successfully'
                })
            else:
                return Response(
                    {'error': result.get('error', 'Failed to handle call')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Error handling incoming call: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AsteriskCallProcessView(APIView):
    """
    API endpoint to process audio from Asterisk call
    Receives audio, transcribes, processes with voicebot, and returns response
    """

    def post(self, request):
        """Process audio from Asterisk call"""
        try:
            if not getattr(settings, 'ASTERISK_ENABLED', False):
                return Response(
                    {'error': 'Asterisk integration is not enabled'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Get request data
            session_id = request.data.get('session_id')
            audio_data = request.FILES.get('audio')
            language = request.data.get('language', 'en-IN')
            voice_provider = request.data.get('voice_provider',
                                            getattr(settings, 'VOICE_PROVIDER', 'browser'))

            if not session_id:
                return Response(
                    {'error': 'session_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Step 1: Transcribe audio to text
            transcript = ''

            if audio_data:
                if voice_provider == 'ai4bharat':
                    ai4bharat_service = get_ai4bharat_service()
                    stt_result = ai4bharat_service.speech_to_text(
                        audio_data.read(),
                        language=language
                    )
                    if stt_result['success']:
                        transcript = stt_result['transcript']
                    else:
                        logger.error(f"STT failed: {stt_result.get('error')}")
                        transcript = ''

                elif voice_provider == 'google':
                    voice_service = VoiceService()
                    # Implement Google STT here if needed
                    transcript = ''

                else:
                    # Browser-based (not applicable for Asterisk)
                    return Response(
                        {'error': 'Browser-based speech not supported for Asterisk calls'},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Step 2: Process with voicebot
            voice_manager = VoiceAssistantManager()

            # Get session data
            session_data = request.data.get('session_data', {})
            if isinstance(session_data, str):
                session_data = json.loads(session_data)

            voicebot_response = voice_manager.process_voice_message(
                message=transcript,
                session_id=session_id,
                session_data=session_data
            )

            # Step 3: Convert response to speech
            response_text = voicebot_response.get('message', '')
            audio_response = None

            if voice_provider == 'ai4bharat':
                ai4bharat_service = get_ai4bharat_service()
                tts_result = ai4bharat_service.text_to_speech(
                    response_text,
                    language=language
                )
                if tts_result['success']:
                    audio_response = base64.b64encode(tts_result['audio_data']).decode('utf-8')

            # Return response
            return Response({
                'success': True,
                'transcript': transcript,
                'response_text': response_text,
                'audio_response': audio_response,
                'session_data': voicebot_response.get('data', {}),
                'stage': voicebot_response.get('stage', ''),
                'action': voicebot_response.get('action', 'continue')
            })

        except Exception as e:
            logger.error(f"Error processing Asterisk audio: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AsteriskOutboundCallView(APIView):
    """
    API endpoint to initiate outbound calls
    """

    def post(self, request):
        """Make outbound call"""
        try:
            if not getattr(settings, 'ASTERISK_ENABLED', False):
                return Response(
                    {'error': 'Asterisk integration is not enabled'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            phone_number = request.data.get('phone_number')
            message = request.data.get('message', '')

            if not phone_number:
                return Response(
                    {'error': 'phone_number is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get Asterisk service
            asterisk_service = get_asterisk_service()

            # Make outbound call
            result = asterisk_service.make_outbound_call(phone_number, message)

            if result['success']:
                return Response({
                    'success': True,
                    'channel_id': result.get('channel_id'),
                    'phone_number': result.get('phone_number'),
                    'message': 'Outbound call initiated successfully'
                })
            else:
                return Response(
                    {'error': result.get('error', 'Failed to make outbound call')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Error making outbound call: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AsteriskActiveCallsView(APIView):
    """
    API endpoint to get active calls
    """

    def get(self, request):
        """Get active calls"""
        try:
            if not getattr(settings, 'ASTERISK_ENABLED', False):
                return Response(
                    {'error': 'Asterisk integration is not enabled'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Get Asterisk service
            asterisk_service = get_asterisk_service()

            # Get active calls
            active_calls = asterisk_service.get_active_calls()

            return Response({
                'active_calls': active_calls,
                'count': len(active_calls)
            })

        except Exception as e:
            logger.error(f"Error getting active calls: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AsteriskEndCallView(APIView):
    """
    API endpoint to end a call
    """

    def post(self, request):
        """End call"""
        try:
            if not getattr(settings, 'ASTERISK_ENABLED', False):
                return Response(
                    {'error': 'Asterisk integration is not enabled'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            session_id = request.data.get('session_id')

            if not session_id:
                return Response(
                    {'error': 'session_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get Asterisk service
            asterisk_service = get_asterisk_service()

            # End the call
            success = asterisk_service.end_call(session_id)

            if success:
                return Response({
                    'success': True,
                    'message': 'Call ended successfully'
                })
            else:
                return Response(
                    {'error': 'Call not found or already ended'},
                    status=status.HTTP_404_NOT_FOUND
                )

        except Exception as e:
            logger.error(f"Error ending call: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class AsteriskWebhookView(APIView):
    """
    Webhook endpoint for Asterisk events
    Receives events from Asterisk ARI WebSocket
    """

    def post(self, request):
        """Handle Asterisk webhook event"""
        try:
            event_type = request.data.get('type')
            event_data = request.data.get('data', {})

            logger.info(f"Asterisk webhook event: {event_type}")

            # Handle different event types
            if event_type == 'StasisStart':
                # New channel entered the application
                channel_id = event_data.get('channel', {}).get('id')
                caller_id = event_data.get('channel', {}).get('caller', {}).get('number')

                logger.info(f"New channel started: {channel_id} from {caller_id}")

            elif event_type == 'StasisEnd':
                # Channel left the application
                channel_id = event_data.get('channel', {}).get('id')
                logger.info(f"Channel ended: {channel_id}")

            elif event_type == 'ChannelDtmfReceived':
                # DTMF digit received
                channel_id = event_data.get('channel', {}).get('id')
                digit = event_data.get('digit')
                logger.info(f"DTMF received on {channel_id}: {digit}")

            return Response({
                'success': True,
                'message': 'Event received'
            })

        except Exception as e:
            logger.error(f"Error handling Asterisk webhook: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
