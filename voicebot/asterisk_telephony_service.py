"""
Asterisk Telephony Service Integration
Provides telephony integration for voicebot using Asterisk PBX
Supports both AGI (Asterisk Gateway Interface) and ARI (Asterisk REST Interface)
"""

import os
import sys
import json
import logging
import asyncio
import requests
from typing import Dict, Optional, Callable
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class AsteriskAGIHandler:
    """
    Asterisk AGI (Gateway Interface) Handler
    Handles incoming AGI requests from Asterisk dialplan
    """

    def __init__(self):
        """Initialize AGI Handler"""
        self.env = {}
        self.input_stream = sys.stdin
        self.output_stream = sys.stdout

    def read_environment(self):
        """Read AGI environment variables"""
        while True:
            line = self.input_stream.readline().strip()
            if not line:
                break
            key, value = line.split(':', 1)
            self.env[key.strip()] = value.strip()

        logger.info(f"AGI Environment loaded: {len(self.env)} variables")
        return self.env

    def execute(self, command: str, *args) -> str:
        """
        Execute AGI command

        Args:
            command: AGI command to execute
            args: Command arguments

        Returns:
            Response from Asterisk
        """
        cmd_str = f"{command} {' '.join(str(arg) for arg in args)}\n"
        self.output_stream.write(cmd_str)
        self.output_stream.flush()

        response = self.input_stream.readline().strip()
        logger.debug(f"AGI Command: {cmd_str.strip()} -> Response: {response}")
        return response

    def answer(self):
        """Answer the call"""
        return self.execute('ANSWER')

    def stream_file(self, filename: str, escape_digits: str = '') -> str:
        """Play audio file"""
        return self.execute('STREAM FILE', filename, f'"{escape_digits}"')

    def get_data(self, filename: str, timeout: int = 5000, max_digits: int = 10) -> str:
        """Play file and get DTMF digits"""
        return self.execute('GET DATA', filename, timeout, max_digits)

    def record_file(self, filename: str, format: str = 'wav',
                   escape_digits: str = '#', timeout: int = -1,
                   beep: bool = True) -> str:
        """Record audio from caller"""
        beep_str = 'beep' if beep else ''
        return self.execute('RECORD FILE', filename, format, escape_digits, timeout, beep_str)

    def say_text(self, text: str) -> str:
        """Speak text using TTS"""
        return self.execute('EXEC', 'Festival', f'"{text}"')

    def hangup(self):
        """Hangup the call"""
        return self.execute('HANGUP')

    def get_variable(self, variable: str) -> str:
        """Get channel variable"""
        return self.execute('GET VARIABLE', variable)

    def set_variable(self, variable: str, value: str) -> str:
        """Set channel variable"""
        return self.execute('SET VARIABLE', variable, value)


class AsteriskARIClient:
    """
    Asterisk ARI (REST Interface) Client
    Manages calls through Asterisk REST API
    """

    def __init__(self):
        """Initialize ARI Client"""
        self.base_url = getattr(settings, 'ASTERISK_ARI_URL', 'http://localhost:8088/ari')
        self.username = getattr(settings, 'ASTERISK_ARI_USERNAME', 'asterisk')
        self.password = getattr(settings, 'ASTERISK_ARI_PASSWORD', 'asterisk')
        self.app_name = getattr(settings, 'ASTERISK_ARI_APP', 'voicebot')

        self.session = requests.Session()
        self.session.auth = (self.username, self.password)

        logger.info(f"Asterisk ARI Client initialized: {self.base_url}")

    def get_channels(self) -> list:
        """Get all active channels"""
        try:
            response = self.session.get(f"{self.base_url}/channels")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get channels: {str(e)}")
            return []

    def answer_channel(self, channel_id: str) -> bool:
        """Answer a channel"""
        try:
            response = self.session.post(f"{self.base_url}/channels/{channel_id}/answer")
            response.raise_for_status()
            logger.info(f"Answered channel: {channel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to answer channel {channel_id}: {str(e)}")
            return False

    def play_audio(self, channel_id: str, media_uri: str) -> Dict:
        """Play audio on channel"""
        try:
            payload = {
                'media': f'sound:{media_uri}'
            }
            response = self.session.post(
                f"{self.base_url}/channels/{channel_id}/play",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to play audio on {channel_id}: {str(e)}")
            return {}

    def record_channel(self, channel_id: str, name: str,
                      format: str = 'wav', max_duration: int = 60) -> Dict:
        """Record audio from channel"""
        try:
            payload = {
                'name': name,
                'format': format,
                'maxDurationSeconds': max_duration,
                'ifExists': 'overwrite'
            }
            response = self.session.post(
                f"{self.base_url}/channels/{channel_id}/record",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to record channel {channel_id}: {str(e)}")
            return {}

    def hangup_channel(self, channel_id: str) -> bool:
        """Hangup a channel"""
        try:
            response = self.session.delete(f"{self.base_url}/channels/{channel_id}")
            response.raise_for_status()
            logger.info(f"Hung up channel: {channel_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to hangup channel {channel_id}: {str(e)}")
            return False

    def originate_call(self, endpoint: str, extension: str, context: str = 'default') -> Dict:
        """Originate outbound call"""
        try:
            payload = {
                'endpoint': endpoint,
                'extension': extension,
                'context': context,
                'app': self.app_name
            }
            response = self.session.post(
                f"{self.base_url}/channels",
                json=payload
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to originate call: {str(e)}")
            return {}


class AsteriskTelephonyService:
    """
    Main Asterisk Telephony Service
    Integrates voicebot with Asterisk for phone call handling
    """

    def __init__(self):
        """Initialize Asterisk Telephony Service"""
        self.agi = AsteriskAGIHandler()
        self.ari = AsteriskARIClient()

        self.recording_path = getattr(settings, 'ASTERISK_RECORDING_PATH',
                                     '/var/spool/asterisk/recording')
        self.audio_path = getattr(settings, 'ASTERISK_AUDIO_PATH',
                                  '/var/lib/asterisk/sounds/custom')

        self.voicebot_callback = None
        self.active_sessions = {}

        logger.info("Asterisk Telephony Service initialized")

    def register_voicebot_callback(self, callback: Callable):
        """
        Register voicebot processing callback

        Args:
            callback: Function to process voice messages
        """
        self.voicebot_callback = callback
        logger.info("Voicebot callback registered")

    def handle_incoming_call_agi(self, caller_id: str) -> Dict:
        """
        Handle incoming call using AGI

        Args:
            caller_id: Caller's phone number

        Returns:
            Call handling result
        """
        try:
            session_id = f"asterisk_{caller_id}_{int(datetime.now().timestamp())}"

            logger.info(f"Incoming call from {caller_id}, session: {session_id}")

            # Answer the call
            self.agi.answer()

            # Play welcome message
            self.agi.stream_file('custom/welcome')

            # Initialize session
            self.active_sessions[session_id] = {
                'caller_id': caller_id,
                'start_time': datetime.now(),
                'stage': 'greeting'
            }

            # Main conversation loop
            while True:
                # Record user input
                recording_file = f"{self.recording_path}/input_{session_id}_{int(datetime.now().timestamp())}"
                self.agi.record_file(recording_file, 'wav', '#', 5000, True)

                # Check if recording exists
                if not os.path.exists(f"{recording_file}.wav"):
                    logger.warning(f"No recording found: {recording_file}")
                    break

                # Process with voicebot
                if self.voicebot_callback:
                    with open(f"{recording_file}.wav", 'rb') as audio_file:
                        audio_data = audio_file.read()

                    response = self.voicebot_callback(
                        audio_data=audio_data,
                        session_id=session_id,
                        caller_id=caller_id
                    )

                    # Play response
                    if response.get('audio_file'):
                        self.agi.stream_file(response['audio_file'])
                    elif response.get('text'):
                        self.agi.say_text(response['text'])

                    # Check if conversation is complete
                    if response.get('action') == 'end':
                        break
                else:
                    logger.error("Voicebot callback not registered")
                    break

            # Play goodbye message
            self.agi.stream_file('custom/goodbye')

            # Hangup
            self.agi.hangup()

            # Clean up session
            del self.active_sessions[session_id]

            return {
                'success': True,
                'session_id': session_id,
                'caller_id': caller_id
            }

        except Exception as e:
            logger.error(f"AGI call handling error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def handle_incoming_call_ari(self, channel_id: str, caller_id: str) -> Dict:
        """
        Handle incoming call using ARI

        Args:
            channel_id: Asterisk channel ID
            caller_id: Caller's phone number

        Returns:
            Call handling result
        """
        try:
            session_id = f"asterisk_{caller_id}_{int(datetime.now().timestamp())}"

            logger.info(f"ARI: Incoming call from {caller_id}, channel: {channel_id}")

            # Answer the call
            self.ari.answer_channel(channel_id)

            # Play welcome message
            self.ari.play_audio(channel_id, 'custom/welcome')

            # Initialize session
            self.active_sessions[session_id] = {
                'caller_id': caller_id,
                'channel_id': channel_id,
                'start_time': datetime.now(),
                'stage': 'greeting'
            }

            return {
                'success': True,
                'session_id': session_id,
                'channel_id': channel_id,
                'caller_id': caller_id
            }

        except Exception as e:
            logger.error(f"ARI call handling error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def make_outbound_call(self, phone_number: str, message: str) -> Dict:
        """
        Make outbound call with voicebot

        Args:
            phone_number: Number to call
            message: Message to deliver

        Returns:
            Call result
        """
        try:
            endpoint = f"PJSIP/{phone_number}"
            result = self.ari.originate_call(endpoint, 's', 'outbound')

            if result:
                channel_id = result.get('id')
                logger.info(f"Outbound call initiated to {phone_number}, channel: {channel_id}")

                return {
                    'success': True,
                    'channel_id': channel_id,
                    'phone_number': phone_number
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to originate call'
                }

        except Exception as e:
            logger.error(f"Outbound call error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_active_calls(self) -> list:
        """Get list of active calls"""
        return list(self.active_sessions.values())

    def end_call(self, session_id: str) -> bool:
        """End a call by session ID"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            channel_id = session.get('channel_id')

            if channel_id:
                self.ari.hangup_channel(channel_id)

            del self.active_sessions[session_id]
            return True

        return False


# Singleton instance
_asterisk_service = None


def get_asterisk_service() -> AsteriskTelephonyService:
    """Get or create Asterisk service singleton"""
    global _asterisk_service
    if _asterisk_service is None:
        _asterisk_service = AsteriskTelephonyService()
    return _asterisk_service
