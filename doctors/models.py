from django.db import models
from django.contrib.auth.models import User


class Specialization(models.Model):
    """
    Medical specializations for doctors
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    keywords = models.TextField(
        help_text="Comma-separated keywords for AI matching (e.g., 'leg pain, bone, fracture, joint')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Specializations"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_keywords_list(self):
        """Return keywords as a list"""
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]


class Doctor(models.Model):
    """
    Doctor profile with specialization and schedule
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    specialization = models.ForeignKey(
        Specialization, 
        on_delete=models.CASCADE,
        related_name='doctors'
    )
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    qualification = models.CharField(max_length=200, blank=True)
    experience_years = models.IntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"Dr. {self.name} - {self.specialization.name}"


class DoctorSchedule(models.Model):
    """
    Weekly schedule for doctors
    """
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    doctor = models.ForeignKey(
        Doctor, 
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    day_of_week = models.IntegerField(choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration = models.IntegerField(
        default=30,
        help_text="Duration of each appointment slot in minutes"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['doctor', 'day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.doctor.name} - {self.get_day_of_week_display()} ({self.start_time} - {self.end_time})"


class DoctorLeave(models.Model):
    """
    Track doctor's leave/unavailability
    """
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='leaves'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.doctor.name} - Leave from {self.start_date} to {self.end_date}"
