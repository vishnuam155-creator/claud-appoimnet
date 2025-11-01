from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views import View
from django.utils.decorators import method_decorator
import json
import uuid
from chatbot.conversation_manager import ConversationManager


def chatbot_page(request):
    """Render the chatbot interface"""
    return render(request, 'patient_booking/chatbot.html')


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


def home(request):
    """Home page"""
    return render(request, 'patient_booking/home.html')
