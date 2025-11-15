"""
VoiceBot REST API URL Configuration
Pure REST API - No template rendering
"""

from django.urls import path
from . import views
from . import voice_intelligence_views

app_name = 'voicebot'

urlpatterns = [
    # ========== Voice Assistant REST API ==========
    # Main API endpoint for voice-based conversation
    path('api/', views.VoiceAssistantAPIView.as_view(), name='api'),

    # ========== Voice Intelligence API Endpoints ==========
    # Advanced AI-powered voice intelligence system
    path('api/intelligence/', voice_intelligence_views.VoiceIntelligenceAPIView.as_view(), name='voice_intelligence'),
    path('api/database-action/', voice_intelligence_views.DatabaseActionAPIView.as_view(), name='database_action'),
    path('api/intent-analysis/', voice_intelligence_views.IntentAnalysisAPIView.as_view(), name='intent_analysis'),
    path('api/session/', voice_intelligence_views.SessionManagementAPIView.as_view(), name='session_management'),

    # ========== Compatibility Endpoint ==========
    # V2 endpoint with enhanced features
    path('api/v2/', voice_intelligence_views.VoicebotCompatibilityView.as_view(), name='api_v2'),
]

# NOTE: Template-based views have been removed. This is now a pure REST API.
# Frontend applications should consume these API endpoints directly.
#
# For frontend integration, see:
# - GET /voicebot/api/ for API documentation
# - POST /voicebot/api/ for voice conversation
#
# Recommended Frontend Stack:
# - React + react-speech-recognition
# - Vue.js + vue-speech
# - Vanilla JS + Web Speech API
