from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta
from .models import Specialization, Doctor, DoctorSchedule, DoctorLeave
from .serializers import (
    SpecializationSerializer,
    DoctorListSerializer,
    DoctorDetailSerializer,
    DoctorCreateUpdateSerializer,
    DoctorScheduleSerializer,
    DoctorLeaveSerializer,
    AvailabilitySlotSerializer
)


class SpecializationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing specializations

    list: Get all specializations
    create: Create a new specialization
    retrieve: Get a specific specialization
    update: Update a specialization
    partial_update: Partially update a specialization
    destroy: Delete a specialization
    """
    queryset = Specialization.objects.all()
    serializer_class = SpecializationSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'keywords']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def doctors(self, request, pk=None):
        """Get all doctors for a specific specialization"""
        specialization = self.get_object()
        doctors = specialization.doctors.filter(is_active=True)
        serializer = DoctorListSerializer(doctors, many=True, context={'request': request})
        return Response(serializer.data)


class DoctorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctors

    list: Get all doctors (filterable by specialization, is_active)
    create: Create a new doctor
    retrieve: Get a specific doctor with full details
    update: Update a doctor
    partial_update: Partially update a doctor
    destroy: Delete a doctor
    search: Search doctors by name
    availability: Get available slots for a doctor
    """
    queryset = Doctor.objects.select_related('specialization').prefetch_related(
        'schedules', 'leaves'
    ).all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['specialization', 'is_active']
    search_fields = ['name', 'qualification', 'bio']
    ordering_fields = ['name', 'experience_years', 'consultation_fee', 'created_at']
    ordering = ['name']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return DoctorListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DoctorCreateUpdateSerializer
        return DoctorDetailSerializer

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search doctors by name or specialization
        Query params: ?q=search_term
        """
        search_term = request.query_params.get('q', '')
        if not search_term:
            return Response(
                {'error': 'Search term is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        doctors = self.queryset.filter(
            models.Q(name__icontains=search_term) |
            models.Q(specialization__name__icontains=search_term) |
            models.Q(qualification__icontains=search_term),
            is_active=True
        )

        serializer = DoctorListSerializer(doctors, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def availability(self, request, pk=None):
        """
        Get available time slots for a doctor
        Query params:
        - ?date=YYYY-MM-DD (required)
        - ?days=N (optional, default=1, get N days from date)
        """
        doctor = self.get_object()
        date_str = request.query_params.get('date')
        days = int(request.query_params.get('days', 1))

        if not date_str:
            return Response(
                {'error': 'Date parameter is required (format: YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if start_date < timezone.now().date():
            return Response(
                {'error': 'Cannot get availability for past dates'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate available slots
        from appointments.models import Appointment
        available_slots = []

        for day_offset in range(days):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()

            # Check if doctor has schedule for this day
            schedules = doctor.schedules.filter(
                day_of_week=day_of_week,
                is_active=True
            )

            if not schedules.exists():
                continue

            # Check if doctor is on leave
            is_on_leave = doctor.leaves.filter(
                start_date__lte=current_date,
                end_date__gte=current_date
            ).exists()

            if is_on_leave:
                continue

            # Generate time slots
            for schedule in schedules:
                current_time = schedule.start_time
                end_time = schedule.end_time
                slot_duration = timedelta(minutes=schedule.slot_duration)

                while current_time < end_time:
                    # Check if slot is already booked
                    is_booked = Appointment.objects.filter(
                        doctor=doctor,
                        appointment_date=current_date,
                        appointment_time=current_time,
                        status__in=['pending', 'confirmed']
                    ).exists()

                    # Check if slot is in the past
                    slot_datetime = datetime.combine(current_date, current_time)
                    is_past = slot_datetime < datetime.now()

                    slot_info = {
                        'date': current_date,
                        'time': current_time,
                        'doctor': doctor.id,
                        'doctor_name': doctor.name,
                        'is_available': not is_booked and not is_past,
                        'reason': ''
                    }

                    if is_booked:
                        slot_info['reason'] = 'Already booked'
                    elif is_past:
                        slot_info['reason'] = 'Past time'

                    available_slots.append(slot_info)

                    # Move to next slot
                    current_time_dt = datetime.combine(current_date, current_time)
                    next_time_dt = current_time_dt + slot_duration
                    current_time = next_time_dt.time()

        serializer = AvailabilitySlotSerializer(available_slots, many=True)
        return Response({
            'doctor': DoctorListSerializer(doctor, context={'request': request}).data,
            'date_range': {
                'start': start_date,
                'end': start_date + timedelta(days=days - 1)
            },
            'slots': serializer.data
        })

    @action(detail=True, methods=['get'])
    def schedules(self, request, pk=None):
        """Get all schedules for a doctor"""
        doctor = self.get_object()
        schedules = doctor.schedules.filter(is_active=True).order_by('day_of_week', 'start_time')
        serializer = DoctorScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_schedule(self, request, pk=None):
        """Add a schedule for a doctor"""
        doctor = self.get_object()
        data = request.data.copy()
        data['doctor'] = doctor.id

        serializer = DoctorScheduleSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def leaves(self, request, pk=None):
        """Get all leaves for a doctor"""
        doctor = self.get_object()
        upcoming = request.query_params.get('upcoming', 'false').lower() == 'true'

        leaves = doctor.leaves.all()
        if upcoming:
            leaves = leaves.filter(end_date__gte=timezone.now().date())

        serializer = DoctorLeaveSerializer(leaves, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_leave(self, request, pk=None):
        """Add a leave for a doctor"""
        doctor = self.get_object()
        data = request.data.copy()
        data['doctor'] = doctor.id

        serializer = DoctorLeaveSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctor schedules
    """
    queryset = DoctorSchedule.objects.select_related('doctor').all()
    serializer_class = DoctorScheduleSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['doctor', 'day_of_week', 'is_active']
    ordering_fields = ['day_of_week', 'start_time']
    ordering = ['doctor', 'day_of_week', 'start_time']


class DoctorLeaveViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing doctor leaves
    """
    queryset = DoctorLeave.objects.select_related('doctor').all()
    serializer_class = DoctorLeaveSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['doctor']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        """Filter upcoming leaves if requested"""
        queryset = super().get_queryset()
        upcoming = self.request.query_params.get('upcoming', 'false').lower() == 'true'

        if upcoming:
            queryset = queryset.filter(end_date__gte=timezone.now().date())

        return queryset
