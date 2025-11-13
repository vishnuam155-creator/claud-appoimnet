"""
Voice Intelligence API Views
REST API endpoints for the voice intelligence assistant system.
"""

import json
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .voice_intelligence_manager import VoiceIntelligenceManager


@method_decorator(csrf_exempt, name='dispatch')
class VoiceIntelligenceAPIView(View):
    """
    Main API endpoint for voice intelligence assistant.

    Endpoints:
    - POST /api/voice-intelligence/ - Process voice input
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = VoiceIntelligenceManager(clinic_name="MedCare Clinic")

    def post(self, request):
        """
        Process voice input and return response.

        Request body:
        {
            "voice_text": "user speech input",
            "session_id": "optional session id"
        }

        Response:
        {
            "success": true/false,
            "session_id": "uuid",
            "voice_response": "natural language response for TTS",
            "action": "database_query_completed/direct_response/clarification_needed/error",
            "data": {
                "intent": {...},
                "database_action": {...},
                "database_result": {...},
                "conversation_context": {...}
            }
        }
        """
        try:
            body = json.loads(request.body.decode('utf-8'))
            voice_text = body.get('voice_text', '').strip()
            session_id = body.get('session_id')

            if not voice_text:
                return JsonResponse({
                    "success": False,
                    "error": "voice_text is required",
                    "voice_response": "I didn't catch that. Could you please repeat?"
                }, status=400)

            # Process voice input
            response = self.manager.process_voice_input(voice_text, session_id)

            return JsonResponse(response)

        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "error": "Invalid JSON in request body",
                "voice_response": "I'm having trouble processing that. Could you try again?"
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e),
                "voice_response": "I apologize, but I encountered an unexpected error. Please try again."
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class DatabaseActionAPIView(View):
    """
    API endpoint for executing database actions directly.

    This endpoint allows backend systems to execute database actions
    and receive natural language responses.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = VoiceIntelligenceManager(clinic_name="MedCare Clinic")

    def post(self, request):
        """
        Execute database action directly.

        Request body:
        {
            "action": "query_database",
            "query_type": "appointment_lookup/create_appointment/etc",
            "parameters": {...},
            "session_id": "optional"
        }

        Response:
        {
            "success": true/false,
            "session_id": "uuid",
            "voice_response": "natural language response",
            "database_result": {...}
        }
        """
        try:
            body = json.loads(request.body.decode('utf-8'))
            action = {
                "action": body.get('action'),
                "query_type": body.get('query_type'),
                "parameters": body.get('parameters', {})
            }
            session_id = body.get('session_id')

            if not action.get('action') or not action.get('query_type'):
                return JsonResponse({
                    "success": False,
                    "error": "action and query_type are required"
                }, status=400)

            # Execute database action
            response = self.manager.execute_database_action_directly(action, session_id)

            return JsonResponse(response)

        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "error": "Invalid JSON in request body"
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class IntentAnalysisAPIView(View):
    """
    API endpoint for analyzing intent without executing actions.

    Useful for debugging and testing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = VoiceIntelligenceManager(clinic_name="MedCare Clinic")

    def post(self, request):
        """
        Analyze intent and generate action without executing.

        Request body:
        {
            "voice_text": "user speech input",
            "session_id": "optional"
        }

        Response:
        {
            "understood_input": {...},
            "intent": {...},
            "database_action": {...},
            "missing_information": [...]
        }
        """
        try:
            body = json.loads(request.body.decode('utf-8'))
            voice_text = body.get('voice_text', '').strip()
            session_id = body.get('session_id')

            if not voice_text:
                return JsonResponse({
                    "error": "voice_text is required"
                }, status=400)

            # Analyze intent
            result = self.manager.get_intent_and_action(voice_text, session_id)

            return JsonResponse(result)

        except json.JSONDecodeError:
            return JsonResponse({
                "error": "Invalid JSON in request body"
            }, status=400)

        except Exception as e:
            return JsonResponse({
                "error": str(e)
            }, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class SessionManagementAPIView(View):
    """
    API endpoint for managing voice intelligence sessions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = VoiceIntelligenceManager(clinic_name="MedCare Clinic")

    def get(self, request):
        """
        Get session information.

        Query params:
            session_id: Session ID to retrieve

        Response:
        {
            "session_id": "uuid",
            "conversation_length": 5,
            "collected_information": {...},
            "current_intent": "appointment_booking",
            "last_action": "appointment_created"
        }
        """
        session_id = request.GET.get('session_id')

        if not session_id:
            return JsonResponse({
                "error": "session_id query parameter is required"
            }, status=400)

        session_info = self.manager.get_session_info(session_id)

        return JsonResponse(session_info)

    def delete(self, request):
        """
        Clear session.

        Query params:
            session_id: Session ID to clear

        Response:
        {
            "success": true/false,
            "message": "Session cleared"
        }
        """
        session_id = request.GET.get('session_id')

        if not session_id:
            return JsonResponse({
                "error": "session_id query parameter is required"
            }, status=400)

        success = self.manager.clear_session(session_id)

        return JsonResponse({
            "success": success,
            "message": "Session cleared" if success else "Failed to clear session"
        })


# Legacy compatibility view for existing voicebot
@method_decorator(csrf_exempt, name='dispatch')
class VoicebotCompatibilityView(View):
    """
    Compatibility view that wraps voice intelligence in the old voicebot API format.

    This allows existing frontend code to work with the new system.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.manager = VoiceIntelligenceManager(clinic_name="MedCare Clinic")

    def post(self, request):
        """
        Process voice message (legacy format).

        Request body:
        {
            "session_id": "optional",
            "message": "user voice text"
        }

        Response (legacy format):
        {
            "success": true,
            "session_id": "uuid",
            "message": "bot response",
            "stage": "conversation_stage",
            "action": "continue/booking_complete",
            "data": {...}
        }
        """
        try:
            body = json.loads(request.body.decode('utf-8'))
            message = body.get('message', '').strip()
            session_id = body.get('session_id')

            if not message:
                return JsonResponse({
                    "success": False,
                    "error": "message is required"
                }, status=400)

            # Process with new system
            response = self.manager.process_voice_input(message, session_id)

            # Convert to legacy format
            legacy_response = {
                "success": response.get('success'),
                "session_id": response.get('session_id'),
                "message": response.get('voice_response'),
                "action": self._map_action_to_legacy(response.get('action')),
                "data": response.get('data', {})
            }

            # Add stage for compatibility
            intent = response.get('data', {}).get('intent', {})
            legacy_response['stage'] = self._map_intent_to_stage(intent.get('intent'))

            return JsonResponse(legacy_response)

        except Exception as e:
            return JsonResponse({
                "success": False,
                "error": str(e),
                "message": "I apologize, but I encountered an error."
            }, status=500)

    def _map_action_to_legacy(self, action: str) -> str:
        """Map new action types to legacy action types."""
        mapping = {
            "database_query_completed": "continue",
            "direct_response": "continue",
            "clarification_needed": "continue",
            "error": "error"
        }
        return mapping.get(action, "continue")

    def _map_intent_to_stage(self, intent: str) -> str:
        """Map intent to legacy conversation stage."""
        mapping = {
            "appointment_booking": "booking_in_progress",
            "appointment_lookup": "lookup",
            "appointment_cancel": "cancellation",
            "appointment_reschedule": "rescheduling",
            "general_query": "greeting",
            "support_request": "greeting"
        }
        return mapping.get(intent, "greeting")
