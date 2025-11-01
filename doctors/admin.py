from django.contrib import admin
from .models import Specialization, Doctor, DoctorSchedule, DoctorLeave


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name', 'keywords']
    list_filter = ['created_at']


class DoctorScheduleInline(admin.TabularInline):
    model = DoctorSchedule
    extra = 1


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['name', 'specialization', 'phone', 'email', 'is_active', 'experience_years']
    list_filter = ['specialization', 'is_active', 'created_at']
    search_fields = ['name', 'email', 'phone']
    inlines = [DoctorScheduleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'specialization', 'phone', 'email', 'photo')
        }),
        ('Professional Details', {
            'fields': ('qualification', 'experience_years', 'consultation_fee', 'bio')
        }),
        ('Status', {
            'fields': ('is_active', 'user')
        }),
    )


@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'day_of_week', 'start_time', 'end_time', 'slot_duration', 'is_active']
    list_filter = ['day_of_week', 'is_active', 'doctor']
    search_fields = ['doctor__name']


@admin.register(DoctorLeave)
class DoctorLeaveAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'start_date', 'end_date', 'reason']
    list_filter = ['start_date', 'doctor']
    search_fields = ['doctor__name', 'reason']
    date_hierarchy = 'start_date'
