"""
REST API URL Configuration for WhatsApp Integration
All template-based routes have been removed - pure API endpoints only
"""
from django.urls import path
from . import views

app_name = 'whatsapp_integration'

urlpatterns = [
    # Meta WhatsApp webhook endpoints
    path('webhook/', views.whatsapp_webhook, name='webhook'),
    path('webhook/status/', views.whatsapp_status_webhook, name='status_webhook'),

    # Session and message APIs
    path('api/sessions/', views.whatsapp_sessions_api, name='sessions_api'),
    path('api/sessions/<str:session_id>/messages/', views.session_messages_api, name='session_messages_api'),
]
