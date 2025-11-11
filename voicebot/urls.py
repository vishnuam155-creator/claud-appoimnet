"""
VoiceBot URL Configuration
"""

from django.urls import path
from . import views

app_name = 'voicebot'

urlpatterns = [
    # Voice Assistant Page
    path('', views.voice_assistant_page, name='voice_assistant'),

    # API Endpoint for Voice Processing
    path('api/', views.VoiceAssistantAPIView.as_view(), name='api'),
]
