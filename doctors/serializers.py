"""
Serializers for Doctor models
"""
from rest_framework import serializers
from .models import Doctor, Specialization, DoctorSchedule, DoctorLeave


class SpecializationSerializer(serializers.ModelSerializer):
    """Serializer for Specialization model"""
    keywords_list = serializers.ListField(
        source='get_keywords_list',
        read_only=True
    )

    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'keywords', 'keywords_list', 'created_at']
        read_only_fields = ['id', 'created_at']


class DoctorScheduleSerializer(serializers.ModelSerializer):
    """Serializer for DoctorSchedule model"""
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = DoctorSchedule
        fields = [
            'id', 'doctor', 'day_of_week', 'day_name',
            'start_time', 'end_time', 'slot_duration', 'is_active'
        ]
        read_only_fields = ['id']


class DoctorLeaveSerializer(serializers.ModelSerializer):
    """Serializer for DoctorLeave model"""
    class Meta:
        model = DoctorLeave
        fields = ['id', 'doctor', 'start_date', 'end_date', 'reason', 'created_at']
        read_only_fields = ['id', 'created_at']


class DoctorSerializer(serializers.ModelSerializer):
    """Serializer for Doctor model"""
    specialization = SpecializationSerializer(read_only=True)
    specialization_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Doctor
        fields = [
            'id', 'name', 'specialization', 'specialization_id',
            'phone', 'email', 'qualification', 'experience_years',
            'consultation_fee', 'is_active', 'photo', 'bio',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DoctorDetailSerializer(DoctorSerializer):
    """Detailed serializer for Doctor with schedules and leaves"""
    schedules = DoctorScheduleSerializer(many=True, read_only=True)
    leaves = DoctorLeaveSerializer(many=True, read_only=True)

    class Meta(DoctorSerializer.Meta):
        fields = DoctorSerializer.Meta.fields + ['schedules', 'leaves']
