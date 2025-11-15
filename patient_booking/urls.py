"""
REST API URL Configuration for Patient Booking
All template-based routes have been removed - pure API endpoints only
"""
from django.urls import path
from . import views

app_name = 'patient_booking'

urlpatterns = [
    # Chatbot API
    path('api/chatbot/', views.ChatbotAPIView.as_view(), name='chatbot_api'),
    path('api/chatbot/reset/', views.chatbot_reset_session, name='chatbot_reset'),
    path('api/chatbot/debug/<str:session_id>/', views.chatbot_debug_session, name='chatbot_debug'),

    # Voice API
    path('api/voice/', views.VoiceAPIView.as_view(), name='voice_api'),

    # Voice Assistant API
    path('api/voice-assistant/', views.VoiceAssistantAPIView.as_view(), name='voice_assistant_api'),
]
