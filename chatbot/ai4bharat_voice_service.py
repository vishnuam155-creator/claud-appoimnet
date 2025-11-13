"""
AI4Bharat Voice Service Integration
Provides Speech-to-Text and Text-to-Speech using AI4Bharat models
Supports multiple Indian languages
"""

import os
import requests
import json
import base64
import logging
from typing import Dict, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class AI4BharatVoiceService:
    """
    AI4Bharat Voice Service for Indian Language Speech Processing

    Supports:
    - Speech-to-Text (ASR) using IndicWav2Vec
    - Text-to-Speech (TTS) using IndicTTS
    - Multiple Indian languages: Hindi, Tamil, Telugu, Bengali, Marathi, etc.
    """

    # Supported languages with their codes
    SUPPORTED_LANGUAGES = {
        'hindi': 'hi',
        'tamil': 'ta',
        'telugu': 'te',
        'bengali': 'bn',
        'marathi': 'mr',
        'gujarati': 'gu',
        'kannada': 'kn',
        'malayalam': 'ml',
        'punjabi': 'pa',
        'english': 'en'
    }

    def __init__(self):
        """Initialize AI4Bharat Voice Service"""
        self.asr_endpoint = getattr(settings, 'AI4BHARAT_ASR_ENDPOINT',
                                    'https://api.ai4bharat.org/asr/v1/recognize')
        self.tts_endpoint = getattr(settings, 'AI4BHARAT_TTS_ENDPOINT',
                                    'https://api.ai4bharat.org/tts/v1/synthesize')
        self.api_key = getattr(settings, 'AI4BHARAT_API_KEY', os.getenv('AI4BHARAT_API_KEY'))
        self.default_language = getattr(settings, 'AI4BHARAT_DEFAULT_LANGUAGE', 'hi')

        # Voice settings
        self.default_voice_gender = getattr(settings, 'AI4BHARAT_VOICE_GENDER', 'female')
        self.speaking_rate = getattr(settings, 'AI4BHARAT_SPEAKING_RATE', 1.0)

        logger.info(f"AI4Bharat Voice Service initialized with language: {self.default_language}")

    def speech_to_text(self, audio_data: bytes, language: str = None,
                      audio_format: str = 'wav') -> Dict:
        """
        Convert speech audio to text using AI4Bharat ASR

        Args:
            audio_data: Audio data in bytes
            language: Language code (hi, ta, te, etc.)
            audio_format: Audio format (wav, mp3, flac)

        Returns:
            Dict with transcription results
        """
        try:
            if not self.api_key:
                logger.warning("AI4Bharat API key not configured, using fallback")
                return self._fallback_stt(audio_data)

            language = language or self.default_language

            # Prepare request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            # Encode audio to base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            payload = {
                'audio': audio_base64,
                'language': language,
                'format': audio_format,
                'sampleRate': 16000
            }

            logger.info(f"Sending ASR request for language: {language}")
            response = requests.post(
                self.asr_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                transcript = result.get('transcript', '')
                confidence = result.get('confidence', 0.0)

                logger.info(f"ASR Success: {transcript[:50]}... (confidence: {confidence})")

                return {
                    'success': True,
                    'transcript': transcript,
                    'confidence': confidence,
                    'language': language,
                    'alternatives': result.get('alternatives', [])
                }
            else:
                logger.error(f"ASR API error: {response.status_code} - {response.text}")
                return self._fallback_stt(audio_data)

        except requests.exceptions.RequestException as e:
            logger.error(f"ASR request failed: {str(e)}")
            return self._fallback_stt(audio_data)
        except Exception as e:
            logger.error(f"ASR processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'transcript': ''
            }

    def text_to_speech(self, text: str, language: str = None,
                      voice_gender: str = None) -> Dict:
        """
        Convert text to speech audio using AI4Bharat TTS

        Args:
            text: Text to convert to speech
            language: Language code (hi, ta, te, etc.)
            voice_gender: Voice gender (male/female)

        Returns:
            Dict with audio data and metadata
        """
        try:
            if not self.api_key:
                logger.warning("AI4Bharat API key not configured, using fallback")
                return self._fallback_tts(text)

            language = language or self.default_language
            voice_gender = voice_gender or self.default_voice_gender

            # Prepare request
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'text': text,
                'language': language,
                'gender': voice_gender,
                'speakingRate': self.speaking_rate,
                'audioFormat': 'wav'
            }

            logger.info(f"Sending TTS request for language: {language}, text length: {len(text)}")
            response = requests.post(
                self.tts_endpoint,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                audio_base64 = result.get('audio', '')
                audio_data = base64.b64decode(audio_base64)

                logger.info(f"TTS Success: Generated {len(audio_data)} bytes of audio")

                return {
                    'success': True,
                    'audio_data': audio_data,
                    'audio_format': 'wav',
                    'language': language,
                    'duration': result.get('duration', 0)
                }
            else:
                logger.error(f"TTS API error: {response.status_code} - {response.text}")
                return self._fallback_tts(text)

        except requests.exceptions.RequestException as e:
            logger.error(f"TTS request failed: {str(e)}")
            return self._fallback_tts(text)
        except Exception as e:
            logger.error(f"TTS processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'audio_data': None
            }

    def detect_language(self, audio_data: bytes) -> Dict:
        """
        Detect the language of the audio

        Args:
            audio_data: Audio data in bytes

        Returns:
            Dict with detected language and confidence
        """
        try:
            if not self.api_key:
                return {
                    'success': False,
                    'language': self.default_language,
                    'confidence': 0.0
                }

            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            payload = {
                'audio': audio_base64,
                'format': 'wav'
            }

            detect_endpoint = getattr(settings, 'AI4BHARAT_LANG_DETECT_ENDPOINT',
                                     'https://api.ai4bharat.org/language/detect')

            response = requests.post(
                detect_endpoint,
                headers=headers,
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'language': result.get('language', self.default_language),
                    'confidence': result.get('confidence', 0.0),
                    'alternatives': result.get('alternatives', [])
                }
            else:
                logger.error(f"Language detection error: {response.status_code}")
                return {
                    'success': False,
                    'language': self.default_language,
                    'confidence': 0.0
                }

        except Exception as e:
            logger.error(f"Language detection failed: {str(e)}")
            return {
                'success': False,
                'language': self.default_language,
                'confidence': 0.0
            }

    def _fallback_stt(self, audio_data: bytes) -> Dict:
        """Fallback STT when API is unavailable"""
        logger.info("Using fallback STT (browser-based)")
        return {
            'success': False,
            'transcript': '',
            'error': 'API not configured, use browser-based speech recognition',
            'fallback': True
        }

    def _fallback_tts(self, text: str) -> Dict:
        """Fallback TTS when API is unavailable"""
        logger.info("Using fallback TTS (browser-based)")
        return {
            'success': False,
            'audio_data': None,
            'error': 'API not configured, use browser-based speech synthesis',
            'fallback': True,
            'text': text
        }

    def get_supported_languages(self) -> List[Dict]:
        """Get list of supported languages"""
        return [
            {'code': code, 'name': name.title()}
            for name, code in self.SUPPORTED_LANGUAGES.items()
        ]

    def validate_language(self, language: str) -> bool:
        """Validate if language is supported"""
        return language in self.SUPPORTED_LANGUAGES.values()


# Singleton instance
_ai4bharat_service = None


def get_ai4bharat_service() -> AI4BharatVoiceService:
    """Get or create AI4Bharat service singleton"""
    global _ai4bharat_service
    if _ai4bharat_service is None:
        _ai4bharat_service = AI4BharatVoiceService()
    return _ai4bharat_service
