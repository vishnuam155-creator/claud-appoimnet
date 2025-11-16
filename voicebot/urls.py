"""
VoiceBot REST API URL Configuration
Pure REST API - No template rendering
Enhanced with RAG (Retrieval-Augmented Generation) System
"""

from django.urls import path
from . import views
from . import views_rag
from . import voice_intelligence_views

app_name = 'voicebot'

urlpatterns = [
    # ========== RAG-Powered Voice Assistant API (NEW - Recommended) ==========
    # Advanced RAG-based conversation with Gemini 2.5 Flash
    # Full context awareness, natural conversation, handles changes at any stage
    path('api/', views_rag.VoiceAssistantRAGAPIView.as_view(), name='api'),
    path('api/rag/', views_rag.VoiceAssistantRAGAPIView.as_view(), name='api_rag'),

    # ========== Legacy Voice Assistant API ==========
    # Original implementation (kept for backwards compatibility)
    path('api/legacy/', views.VoiceAssistantAPIView.as_view(), name='api_legacy'),

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
