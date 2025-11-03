"""
URL Configuration for WhatsApp Integration
"""
from django.urls import path
from . import views

app_name = 'whatsapp_integration'

urlpatterns = [
    # Twilio webhook endpoints
    path('webhook/', views.whatsapp_webhook, name='webhook'),
    path('webhook/status/', views.whatsapp_status_webhook, name='status_webhook'),

    # Web interface
    path('chat/', views.whatsapp_chat_interface, name='chat_interface'),

    # Admin dashboard
    path('admin/dashboard/', views.whatsapp_admin_dashboard, name='admin_dashboard'),
    path('admin/session/<str:session_id>/messages/', views.session_messages, name='session_messages'),
]
