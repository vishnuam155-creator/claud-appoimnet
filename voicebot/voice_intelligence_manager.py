"""
Voice Intelligence Manager
Orchestrates the voice intelligence assistant workflow using intent-to-action architecture.
"""

import json
import uuid
from typing import Dict, Any, Optional
from django.core.cache import cache

from .voice_intelligence_service import VoiceIntelligenceService
from .database_action_handler import DatabaseActionHandler


class VoiceIntelligenceManager:
    """
    Manages the complete voice intelligence workflow:
    1. Receive voice input
    2. Understand and correct speech
    3. Identify intent
    4. Generate database action (JSON)
    5. Execute database action
    6. Generate natural language response
    7. Return voice output
    """

    def __init__(self, clinic_name: str = "MedCare Clinic"):
        self.clinic_name = clinic_name
        self.intelligence_service = VoiceIntelligenceService(clinic_name)
        self.db_handler = DatabaseActionHandler()

    def process_voice_input(
        self,
        voice_text: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing voice input.

        Args:
            voice_text: Raw voice input from user
            session_id: Optional session ID for conversation continuity

        Returns:
            {
                "success": true/false,
                "session_id": "uuid",
                "voice_response": "natural language response for TTS",
                "action": "database_action/respond/clarify/complete",
                "data": {
                    "intent": {...},
                    "database_action": {...},
                    "database_result": {...},
                    "conversation_context": {...}
                }
            }
        """
        # Initialize or retrieve session
        if not session_id:
            session_id = str(uuid.uuid4())

        context = self._get_session_context(session_id)

        try:
            # Step 1: Understand and correct voice input
            understood = self.intelligence_service.understand_voice_input(voice_text, context)

            # Step 2: Identify intent
            intent = self.intelligence_service.identify_intent(
                understood.get('corrected_text', voice_text),
                context
            )

            # Update context with new information
            self._update_context(context, understood, intent)

            # Step 3: Generate database action or respond directly
            db_action = self.intelligence_service.generate_database_action(
                intent,
                understood,
                context
            )

            # Step 4: Execute database action if needed
            if db_action.get('action') == 'query_database':
                # Execute database operation
                db_result = self.db_handler.execute_action(db_action)

                # Step 5: Generate natural language response from DB result
                voice_response = self.intelligence_service.generate_voice_response(
                    db_result,
                    db_action.get('query_type'),
                    context
                )

                # Update context with database result
                self._update_context_from_db_result(context, db_result, db_action.get('query_type'))

                response = {
                    "success": db_result.get('status') == 'success',
                    "session_id": session_id,
                    "voice_response": voice_response,
                    "action": "database_query_completed",
                    "data": {
                        "intent": intent,
                        "understood_input": understood,
                        "database_action": db_action,
                        "database_result": db_result,
                        "conversation_context": context
                    }
                }

            elif db_action.get('action') == 'respond':
                # Direct response (no database needed)
                voice_response = db_action.get('direct_response', "How can I help you?")

                response = {
                    "success": True,
                    "session_id": session_id,
                    "voice_response": voice_response,
                    "action": "direct_response",
                    "data": {
                        "intent": intent,
                        "understood_input": understood,
                        "conversation_context": context
                    }
                }

            else:
                # Check if clarification is needed
                if understood.get('needs_clarification') or intent.get('confidence') == 'low':
                    # Generate clarification question
                    missing_info = self._identify_missing_information(intent, context)
                    voice_response = self.intelligence_service.generate_clarification_question(
                        missing_info,
                        context
                    )

                    response = {
                        "success": True,
                        "session_id": session_id,
                        "voice_response": voice_response,
                        "action": "clarification_needed",
                        "data": {
                            "intent": intent,
                            "understood_input": understood,
                            "missing_information": missing_info,
                            "conversation_context": context
                        }
                    }
                else:
                    voice_response = "I understand. How can I assist you with your appointment today?"
                    response = {
                        "success": True,
                        "session_id": session_id,
                        "voice_response": voice_response,
                        "action": "continue",
                        "data": {
                            "intent": intent,
                            "understood_input": understood,
                            "conversation_context": context
                        }
                    }

            # Save session context
            self._save_session_context(session_id, context)

            return response

        except Exception as e:
            error_response = f"I apologize, but I encountered an issue processing your request. Could you please try again?"

            return {
                "success": False,
                "session_id": session_id,
                "voice_response": error_response,
                "action": "error",
                "data": {
                    "error": str(e),
                    "conversation_context": context
                }
            }

    def execute_database_action_directly(
        self,
        action: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a database action directly (for backend integration).

        Args:
            action: JSON action to execute
            session_id: Optional session ID

        Returns:
            {
                "success": true/false,
                "session_id": "uuid",
                "voice_response": "natural language response",
                "database_result": {...}
            }
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        context = self._get_session_context(session_id)

        try:
            # Execute database action
            db_result = self.db_handler.execute_action(action)

            # Generate natural language response
            voice_response = self.intelligence_service.generate_voice_response(
                db_result,
                action.get('query_type'),
                context
            )

            # Update context
            self._update_context_from_db_result(context, db_result, action.get('query_type'))
            self._save_session_context(session_id, context)

            return {
                "success": db_result.get('status') == 'success',
                "session_id": session_id,
                "voice_response": voice_response,
                "database_result": db_result,
                "conversation_context": context
            }

        except Exception as e:
            return {
                "success": False,
                "session_id": session_id,
                "voice_response": "I apologize, but I encountered an issue processing that request.",
                "database_result": {
                    "status": "error",
                    "message": str(e),
                    "data": None
                }
            }

    def get_intent_and_action(
        self,
        voice_text: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get intent and database action without executing (for testing/debugging).

        Returns:
            {
                "understood_input": {...},
                "intent": {...},
                "database_action": {...},
                "missing_information": [...]
            }
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        context = self._get_session_context(session_id)

        # Understand input
        understood = self.intelligence_service.understand_voice_input(voice_text, context)

        # Identify intent
        intent = self.intelligence_service.identify_intent(
            understood.get('corrected_text', voice_text),
            context
        )

        # Generate database action
        db_action = self.intelligence_service.generate_database_action(
            intent,
            understood,
            context
        )

        # Identify missing information
        missing_info = self._identify_missing_information(intent, context)

        return {
            "understood_input": understood,
            "intent": intent,
            "database_action": db_action,
            "missing_information": missing_info,
            "conversation_context": context
        }

    # ========================
    # SESSION MANAGEMENT
    # ========================

    def _get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieve session context from cache."""
        context = cache.get(f'voice_session_{session_id}')

        if not context:
            context = {
                "session_id": session_id,
                "conversation_history": [],
                "collected_information": {},
                "current_intent": None,
                "last_action": None
            }

        return context

    def _save_session_context(self, session_id: str, context: Dict[str, Any]) -> None:
        """Save session context to cache (1 hour timeout)."""
        cache.set(f'voice_session_{session_id}', context, timeout=3600)

    def _update_context(
        self,
        context: Dict[str, Any],
        understood: Dict[str, Any],
        intent: Dict[str, Any]
    ) -> None:
        """Update context with new information from current interaction."""
        # Add to conversation history
        context['conversation_history'].append({
            "timestamp": str(uuid.uuid4()),  # Use UUID as simple timestamp
            "user_input": understood.get('corrected_text', ''),
            "intent": intent.get('intent'),
            "confidence": intent.get('confidence')
        })

        # Update collected information
        entities = understood.get('extracted_entities', {})
        for key, value in entities.items():
            if value:  # Only update if value exists
                context['collected_information'][key] = value

        # Update current intent
        context['current_intent'] = intent.get('intent')

    def _update_context_from_db_result(
        self,
        context: Dict[str, Any],
        db_result: Dict[str, Any],
        query_type: str
    ) -> None:
        """Update context with information from database result."""
        if db_result.get('status') == 'success':
            data = db_result.get('data', {})

            if query_type == 'create_appointment':
                context['collected_information']['appointment_id'] = data.get('appointment_id')
                context['collected_information']['booking_id'] = data.get('booking_id')
                context['last_action'] = 'appointment_created'

            elif query_type == 'appointment_lookup':
                if isinstance(data, list) and len(data) > 0:
                    context['collected_information']['appointments'] = data
                    context['last_action'] = 'appointments_retrieved'

            elif query_type == 'get_doctors':
                doctors_data = data.get('doctors', [])
                if doctors_data:
                    context['collected_information']['available_doctors'] = doctors_data
                    context['last_action'] = 'doctors_retrieved'

    def _identify_missing_information(
        self,
        intent: Dict[str, Any],
        context: Dict[str, Any]
    ) -> list:
        """Identify what information is still needed based on intent."""
        intent_type = intent.get('intent')
        collected = context.get('collected_information', {})

        missing = []

        if intent_type == 'appointment_booking':
            required = ['name', 'phone', 'doctor_name', 'date', 'time']
            missing = [field for field in required if not collected.get(field)]

        elif intent_type == 'appointment_lookup':
            if not collected.get('phone') and not collected.get('appointment_id'):
                missing = ['phone']

        elif intent_type == 'appointment_cancel':
            required = ['appointment_id', 'phone']
            missing = [field for field in required if not collected.get(field)]

        elif intent_type == 'appointment_reschedule':
            required = ['appointment_id', 'phone', 'date', 'time']
            missing = [field for field in required if not collected.get(field)]

        return missing

    def clear_session(self, session_id: str) -> bool:
        """Clear session context."""
        try:
            cache.delete(f'voice_session_{session_id}')
            return True
        except:
            return False

    def get_session_info(self, session_id: str) -> Dict[str, Any]:
        """Get current session information."""
        context = self._get_session_context(session_id)
        return {
            "session_id": session_id,
            "conversation_length": len(context.get('conversation_history', [])),
            "collected_information": context.get('collected_information', {}),
            "current_intent": context.get('current_intent'),
            "last_action": context.get('last_action')
        }
