from django.urls import path
from . import views

app_name = 'patient_booking'

urlpatterns = [
    path('', views.home, name='home'),
    path('chatbot/', views.chatbot_page, name='chatbot'),
    path('api/chatbot/', views.ChatbotAPIView.as_view(), name='chatbot_api'),
]
