from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Q
from .models import Appointment, AppointmentHistory, SMSNotification
from .serializers import (
    AppointmentListSerializer,
    AppointmentDetailSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
    AppointmentStatusUpdateSerializer,
    AppointmentRescheduleSerializer,
    AppointmentHistorySerializer,
    SMSNotificationSerializer,
    PatientLookupSerializer
)


class AppointmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing appointments

    list: Get all appointments (filterable by doctor, status, date)
    create: Create a new appointment
    retrieve: Get a specific appointment with full details
    update: Update appointment details
    partial_update: Partially update appointment
    destroy: Cancel an appointment
    """
    queryset = Appointment.objects.select_related(
        'doctor', 'doctor__specialization'
    ).prefetch_related(
        'history', 'sms_notifications'
    ).all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['doctor', 'status', 'appointment_date']
    search_fields = ['patient_name', 'patient_phone', 'patient_email', 'booking_id']
    ordering_fields = ['appointment_date', 'appointment_time', 'created_at']
    ordering = ['-appointment_date', '-appointment_time']
    lookup_field = 'booking_id'

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return AppointmentListSerializer
        elif self.action == 'create':
            return AppointmentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AppointmentUpdateSerializer
        return AppointmentDetailSerializer

    def get_queryset(self):
        """Filter appointments based on query parameters"""
        queryset = super().get_queryset()

        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(appointment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(appointment_date__lte=end_date)

        # Filter upcoming appointments
        upcoming = self.request.query_params.get('upcoming', 'false').lower() == 'true'
        if upcoming:
            queryset = queryset.filter(
                appointment_date__gte=timezone.now().date(),
                status__in=['pending', 'confirmed']
            )

        # Filter by patient phone
        phone = self.request.query_params.get('phone')
        if phone:
            queryset = queryset.filter(patient_phone=phone)

        return queryset

    def create(self, request, *args, **kwargs):
        """Create appointment and send SMS notification"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()

        # Send SMS notification
        from twilio_service import send_appointment_confirmation_sms
        try:
            send_appointment_confirmation_sms(appointment)
        except Exception as e:
            # Log error but don't fail the request
            print(f"Failed to send SMS: {str(e)}")

        # Return detailed appointment data
        detail_serializer = AppointmentDetailSerializer(
            appointment,
            context={'request': request}
        )
        return Response(
            detail_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch'])
    def update_status(self, request, booking_id=None):
        """
        Update appointment status
        Body: {"status": "confirmed|cancelled|completed|no_show", "reason": "...", "changed_by": "..."}
        """
        appointment = self.get_object()
        serializer = AppointmentStatusUpdateSerializer(
            appointment,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            updated_appointment = serializer.save()

            # Send SMS notification for status change
            if updated_appointment.status == 'cancelled':
                from twilio_service import send_appointment_cancelled_sms
                try:
                    send_appointment_cancelled_sms(updated_appointment)
                except Exception as e:
                    print(f"Failed to send SMS: {str(e)}")

            detail_serializer = AppointmentDetailSerializer(
                updated_appointment,
                context={'request': request}
            )
            return Response(detail_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def reschedule(self, request, booking_id=None):
        """
        Reschedule an appointment
        Body: {"new_date": "YYYY-MM-DD", "new_time": "HH:MM:SS", "reason": "...", "changed_by": "..."}
        """
        appointment = self.get_object()

        if appointment.status not in ['pending', 'confirmed']:
            return Response(
                {'error': 'Only pending or confirmed appointments can be rescheduled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AppointmentRescheduleSerializer(
            appointment,
            data=request.data
        )

        if serializer.is_valid():
            updated_appointment = serializer.save()

            # Send SMS notification for reschedule
            from twilio_service import send_appointment_rescheduled_sms
            try:
                send_appointment_rescheduled_sms(updated_appointment)
            except Exception as e:
                print(f"Failed to send SMS: {str(e)}")

            detail_serializer = AppointmentDetailSerializer(
                updated_appointment,
                context={'request': request}
            )
            return Response(detail_serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, booking_id=None):
        """
        Cancel an appointment
        Body: {"reason": "...", "changed_by": "..."}
        """
        return self.update_status(request, booking_id)

    @action(detail=True, methods=['get'])
    def history(self, request, booking_id=None):
        """Get appointment history"""
        appointment = self.get_object()
        history = appointment.history.all()
        serializer = AppointmentHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def notifications(self, request, booking_id=None):
        """Get SMS notifications for an appointment"""
        appointment = self.get_object()
        notifications = appointment.sms_notifications.all()
        serializer = SMSNotificationSerializer(notifications, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def search_patient(self, request):
        """
        Search for appointments by patient phone or email
        Body: {"phone": "...", "email": "..."}
        """
        serializer = PatientLookupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data.get('phone')
        email = serializer.validated_data.get('email')

        queryset = self.queryset
        if phone:
            queryset = queryset.filter(patient_phone=phone)
        if email:
            queryset = queryset.filter(patient_email=email)

        appointments = queryset.order_by('-appointment_date', '-appointment_time')

        # Group by status
        result = {
            'patient_phone': phone,
            'patient_email': email,
            'upcoming': [],
            'past': [],
            'cancelled': []
        }

        for appointment in appointments:
            serialized = AppointmentListSerializer(
                appointment,
                context={'request': request}
            ).data

            if appointment.status == 'cancelled':
                result['cancelled'].append(serialized)
            elif appointment.appointment_date >= timezone.now().date():
                result['upcoming'].append(serialized)
            else:
                result['past'].append(serialized)

        return Response(result)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get appointment statistics"""
        from django.db.models import Count

        total = self.queryset.count()
        by_status = dict(
            self.queryset.values('status').annotate(count=Count('id')).values_list('status', 'count')
        )

        upcoming = self.queryset.filter(
            appointment_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).count()

        today = self.queryset.filter(
            appointment_date=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).count()

        return Response({
            'total': total,
            'by_status': by_status,
            'upcoming': upcoming,
            'today': today
        })


class AppointmentHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing appointment history (read-only)
    """
    queryset = AppointmentHistory.objects.select_related('appointment').all()
    serializer_class = AppointmentHistorySerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['appointment', 'action', 'changed_by']
    ordering_fields = ['changed_at']
    ordering = ['-changed_at']


class SMSNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing SMS notifications (read-only)
    """
    queryset = SMSNotification.objects.select_related('appointment').all()
    serializer_class = SMSNotificationSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['appointment', 'notification_type', 'status']
    ordering_fields = ['sent_at', 'updated_at']
    ordering = ['-sent_at']

    @action(detail=False, methods=['post'])
    def resend(self, request):
        """
        Resend SMS notification
        Body: {"appointment_id": "...", "notification_type": "confirmation|reminder|cancellation|reschedule"}
        """
        appointment_id = request.data.get('appointment_id')
        notification_type = request.data.get('notification_type', 'reminder')

        if not appointment_id:
            return Response(
                {'error': 'appointment_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            appointment = Appointment.objects.get(booking_id=appointment_id)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Send SMS based on type
        from twilio_service import (
            send_appointment_confirmation_sms,
            send_appointment_reminder_sms,
            send_appointment_cancelled_sms,
            send_appointment_rescheduled_sms
        )

        try:
            if notification_type == 'confirmation':
                sms_notification = send_appointment_confirmation_sms(appointment)
            elif notification_type == 'reminder':
                sms_notification = send_appointment_reminder_sms(appointment)
            elif notification_type == 'cancellation':
                sms_notification = send_appointment_cancelled_sms(appointment)
            elif notification_type == 'reschedule':
                sms_notification = send_appointment_rescheduled_sms(appointment)
            else:
                return Response(
                    {'error': 'Invalid notification_type'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if sms_notification:
                serializer = SMSNotificationSerializer(sms_notification)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': 'Failed to send SMS'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
