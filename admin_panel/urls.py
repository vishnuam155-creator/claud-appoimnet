"""
REST API URL Configuration for Admin Panel
All template-based routes have been removed - pure API endpoints only
"""
from django.urls import path
from . import api_views

app_name = 'admin_panel'

urlpatterns = [
    # Dashboard statistics
    path('api/dashboard/', api_views.DashboardStatsAPIView.as_view(), name='dashboard_stats'),

    # Appointment management
    path('api/appointments/', api_views.AppointmentListAPIView.as_view(), name='appointment_list'),
    path('api/appointments/<str:booking_id>/', api_views.AppointmentDetailAPIView.as_view(), name='appointment_detail'),
    path('api/appointments/<str:booking_id>/update/', api_views.AppointmentUpdateStatusAPIView.as_view(), name='update_status'),

    # Calendar endpoints
    path('api/calendar/', api_views.CalendarDataAPIView.as_view(), name='calendar_data'),
    path('api/appointments-by-date/', api_views.AppointmentsByDateAPIView.as_view(), name='appointments_by_date'),
]
