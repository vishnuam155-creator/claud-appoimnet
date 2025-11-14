"""
REST API views for Admin Panel
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from django.db.models import Q, Count
from datetime import datetime, timedelta
import calendar

from appointments.models import Appointment, AppointmentHistory
from appointments.serializers import (
    AppointmentSerializer,
    AppointmentDetailSerializer,
    AppointmentUpdateSerializer
)
from doctors.models import Doctor


class DashboardStatsAPIView(APIView):
    """
    API endpoint for dashboard statistics
    GET: Returns appointment statistics
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get dashboard statistics"""
        today = datetime.now().date()

        # Calculate statistics
        total_appointments = Appointment.objects.count()
        today_appointments = Appointment.objects.filter(appointment_date=today).count()
        pending_appointments = Appointment.objects.filter(status='pending').count()
        confirmed_appointments = Appointment.objects.filter(status='confirmed').count()

        # Upcoming appointments (next 7 days)
        upcoming = Appointment.objects.filter(
            appointment_date__gte=today,
            appointment_date__lte=today + timedelta(days=7),
            status__in=['pending', 'confirmed']
        ).order_by('appointment_date', 'appointment_time')[:10]

        # Recent appointments
        recent = Appointment.objects.all().order_by('-created_at')[:10]

        # Status breakdown
        status_breakdown = Appointment.objects.values('status').annotate(
            count=Count('id')
        ).order_by('-count')

        return Response({
            'success': True,
            'statistics': {
                'total_appointments': total_appointments,
                'today_appointments': today_appointments,
                'pending_appointments': pending_appointments,
                'confirmed_appointments': confirmed_appointments,
            },
            'upcoming_appointments': AppointmentSerializer(upcoming, many=True).data,
            'recent_appointments': AppointmentSerializer(recent, many=True).data,
            'status_breakdown': list(status_breakdown)
        })


class AppointmentListAPIView(APIView):
    """
    API endpoint for appointment list with filters
    GET: Returns filtered list of appointments
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """List appointments with filters"""
        appointments = Appointment.objects.all().select_related('doctor', 'doctor__specialization')

        # Apply filters
        status_filter = request.GET.get('status')
        doctor_id = request.GET.get('doctor')
        date = request.GET.get('date')
        search = request.GET.get('search')

        if status_filter:
            appointments = appointments.filter(status=status_filter)

        if doctor_id:
            appointments = appointments.filter(doctor_id=doctor_id)

        if date:
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d').date()
                appointments = appointments.filter(appointment_date=date_obj)
            except ValueError:
                return Response({
                    'success': False,
                    'error': 'Invalid date format. Use YYYY-MM-DD'
                }, status=status.HTTP_400_BAD_REQUEST)

        if search:
            appointments = appointments.filter(
                Q(patient_name__icontains=search) |
                Q(patient_phone__icontains=search) |
                Q(booking_id__icontains=search)
            )

        appointments = appointments.order_by('-appointment_date', '-appointment_time')

        # Pagination
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        end = start + page_size

        total_count = appointments.count()
        appointments_page = appointments[start:end]

        return Response({
            'success': True,
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'appointments': AppointmentSerializer(appointments_page, many=True).data
        })


class AppointmentDetailAPIView(APIView):
    """
    API endpoint for appointment details
    GET: Returns detailed appointment information
    """
    permission_classes = [IsAdminUser]

    def get(self, request, booking_id):
        """Get appointment details"""
        try:
            appointment = Appointment.objects.select_related(
                'doctor',
                'doctor__specialization'
            ).prefetch_related(
                'history',
                'sms_notifications'
            ).get(booking_id=booking_id)

            return Response({
                'success': True,
                'appointment': AppointmentDetailSerializer(appointment).data
            })

        except Appointment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Appointment not found'
            }, status=status.HTTP_404_NOT_FOUND)


class AppointmentUpdateStatusAPIView(APIView):
    """
    API endpoint for updating appointment status
    PUT/PATCH: Update appointment status
    """
    permission_classes = [IsAdminUser]

    def put(self, request, booking_id):
        return self.update_status(request, booking_id)

    def patch(self, request, booking_id):
        return self.update_status(request, booking_id)

    def update_status(self, request, booking_id):
        """Update appointment status"""
        try:
            appointment = Appointment.objects.get(booking_id=booking_id)

            serializer = AppointmentUpdateSerializer(
                appointment,
                data=request.data,
                partial=True
            )

            if serializer.is_valid():
                serializer.save()

                return Response({
                    'success': True,
                    'message': f'Appointment status updated to {appointment.status}',
                    'appointment': AppointmentSerializer(appointment).data
                })

            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        except Appointment.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Appointment not found'
            }, status=status.HTTP_404_NOT_FOUND)


class CalendarDataAPIView(APIView):
    """
    API endpoint for calendar view data
    GET: Returns appointments grouped by date for a specific month
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get calendar data for a specific month"""
        today = datetime.now().date()
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))

        try:
            # Validate month and year
            if not (1 <= month <= 12):
                return Response({
                    'success': False,
                    'error': 'Invalid month. Must be between 1 and 12'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get appointments for this month
            appointments = Appointment.objects.filter(
                appointment_date__year=year,
                appointment_date__month=month
            ).select_related('doctor', 'doctor__specialization')

            # Group by date
            appointments_by_date = {}
            for apt in appointments:
                date_key = apt.appointment_date.strftime('%Y-%m-%d')
                if date_key not in appointments_by_date:
                    appointments_by_date[date_key] = {
                        'count': 0,
                        'appointments': []
                    }
                appointments_by_date[date_key]['count'] += 1
                appointments_by_date[date_key]['appointments'].append(
                    AppointmentSerializer(apt).data
                )

            # Generate calendar data
            cal = calendar.monthcalendar(year, month)
            month_name = calendar.month_name[month]

            # Calculate previous and next month/year
            if month == 1:
                prev_month, prev_year = 12, year - 1
            else:
                prev_month, prev_year = month - 1, year

            if month == 12:
                next_month, next_year = 1, year + 1
            else:
                next_month, next_year = month + 1, year

            return Response({
                'success': True,
                'year': year,
                'month': month,
                'month_name': month_name,
                'calendar_weeks': cal,
                'appointments_by_date': appointments_by_date,
                'today': today.strftime('%Y-%m-%d'),
                'navigation': {
                    'prev_month': prev_month,
                    'prev_year': prev_year,
                    'next_month': next_month,
                    'next_year': next_year
                }
            })

        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AppointmentsByDateAPIView(APIView):
    """
    API endpoint to fetch appointments for a specific date
    GET: Returns appointments for the specified date
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Fetch appointments for a specific date"""
        date_str = request.GET.get('date')

        if not date_str:
            return Response({
                'success': False,
                'error': 'Date parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Parse the date
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

            # Fetch appointments for this date
            appointments = Appointment.objects.filter(
                appointment_date=date_obj
            ).select_related('doctor', 'doctor__specialization').order_by('appointment_time')

            return Response({
                'success': True,
                'date': date_str,
                'count': appointments.count(),
                'appointments': AppointmentSerializer(appointments, many=True).data
            })

        except ValueError:
            return Response({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
