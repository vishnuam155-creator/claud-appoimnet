"""
VoiceBot URL Configuration
"""

from django.urls import path
from . import views
from . import voice_intelligence_views
from . import voice_provider_views
from . import asterisk_views

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

    # Voice Provider Configuration Endpoints
    path('api/voice-provider/config/', voice_provider_views.VoiceProviderConfigView.as_view(), name='voice_provider_config'),
    path('api/voice-provider/test/', voice_provider_views.VoiceProviderTestView.as_view(), name='voice_provider_test'),

    # AI4Bharat API Endpoints
    path('api/ai4bharat/languages/', voice_provider_views.AI4BharatLanguageView.as_view(), name='ai4bharat_languages'),
    path('api/ai4bharat/stt/', voice_provider_views.AI4BharatSpeechToTextView.as_view(), name='ai4bharat_stt'),
    path('api/ai4bharat/tts/', voice_provider_views.AI4BharatTextToSpeechView.as_view(), name='ai4bharat_tts'),

    # Asterisk Telephony Endpoints
    path('api/asterisk/incoming/', asterisk_views.AsteriskIncomingCallView.as_view(), name='asterisk_incoming'),
    path('api/asterisk/process/', asterisk_views.AsteriskCallProcessView.as_view(), name='asterisk_process'),
    path('api/asterisk/outbound/', asterisk_views.AsteriskOutboundCallView.as_view(), name='asterisk_outbound'),
    path('api/asterisk/active-calls/', asterisk_views.AsteriskActiveCallsView.as_view(), name='asterisk_active_calls'),
    path('api/asterisk/end-call/', asterisk_views.AsteriskEndCallView.as_view(), name='asterisk_end_call'),
    path('api/asterisk/webhook/', asterisk_views.AsteriskWebhookView.as_view(), name='asterisk_webhook'),
]
