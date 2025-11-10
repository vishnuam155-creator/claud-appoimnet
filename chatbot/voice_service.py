"""
Voice Service for Medical Appointment Booking System
Handles Speech-to-Text (STT) and Text-to-Speech (TTS) functionality
"""

import os
import io
import base64
from typing import Dict, Any, Optional, Tuple
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Service to handle voice interactions for appointment booking.
    Supports both Google Cloud Speech API and Web Speech API fallback.
    """

    def __init__(self):
        self.use_google_cloud = getattr(settings, 'USE_GOOGLE_CLOUD_SPEECH', False)

        if self.use_google_cloud:
            try:
                from google.cloud import speech_v1 as speech
                from google.cloud import texttospeech
                self.speech_client = speech.SpeechClient()
                self.tts_client = texttospeech.TextToSpeechClient()
                logger.info("Google Cloud Speech API initialized")
            except Exception as e:
                logger.warning(f"Google Cloud Speech API not available: {e}")
                self.use_google_cloud = False

    def transcribe_audio(self, audio_data: bytes, audio_format: str = "webm") -> Dict[str, Any]:
        """
        Convert speech audio to text using Google Cloud Speech API or alternative.

        Args:
            audio_data: Audio data in bytes
            audio_format: Audio format (webm, mp3, wav, etc.)

        Returns:
            Dict with 'success', 'text', and optional 'confidence' keys
        """
        try:
            if self.use_google_cloud:
                return self._transcribe_google_cloud(audio_data, audio_format)
            else:
                # Web Speech API is handled on frontend, this is a fallback
                return {
                    'success': True,
                    'text': '',
                    'message': 'Using browser speech recognition'
                }
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return {
                'success': False,
                'error': str(e),
                'text': ''
            }

    def _transcribe_google_cloud(self, audio_data: bytes, audio_format: str) -> Dict[str, Any]:
        """
        Transcribe audio using Google Cloud Speech-to-Text API.
        """
        from google.cloud import speech_v1 as speech

        # Map audio format to encoding
        encoding_map = {
            'webm': speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            'mp3': speech.RecognitionConfig.AudioEncoding.MP3,
            'wav': speech.RecognitionConfig.AudioEncoding.LINEAR16,
            'ogg': speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        }

        encoding = encoding_map.get(audio_format.lower(), speech.RecognitionConfig.AudioEncoding.WEBM_OPUS)

        # Configure recognition
        config = speech.RecognitionConfig(
            encoding=encoding,
            sample_rate_hertz=48000,  # Standard for webm
            language_code='en-IN',  # English (India) for better medical term recognition
            alternative_language_codes=['hi-IN', 'en-US'],  # Support Hindi and US English
            enable_automatic_punctuation=True,
            model='medical_conversation',  # Optimized for medical conversations
            use_enhanced=True,
        )

        audio = speech.RecognitionAudio(content=audio_data)

        # Perform recognition
        response = self.speech_client.recognize(config=config, audio=audio)

        if not response.results:
            return {
                'success': False,
                'text': '',
                'message': 'No speech detected'
            }

        # Get the most confident result
        result = response.results[0]
        alternative = result.alternatives[0]

        return {
            'success': True,
            'text': alternative.transcript,
            'confidence': alternative.confidence,
        }

    def synthesize_speech(self, text: str, language_code: str = 'en-IN') -> Dict[str, Any]:
        """
        Convert text to speech audio using Google Cloud Text-to-Speech API.

        Args:
            text: Text to convert to speech
            language_code: Language code (en-IN, hi-IN, etc.)

        Returns:
            Dict with 'success', 'audio_data' (base64), and 'audio_format' keys
        """
        try:
            if self.use_google_cloud:
                return self._synthesize_google_cloud(text, language_code)
            else:
                # Web Speech API synthesis is handled on frontend
                return {
                    'success': True,
                    'audio_data': '',
                    'use_browser_tts': True,
                    'text': text
                }
        except Exception as e:
            logger.error(f"Error synthesizing speech: {e}")
            return {
                'success': False,
                'error': str(e),
                'audio_data': ''
            }

    def _synthesize_google_cloud(self, text: str, language_code: str) -> Dict[str, Any]:
        """
        Synthesize speech using Google Cloud Text-to-Speech API.
        """
        from google.cloud import texttospeech

        # Set up the synthesis input
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Select voice parameters
        voice_config = {
            'en-IN': {
                'name': 'en-IN-Wavenet-D',  # Natural female voice for medical assistant
                'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE
            },
            'hi-IN': {
                'name': 'hi-IN-Wavenet-D',
                'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE
            },
            'en-US': {
                'name': 'en-US-Wavenet-F',
                'ssml_gender': texttospeech.SsmlVoiceGender.FEMALE
            }
        }

        voice_params = voice_config.get(language_code, voice_config['en-IN'])

        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_params['name'],
            ssml_gender=voice_params['ssml_gender']
        )

        # Configure audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.95,  # Slightly slower for clarity
            pitch=0.0,
            effects_profile_id=['telephony-class-application']  # Optimized for voice calls
        )

        # Perform synthesis
        response = self.tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        # Encode audio to base64 for transmission
        audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')

        return {
            'success': True,
            'audio_data': audio_base64,
            'audio_format': 'mp3',
            'use_browser_tts': False
        }

    def get_voice_guidance(self, conversation_stage: str) -> str:
        """
        Get voice guidance text for different stages of appointment booking.
        This provides more detailed verbal instructions than text chat.

        Args:
            conversation_stage: Current stage of conversation

        Returns:
            Guidance text to be spoken
        """
        guidance_map = {
            'greeting': (
                "Hello! Welcome to the medical appointment booking system. "
                "I'm your voice assistant, and I'll help you book an appointment step by step. "
                "You can speak naturally, and I'll understand. "
                "To get started, please tell me what symptoms or health concerns you're experiencing today."
            ),
            'symptoms': (
                "Please describe your symptoms or health concerns. "
                "Take your time and speak clearly. "
                "I'll help match you with the right doctor."
            ),
            'doctor_selection': (
                "Based on your symptoms, I've found some doctors who can help you. "
                "I'll read out the options. Please tell me which doctor you'd like to see, "
                "or say the number of your choice."
            ),
            'date_selection': (
                "Great! Now let's choose a date for your appointment. "
                "I can show you available dates. "
                "Please tell me your preferred date, or say 'show available dates'."
            ),
            'time_selection': (
                "Now let's pick a time that works for you. "
                "Please tell me your preferred time slot from the available options."
            ),
            'patient_details': (
                "Almost done! I need to collect your contact information. "
                "Please provide your full name, phone number, and age. "
                "You can say them one at a time, or all together."
            ),
            'confirmation': (
                "Let me confirm your appointment details. "
                "If everything looks correct, say 'confirm' to book the appointment. "
                "If you need to change anything, just tell me what to modify."
            ),
            'completed': (
                "Perfect! Your appointment has been successfully booked. "
                "You'll receive a confirmation message via SMS. "
                "Is there anything else I can help you with?"
            )
        }

        return guidance_map.get(conversation_stage,
                               "How can I assist you with your appointment?")

    def format_response_for_voice(self, text_response: str, stage: str) -> str:
        """
        Format text response to be more suitable for voice output.
        Adds natural pauses and clearer pronunciation.

        Args:
            text_response: Original text response
            stage: Current conversation stage

        Returns:
            Formatted text for voice synthesis
        """
        # Remove HTML tags if any
        import re
        text = re.sub(r'<[^>]+>', '', text_response)

        # Add pauses for better speech flow
        text = text.replace('...', '... pause for 500ms ...')
        text = text.replace('\n', '. ')

        # Make numbers more speech-friendly
        text = re.sub(r'(\d+):(\d+)\s*(AM|PM)', r'\1 \2 \3', text)

        return text


# Global instance
voice_service = VoiceService()
