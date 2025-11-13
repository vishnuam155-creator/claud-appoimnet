from rest_framework import serializers
from .models import Appointment, AppointmentHistory, SMSNotification
from doctors.serializers import DoctorListSerializer


class AppointmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for appointment history"""

    class Meta:
        model = AppointmentHistory
        fields = ['id', 'appointment', 'status', 'notes', 'changed_by',
                  'changed_at', 'action', 'old_date', 'old_time', 'new_date',
                  'new_time', 'reason']
        read_only_fields = ['id', 'changed_at']


class SMSNotificationSerializer(serializers.ModelSerializer):
    """Serializer for SMS notifications"""

    class Meta:
        model = SMSNotification
        fields = ['id', 'appointment', 'notification_type', 'phone_number',
                  'message_body', 'message_sid', 'status', 'error_message',
                  'sent_at', 'updated_at']
        read_only_fields = ['id', 'sent_at', 'updated_at']


class AppointmentListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for appointment list view"""
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    specialization_name = serializers.CharField(source='doctor.specialization.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'booking_id', 'doctor', 'doctor_name', 'specialization_name',
                  'patient_name', 'patient_phone', 'appointment_date',
                  'appointment_time', 'status', 'status_display', 'symptoms',
                  'created_at']
        read_only_fields = ['id', 'booking_id', 'created_at']


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for appointment detail view"""
    doctor_detail = DoctorListSerializer(source='doctor', read_only=True)
    history = AppointmentHistorySerializer(many=True, read_only=True)
    sms_notifications = SMSNotificationSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    gender_display = serializers.CharField(source='get_patient_gender_display', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'booking_id', 'doctor', 'doctor_detail', 'patient_name',
                  'patient_phone', 'patient_email', 'patient_age', 'patient_gender',
                  'gender_display', 'appointment_date', 'appointment_time',
                  'symptoms', 'notes', 'status', 'status_display', 'session_id',
                  'history', 'sms_notifications', 'created_at', 'updated_at']
        read_only_fields = ['id', 'booking_id', 'created_at', 'updated_at']


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating appointments"""

    class Meta:
        model = Appointment
        fields = ['doctor', 'patient_name', 'patient_phone', 'patient_email',
                  'patient_age', 'patient_gender', 'appointment_date',
                  'appointment_time', 'symptoms', 'notes', 'session_id']

    def validate_patient_phone(self, value):
        """Validate phone number format"""
        import re
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError(
                "Phone number must be entered in the format: '+999999999'. "
                "Up to 15 digits allowed."
            )
        return value

    def validate_patient_age(self, value):
        """Validate patient age"""
        if value is not None:
            if value < 0 or value > 150:
                raise serializers.ValidationError("Please enter a valid age")
        return value

    def validate(self, data):
        """Validate appointment slot availability"""
        from django.utils import timezone
        from datetime import datetime, timedelta

        # Check if appointment date is in the past
        if data['appointment_date'] < timezone.now().date():
            raise serializers.ValidationError({
                'appointment_date': 'Cannot book appointment in the past'
            })

        # Check if doctor is available on this date and time
        doctor = data['doctor']
        appointment_date = data['appointment_date']
        appointment_time = data['appointment_time']

        # Check doctor's schedule for the day
        day_of_week = appointment_date.weekday()
        schedules = doctor.schedules.filter(
            day_of_week=day_of_week,
            is_active=True
        )

        if not schedules.exists():
            raise serializers.ValidationError({
                'appointment_date': f'Doctor is not available on {appointment_date.strftime("%A")}'
            })

        # Check if time falls within any schedule
        time_valid = False
        for schedule in schedules:
            if schedule.start_time <= appointment_time <= schedule.end_time:
                time_valid = True
                break

        if not time_valid:
            raise serializers.ValidationError({
                'appointment_time': 'Selected time is outside doctor\'s schedule'
            })

        # Check if doctor is on leave
        leaves = doctor.leaves.filter(
            start_date__lte=appointment_date,
            end_date__gte=appointment_date
        )
        if leaves.exists():
            leave = leaves.first()
            raise serializers.ValidationError({
                'appointment_date': f'Doctor is on leave from {leave.start_date} to {leave.end_date}'
            })

        # Check for duplicate appointments at same slot
        existing = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status__in=['pending', 'confirmed']
        )

        if existing.exists():
            raise serializers.ValidationError({
                'appointment_time': 'This time slot is already booked'
            })

        return data

    def create(self, validated_data):
        """Create appointment and log history"""
        appointment = super().create(validated_data)

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=appointment,
            status=appointment.status,
            changed_by='patient',
            action='creation',
            notes='Appointment created'
        )

        return appointment


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating appointments"""

    class Meta:
        model = Appointment
        fields = ['patient_name', 'patient_phone', 'patient_email',
                  'patient_age', 'patient_gender', 'symptoms', 'notes']

    def update(self, instance, validated_data):
        """Update appointment and log history"""
        # Store old values
        old_values = {
            'patient_name': instance.patient_name,
            'patient_phone': instance.patient_phone,
        }

        # Update instance
        appointment = super().update(instance, validated_data)

        # Create history entry
        changes = []
        for field, old_value in old_values.items():
            new_value = getattr(appointment, field)
            if old_value != new_value:
                changes.append(f"{field}: {old_value} → {new_value}")

        if changes:
            AppointmentHistory.objects.create(
                appointment=appointment,
                status=appointment.status,
                changed_by='patient',
                action='update',
                notes='; '.join(changes)
            )

        return appointment


class AppointmentStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating appointment status"""
    status = serializers.ChoiceField(choices=Appointment.STATUS_CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True)
    changed_by = serializers.CharField(default='system')

    def validate_status(self, value):
        """Validate status transition"""
        instance = self.instance
        if instance:
            # Define valid transitions
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['completed', 'cancelled', 'no_show'],
                'cancelled': [],  # Cannot change from cancelled
                'completed': [],  # Cannot change from completed
                'no_show': [],  # Cannot change from no_show
            }

            current_status = instance.status
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"Cannot change status from '{current_status}' to '{value}'"
                )

        return value

    def update(self, instance, validated_data):
        """Update status and create history entry"""
        old_status = instance.status
        new_status = validated_data['status']
        reason = validated_data.get('reason', '')
        changed_by = validated_data.get('changed_by', 'system')

        instance.status = new_status
        instance.save()

        # Create history entry
        action = 'cancellation' if new_status == 'cancelled' else 'status_change'
        AppointmentHistory.objects.create(
            appointment=instance,
            status=new_status,
            changed_by=changed_by,
            action=action,
            notes=f'Status changed from {old_status} to {new_status}',
            reason=reason
        )

        return instance


class AppointmentRescheduleSerializer(serializers.Serializer):
    """Serializer for rescheduling appointments"""
    new_date = serializers.DateField()
    new_time = serializers.TimeField()
    reason = serializers.CharField(required=False, allow_blank=True)
    changed_by = serializers.CharField(default='patient')

    def validate(self, data):
        """Validate new appointment slot"""
        from django.utils import timezone

        instance = self.instance
        if not instance:
            raise serializers.ValidationError("No appointment instance provided")

        new_date = data['new_date']
        new_time = data['new_time']

        # Check if new date is in the past
        if new_date < timezone.now().date():
            raise serializers.ValidationError({
                'new_date': 'Cannot reschedule to a past date'
            })

        # Check if new slot is available
        doctor = instance.doctor
        existing = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=new_date,
            appointment_time=new_time,
            status__in=['pending', 'confirmed']
        ).exclude(id=instance.id)

        if existing.exists():
            raise serializers.ValidationError({
                'new_time': 'This time slot is already booked'
            })

        return data

    def update(self, instance, validated_data):
        """Reschedule appointment and create history entry"""
        old_date = instance.appointment_date
        old_time = instance.appointment_time
        new_date = validated_data['new_date']
        new_time = validated_data['new_time']
        reason = validated_data.get('reason', '')
        changed_by = validated_data.get('changed_by', 'patient')

        instance.appointment_date = new_date
        instance.appointment_time = new_time
        instance.save()

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=instance,
            status=instance.status,
            changed_by=changed_by,
            action='reschedule',
            old_date=old_date,
            old_time=old_time,
            new_date=new_date,
            new_time=new_time,
            reason=reason,
            notes=f'Rescheduled from {old_date} {old_time} to {new_date} {new_time}'
        )

        return instance


class PatientLookupSerializer(serializers.Serializer):
    """Serializer for patient lookup"""
    phone = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)

    def validate(self, data):
        """Validate that at least one field is provided"""
        if not data.get('phone') and not data.get('email'):
            raise serializers.ValidationError(
                "Either phone or email must be provided"
            )
        return data
