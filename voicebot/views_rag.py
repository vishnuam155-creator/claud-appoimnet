"""
VoiceBot REST API Views with RAG System - Complete Restructure
Gemini 2.5 Flash-powered natural conversational appointment booking with RAG

This module provides REST API endpoints for voice-based appointment booking
using advanced RAG (Retrieval-Augmented Generation) for natural conversations.
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
from django.utils import timezone
import json
import uuid

from voicebot.voice_assistant_manager_rag import VoiceAssistantManagerRAG


@method_decorator(csrf_exempt, name='dispatch')
class VoiceAssistantRAGAPIView(View):
    """
    RAG-powered API endpoint for voice assistant conversation
    Uses Gemini 2.5 Flash with full database context and conversation history
    """

    def post(self, request):
        """Process voice message with RAG-based understanding"""
        try:
            # Handle empty request body
            if not request.body or request.body.strip() == b'':
                return JsonResponse({
                    'success': False,
                    'error': 'Empty request body',
                    'message': 'Please send a valid JSON request with your message.'
                }, status=400)

            # Parse request data
            content_type = request.META.get('CONTENT_TYPE', '').lower()

            # Support both JSON and form data
            if 'application/json' in content_type:
                try:
                    data = json.loads(request.body)
                    message = data.get('message', '')
                    session_id = data.get('session_id')
                except json.JSONDecodeError as e:
                    print(f"VoiceBot JSON decode error: {e}")
                    return JsonResponse({
                        'success': False,
                        'error': 'Invalid JSON format',
                        'message': 'Please send valid JSON data.'
                    }, status=400)

            elif 'multipart/form-data' in content_type or 'application/x-www-form-urlencoded' in content_type:
                message = request.POST.get('message') or request.POST.get('text', '')
                session_id = request.POST.get('session_id')

            else:
                # Try JSON first, then form data
                try:
                    data = json.loads(request.body)
                    message = data.get('message', '')
                    session_id = data.get('session_id')
                except:
                    message = request.POST.get('message') or request.POST.get('text', '')
                    session_id = request.POST.get('session_id')

            # Generate session ID if not provided
            if not session_id:
                session_id = f"voice_{uuid.uuid4().hex[:12]}"

            # Process message with RAG-powered assistant
            manager = VoiceAssistantManagerRAG(session_id)
            response = manager.process_voice_message(message)

            return JsonResponse({
                'success': response.get('success', True),
                'session_id': session_id,
                'message': response['message'],
                'stage': response['stage'],
                'action': response['action'],
                'data': response['data']
            })

        except Exception as e:
            import traceback
            print(f"Voice assistant error: {e}")
            traceback.print_exc()

            return JsonResponse({
                'success': False,
                'error': str(e),
                'message': 'I apologize, I encountered an error. Could you please repeat that?'
            }, status=500)

    def get(self, request):
        """Return comprehensive RAG API information"""
        return JsonResponse({
            'success': True,
            'message': 'Voice Assistant RAG API - Gemini 2.5 Flash with Retrieval-Augmented Generation',
            'version': '3.0 RAG',
            'timestamp': timezone.now().isoformat(),
            'api_info': {
                'ai_model': 'Google Gemini 2.5 Flash',
                'architecture': 'RAG (Retrieval-Augmented Generation)',
                'endpoint': '/voicebot/api/rag/',
                'method': 'POST',
                'content_type': 'application/json or multipart/form-data',
                'authentication': 'None (can be added)',
                'rate_limit': 'Configurable'
            },
            'features': [
                'Full conversation history with persistent storage',
                'Real-time database context retrieval (doctors, slots, schedules)',
                'Natural language understanding for complex queries',
                'Dynamic change handling - modify any detail at any stage',
                'Intelligent slot availability checking with alternatives',
                'Symptom-based doctor recommendation',
                'Proactive suggestions and helpful guidance',
                'Handles interruptions and topic changes naturally',
                'Multi-turn context-aware conversations',
                'Senior receptionist-like behavior'
            ],
            'rag_components': {
                'retriever': 'RAGRetriever - Fetches relevant context from database',
                'context_manager': 'ConversationContextManager - Manages conversation state',
                'llm_service': 'GeminiRAGService - Generates responses with full context',
                'assistant_manager': 'VoiceAssistantManagerRAG - Orchestrates the flow'
            },
            'request_format': {
                'message': {
                    'type': 'string',
                    'required': True,
                    'description': 'User voice input (transcribed text)',
                    'example': 'I want to book an appointment'
                },
                'session_id': {
                    'type': 'string',
                    'required': False,
                    'description': 'Session ID for conversation continuity (auto-generated if not provided)',
                    'example': 'voice_abc123def456'
                }
            },
            'response_format': {
                'success': 'boolean - Operation success status',
                'session_id': 'string - Session identifier for conversation continuity',
                'message': 'string - Natural conversational response from AI',
                'stage': 'string - Current conversation stage',
                'action': 'string - Action type (continue/booking_complete/cancelled/error)',
                'data': 'object - Complete booking state and collected information'
            },
            'conversation_flow': {
                'stages': [
                    'greeting - Initial welcome',
                    'patient_name - Collect patient name',
                    'doctor_selection - Select doctor by name or symptoms',
                    'date_selection - Choose appointment date',
                    'time_selection - Select time slot',
                    'phone_collection - Collect contact number',
                    'confirmation - Final confirmation',
                    'completed - Booking completed successfully'
                ],
                'note': 'Stages are flexible - system can handle changes at any point'
            },
            'special_capabilities': {
                'change_handling': 'Can modify doctor, date, time, or any detail at any stage',
                'symptom_analysis': 'Analyzes symptoms and recommends appropriate specialist',
                'slot_checking': 'Real-time availability checking with alternative suggestions',
                'natural_conversation': 'Understands context and handles natural speech patterns',
                'error_recovery': 'Graceful handling of errors and unclear inputs'
            },
            'example_conversation': {
                'step_1': {
                    'user': 'Hello',
                    'assistant': 'Hello! Welcome to MedCare Clinic. I\'m here to help you book an appointment. May I have your name, please?'
                },
                'step_2': {
                    'user': 'My name is John',
                    'assistant': 'Nice to meet you, John! How can I help you today? You can tell me which doctor you\'d like to see, or describe any symptoms you\'re experiencing.'
                },
                'step_3': {
                    'user': 'I have a severe headache',
                    'assistant': 'I understand you\'re experiencing a severe headache. Based on your symptoms, I recommend seeing a Neurologist. We have Dr. Smith who specializes in this area. Would you like to book with Dr. Smith?'
                },
                'step_4': {
                    'user': 'Actually, I prefer Dr. Johnson',
                    'assistant': 'No problem! Let me check Dr. Johnson\'s availability. What date would work best for you?'
                },
                'note': 'This is just a sample - the system handles natural, flexible conversations'
            },
            'deployment_notes': {
                'database': 'Requires VoiceConversation and ConversationMessage models',
                'migrations': 'Run migrations before use: python manage.py makemigrations && python manage.py migrate',
                'dependencies': 'Requires google-generativeai package'
            }
        })
