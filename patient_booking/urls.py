from django.urls import path
from . import views
from .api_views import ChatbotAPIView, VoiceAPIView, VoiceAssistantAPIView

app_name = 'patient_booking'

urlpatterns = [
    # HTML Pages
    path('', views.home, name='home'),
    path('chatbot/', views.chatbot_page, name='chatbot'),
    path('voice-assistant/', views.voice_assistant_page, name='voice_assistant'),

    # REST API Endpoints
    path('api/chatbot/', ChatbotAPIView.as_view(), name='chatbot_api'),
    path('api/voice/', VoiceAPIView.as_view(), name='voice_api'),
    path('api/voice-assistant/', VoiceAssistantAPIView.as_view(), name='voice_assistant_api'),
]
