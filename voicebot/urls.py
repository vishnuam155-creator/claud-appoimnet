"""
VoiceBot URL Configuration
"""

from django.urls import path
from . import views
from . import voice_intelligence_views

app_name = 'voicebot'

urlpatterns = [
    # Voice Assistant Page
    path('', views.voice_assistant_page, name='voice_assistant'),

    # Legacy API Endpoint for Voice Processing
    path('api/', views.VoiceAssistantAPIView.as_view(), name='api'),

    # Voice Intelligence API Endpoints (New Architecture)
    path('api/intelligence/', voice_intelligence_views.VoiceIntelligenceAPIView.as_view(), name='voice_intelligence'),
    path('api/database-action/', voice_intelligence_views.DatabaseActionAPIView.as_view(), name='database_action'),
    path('api/intent-analysis/', voice_intelligence_views.IntentAnalysisAPIView.as_view(), name='intent_analysis'),
    path('api/session/', voice_intelligence_views.SessionManagementAPIView.as_view(), name='session_management'),

    # Compatibility endpoint (uses new system with legacy format)
    path('api/v2/', voice_intelligence_views.VoicebotCompatibilityView.as_view(), name='api_v2'),
]
