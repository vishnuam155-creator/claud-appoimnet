from rest_framework import serializers
from .models import Specialization, Doctor, DoctorSchedule, DoctorLeave


class SpecializationSerializer(serializers.ModelSerializer):
    """Serializer for Specialization model"""
    doctors_count = serializers.SerializerMethodField()
    keywords_list = serializers.SerializerMethodField()

    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'keywords', 'keywords_list',
                  'doctors_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_doctors_count(self, obj):
        """Get count of active doctors in this specialization"""
        return obj.doctors.filter(is_active=True).count()

    def get_keywords_list(self, obj):
        """Return keywords as a list"""
        return obj.get_keywords_list()


class DoctorScheduleSerializer(serializers.ModelSerializer):
    """Serializer for DoctorSchedule model"""
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = DoctorSchedule
        fields = ['id', 'doctor', 'day_of_week', 'day_name', 'start_time',
                  'end_time', 'slot_duration', 'is_active']
        read_only_fields = ['id']

    def validate(self, data):
        """Validate that end_time is after start_time"""
        if data.get('start_time') and data.get('end_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError(
                    "End time must be after start time"
                )
        return data


class DoctorLeaveSerializer(serializers.ModelSerializer):
    """Serializer for DoctorLeave model"""
    doctor_name = serializers.CharField(source='doctor.name', read_only=True)
    duration_days = serializers.SerializerMethodField()

    class Meta:
        model = DoctorLeave
        fields = ['id', 'doctor', 'doctor_name', 'start_date', 'end_date',
                  'reason', 'duration_days', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_duration_days(self, obj):
        """Calculate leave duration in days"""
        return (obj.end_date - obj.start_date).days + 1

    def validate(self, data):
        """Validate that end_date is after start_date"""
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError(
                    "End date must be after or equal to start date"
                )
        return data


class DoctorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for doctor list view"""
    specialization_name = serializers.CharField(source='specialization.name', read_only=True)
    appointments_count = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialization', 'specialization_name',
                  'phone', 'email', 'qualification', 'experience_years',
                  'consultation_fee', 'is_active', 'photo_url', 'appointments_count']
        read_only_fields = ['id']

    def get_appointments_count(self, obj):
        """Get count of upcoming appointments"""
        from django.utils import timezone
        return obj.appointments.filter(
            appointment_date__gte=timezone.now().date(),
            status__in=['pending', 'confirmed']
        ).count()

    def get_photo_url(self, obj):
        """Get photo URL if exists"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class DoctorDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for doctor detail view with nested data"""
    specialization_name = serializers.CharField(source='specialization.name', read_only=True)
    specialization_detail = SpecializationSerializer(source='specialization', read_only=True)
    schedules = DoctorScheduleSerializer(many=True, read_only=True)
    leaves = DoctorLeaveSerializer(many=True, read_only=True)
    upcoming_leaves = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialization', 'specialization_name',
                  'specialization_detail', 'phone', 'email', 'qualification',
                  'experience_years', 'consultation_fee', 'is_active', 'photo',
                  'photo_url', 'bio', 'schedules', 'leaves', 'upcoming_leaves',
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_upcoming_leaves(self, obj):
        """Get only upcoming/current leaves"""
        from django.utils import timezone
        upcoming = obj.leaves.filter(end_date__gte=timezone.now().date())
        return DoctorLeaveSerializer(upcoming, many=True).data

    def get_photo_url(self, obj):
        """Get photo URL if exists"""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class DoctorCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating doctors"""

    class Meta:
        model = Doctor
        fields = ['id', 'name', 'specialization', 'phone', 'email',
                  'qualification', 'experience_years', 'consultation_fee',
                  'is_active', 'photo', 'bio']
        read_only_fields = ['id']

    def validate_phone(self, value):
        """Validate phone number format"""
        import re
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError(
                "Phone number must be entered in the format: '+999999999'. "
                "Up to 15 digits allowed."
            )
        return value

    def validate_experience_years(self, value):
        """Validate experience years"""
        if value < 0:
            raise serializers.ValidationError("Experience years cannot be negative")
        if value > 70:
            raise serializers.ValidationError("Experience years seems too high")
        return value


class AvailabilitySlotSerializer(serializers.Serializer):
    """Serializer for available time slots"""
    date = serializers.DateField()
    time = serializers.TimeField()
    doctor = serializers.IntegerField()
    doctor_name = serializers.CharField()
    is_available = serializers.BooleanField()
    reason = serializers.CharField(required=False, allow_blank=True)
