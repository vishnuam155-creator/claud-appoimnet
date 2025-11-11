from django.urls import path
from . import views

app_name = 'patient_booking'

urlpatterns = [
    path('', views.home, name='home'),
    path('chatbot/', views.chatbot_page, name='chatbot'),
    path('voice-assistant/', views.voice_assistant_page, name='voice_assistant'),
    path('api/chatbot/', views.ChatbotAPIView.as_view(), name='chatbot_api'),
    path('api/voice/', views.VoiceAPIView.as_view(), name='voice_api'),
    path('api/voice-assistant/', views.VoiceAssistantAPIView.as_view(), name='voice_assistant_api'),
]
