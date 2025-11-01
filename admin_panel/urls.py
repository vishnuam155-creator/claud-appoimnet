from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<str:booking_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<str:booking_id>/update/', views.update_appointment_status, name='update_status'),
    path('calendar/', views.calendar_view, name='calendar'),
]
