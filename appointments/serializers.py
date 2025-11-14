"""
Serializers for Appointment models
"""
from rest_framework import serializers
from .models import Appointment, AppointmentHistory, SMSNotification
from doctors.models import Doctor, Specialization


class SpecializationSerializer(serializers.ModelSerializer):
    """Serializer for Specialization model"""
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description']


class DoctorSerializer(serializers.ModelSerializer):
    """Serializer for Doctor model"""
    specialization = SpecializationSerializer(read_only=True)
    specialization_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Doctor
        fields = [
            'id', 'name', 'specialization', 'specialization_id',
            'phone', 'email', 'qualification', 'experience_years',
            'consultation_fee', 'is_active', 'photo', 'bio'
        ]
        read_only_fields = ['id']


class AppointmentHistorySerializer(serializers.ModelSerializer):
    """Serializer for AppointmentHistory model"""
    class Meta:
        model = AppointmentHistory
        fields = [
            'id', 'appointment', 'status', 'notes', 'changed_by',
            'changed_at', 'action', 'old_date', 'old_time',
            'new_date', 'new_time', 'reason'
        ]
        read_only_fields = ['id', 'changed_at']


class SMSNotificationSerializer(serializers.ModelSerializer):
    """Serializer for SMSNotification model"""
    class Meta:
        model = SMSNotification
        fields = [
            'id', 'appointment', 'notification_type', 'phone_number',
            'message_body', 'message_sid', 'status', 'error_message',
            'sent_at', 'updated_at'
        ]
        read_only_fields = ['id', 'sent_at', 'updated_at']


class AppointmentSerializer(serializers.ModelSerializer):
    """Serializer for Appointment model"""
    doctor = DoctorSerializer(read_only=True)
    doctor_id = serializers.IntegerField(write_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = [
            'id', 'doctor', 'doctor_id', 'patient_name', 'patient_phone',
            'patient_email', 'patient_age', 'patient_gender',
            'appointment_date', 'appointment_time', 'symptoms', 'notes',
            'status', 'status_display', 'booking_id', 'session_id',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'booking_id', 'created_at', 'updated_at']


class AppointmentDetailSerializer(AppointmentSerializer):
    """Detailed serializer for Appointment with related data"""
    history = AppointmentHistorySerializer(many=True, read_only=True)
    sms_notifications = SMSNotificationSerializer(many=True, read_only=True)

    class Meta(AppointmentSerializer.Meta):
        fields = AppointmentSerializer.Meta.fields + ['history', 'sms_notifications']


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating appointment status"""
    notes = serializers.CharField(required=False, allow_blank=True)
    changed_by = serializers.CharField(required=False, default='api')

    class Meta:
        model = Appointment
        fields = ['status', 'notes', 'changed_by']

    def update(self, instance, validated_data):
        notes = validated_data.pop('notes', '')
        changed_by = validated_data.pop('changed_by', 'api')

        # Update appointment status
        instance.status = validated_data.get('status', instance.status)
        instance.save()

        # Create history entry
        AppointmentHistory.objects.create(
            appointment=instance,
            status=instance.status,
            notes=notes,
            changed_by=changed_by,
            action='status_change'
        )

        return instance
