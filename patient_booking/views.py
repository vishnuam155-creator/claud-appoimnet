"""
Views for rendering HTML templates.
API logic has been moved to api_views.py
"""
from django.shortcuts import render


def home(request):
    """Home page"""
    return render(request, 'patient_booking/home.html')


def chatbot_page(request):
    """Render the chatbot interface"""
    return render(request, 'patient_booking/chatbot.html')




def voice_assistant_page(request):
    """Render the voice assistant interface"""
    return render(request, 'patient_booking/voice_assistant.html')
