"""
Unified Voice Service
Provides a unified interface for multiple voice providers
Supports: Browser API, Google Cloud Speech, AI4Bharat
"""

import logging
from typing import Dict, Optional
from django.conf import settings

from chatbot.ai4bharat_voice_service import get_ai4bharat_service
from chatbot.voice_service import VoiceService

logger = logging.getLogger(__name__)


class UnifiedVoiceService:
    """
    Unified Voice Service that routes to different voice providers
    based on configuration or user preference
    """

    PROVIDERS = {
        'browser': 'Browser Speech API',
        'google': 'Google Cloud Speech',
        'ai4bharat': 'AI4Bharat'
    }

    def __init__(self, provider: str = None, session_data: dict = None):
        """
        Initialize Unified Voice Service

        Args:
            provider: Voice provider to use ('browser', 'google', 'ai4bharat')
            session_data: Session data that may contain provider preference
        """
        # Determine provider
        self.provider = self._determine_provider(provider, session_data)

        # Initialize services
        self.ai4bharat = None
        self.google_voice = None

        if self.provider == 'ai4bharat':
            self.ai4bharat = get_ai4bharat_service()
        elif self.provider == 'google':
            self.google_voice = VoiceService()

        logger.info(f"Unified Voice Service initialized with provider: {self.provider}")

    def _determine_provider(self, provider: str = None, session_data: dict = None) -> str:
        """
        Determine which voice provider to use

        Priority:
        1. Explicitly passed provider
        2. Provider from session data
        3. Provider from settings
        4. Default to 'browser'
        """
        # Priority 1: Explicit provider
        if provider and provider in self.PROVIDERS:
            return provider

        # Priority 2: Session preference
        if session_data and 'voice_provider' in session_data:
            provider_from_session = session_data['voice_provider']
            if provider_from_session in self.PROVIDERS:
                return provider_from_session

        # Priority 3: Settings
        provider_from_settings = getattr(settings, 'VOICE_PROVIDER', 'browser')
        if provider_from_settings in self.PROVIDERS:
            return provider_from_settings

        # Default
        return 'browser'

    def speech_to_text(self, audio_data: bytes, language: str = None,
                      audio_format: str = 'wav') -> Dict:
        """
        Convert speech to text using configured provider

        Args:
            audio_data: Audio data in bytes
            language: Language code
            audio_format: Audio format

        Returns:
            Dict with transcription results
        """
        try:
            if self.provider == 'ai4bharat':
                return self.ai4bharat.speech_to_text(audio_data, language, audio_format)

            elif self.provider == 'google':
                # Implement Google STT if VoiceService supports it
                return {
                    'success': False,
                    'transcript': '',
                    'error': 'Google STT not implemented in this version',
                    'fallback': True
                }

            else:  # browser
                return {
                    'success': False,
                    'transcript': '',
                    'error': 'Browser-based STT must be done client-side',
                    'fallback': True
                }

        except Exception as e:
            logger.error(f"STT error with provider {self.provider}: {str(e)}")
            return {
                'success': False,
                'transcript': '',
                'error': str(e)
            }

    def text_to_speech(self, text: str, language: str = None,
                      voice_gender: str = None) -> Dict:
        """
        Convert text to speech using configured provider

        Args:
            text: Text to convert
            language: Language code
            voice_gender: Voice gender preference

        Returns:
            Dict with audio data and metadata
        """
        try:
            if self.provider == 'ai4bharat':
                return self.ai4bharat.text_to_speech(text, language, voice_gender)

            elif self.provider == 'google':
                # Implement Google TTS if VoiceService supports it
                return {
                    'success': False,
                    'audio_data': None,
                    'error': 'Google TTS not implemented in this version',
                    'fallback': True,
                    'text': text
                }

            else:  # browser
                return {
                    'success': False,
                    'audio_data': None,
                    'error': 'Browser-based TTS must be done client-side',
                    'fallback': True,
                    'text': text
                }

        except Exception as e:
            logger.error(f"TTS error with provider {self.provider}: {str(e)}")
            return {
                'success': False,
                'audio_data': None,
                'error': str(e),
                'text': text
            }

    def get_provider_info(self) -> Dict:
        """Get information about current provider"""
        return {
            'provider': self.provider,
            'provider_name': self.PROVIDERS.get(self.provider, 'Unknown'),
            'supports_server_stt': self.provider in ['ai4bharat', 'google'],
            'supports_server_tts': self.provider in ['ai4bharat', 'google'],
            'requires_client_side': self.provider == 'browser'
        }

    def get_supported_languages(self) -> list:
        """Get supported languages for current provider"""
        if self.provider == 'ai4bharat':
            return self.ai4bharat.get_supported_languages()
        elif self.provider == 'google':
            return [
                {'code': 'en-IN', 'name': 'English (India)'},
                {'code': 'hi-IN', 'name': 'Hindi'},
                {'code': 'en-US', 'name': 'English (US)'}
            ]
        else:  # browser
            return [
                {'code': 'en-IN', 'name': 'English (India)'},
                {'code': 'hi-IN', 'name': 'Hindi'},
                {'code': 'en-US', 'name': 'English (US)'}
            ]

    def validate_configuration(self) -> Dict:
        """
        Validate that the provider is properly configured

        Returns:
            Dict with validation results
        """
        validation = {
            'provider': self.provider,
            'configured': False,
            'errors': []
        }

        if self.provider == 'ai4bharat':
            api_key = getattr(settings, 'AI4BHARAT_API_KEY', '')
            if not api_key:
                validation['errors'].append('AI4BHARAT_API_KEY not configured')
            else:
                validation['configured'] = True

        elif self.provider == 'google':
            use_google = getattr(settings, 'USE_GOOGLE_CLOUD_SPEECH', False)
            if not use_google:
                validation['errors'].append('USE_GOOGLE_CLOUD_SPEECH not enabled')
            else:
                validation['configured'] = True

        else:  # browser
            validation['configured'] = True

        return validation

    @staticmethod
    def get_available_providers() -> list:
        """
        Get list of all available providers with their status

        Returns:
            List of provider information
        """
        providers = []

        # Browser (always available)
        providers.append({
            'id': 'browser',
            'name': 'Browser Speech API',
            'description': 'Built-in browser speech recognition (Free)',
            'enabled': True,
            'configured': True,
            'languages': ['en-IN', 'hi-IN', 'en-US']
        })

        # Google Cloud
        google_enabled = getattr(settings, 'USE_GOOGLE_CLOUD_SPEECH', False)
        providers.append({
            'id': 'google',
            'name': 'Google Cloud Speech',
            'description': 'Google Cloud Speech-to-Text and TTS',
            'enabled': google_enabled,
            'configured': google_enabled,
            'languages': ['en-IN', 'hi-IN', 'en-US', 'ta-IN', 'te-IN']
        })

        # AI4Bharat
        ai4bharat_key = getattr(settings, 'AI4BHARAT_API_KEY', '')
        providers.append({
            'id': 'ai4bharat',
            'name': 'AI4Bharat',
            'description': 'Indian language AI models for speech',
            'enabled': bool(ai4bharat_key),
            'configured': bool(ai4bharat_key),
            'languages': ['hi', 'ta', 'te', 'bn', 'mr', 'gu', 'kn', 'ml', 'pa', 'en']
        })

        return providers

    def set_provider(self, provider: str) -> bool:
        """
        Change the current provider

        Args:
            provider: New provider to use

        Returns:
            True if successful, False otherwise
        """
        if provider not in self.PROVIDERS:
            logger.error(f"Invalid provider: {provider}")
            return False

        # Validate configuration
        validation = self.validate_configuration()
        if not validation['configured']:
            logger.error(f"Provider {provider} is not configured: {validation['errors']}")
            return False

        self.provider = provider

        # Re-initialize services
        if provider == 'ai4bharat':
            self.ai4bharat = get_ai4bharat_service()
        elif provider == 'google':
            self.google_voice = VoiceService()

        logger.info(f"Provider changed to: {provider}")
        return True


# Helper function to get unified voice service
def get_unified_voice_service(provider: str = None, session_data: dict = None) -> UnifiedVoiceService:
    """
    Get or create unified voice service

    Args:
        provider: Voice provider to use
        session_data: Session data

    Returns:
        UnifiedVoiceService instance
    """
    return UnifiedVoiceService(provider, session_data)
