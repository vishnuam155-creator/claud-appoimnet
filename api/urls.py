from django.urls import path, include
from rest_framework.routers import DefaultRouter
from doctors.viewsets import (
    SpecializationViewSet,
    DoctorViewSet,
    DoctorScheduleViewSet,
    DoctorLeaveViewSet
)
from appointments.viewsets import (
    AppointmentViewSet,
    AppointmentHistoryViewSet,
    SMSNotificationViewSet
)

# Create router
router = DefaultRouter()

# Register Doctor module endpoints
router.register(r'specializations', SpecializationViewSet, basename='specialization')
router.register(r'doctors', DoctorViewSet, basename='doctor')
router.register(r'schedules', DoctorScheduleViewSet, basename='schedule')
router.register(r'leaves', DoctorLeaveViewSet, basename='leave')

# Register Appointment module endpoints
router.register(r'appointments', AppointmentViewSet, basename='appointment')
router.register(r'appointment-history', AppointmentHistoryViewSet, basename='appointment-history')
router.register(r'sms-notifications', SMSNotificationViewSet, basename='sms-notification')

urlpatterns = [
    path('v1/', include(router.urls)),
]
