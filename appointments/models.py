from django.db import models
from doctors.models import Doctor


class Appointment(models.Model):
    """
    Patient appointment bookings
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
        ('no_show', 'No Show'),
    ]
    
    # Doctor details
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointments'
    )
    
    # Patient details
    patient_name = models.CharField(max_length=200)
    patient_phone = models.CharField(max_length=15)
    patient_email = models.EmailField(blank=True)
    patient_age = models.IntegerField(null=True, blank=True)
    patient_gender = models.CharField(
        max_length=10,
        choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],
        blank=True
    )
    
    # Appointment details
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    symptoms = models.TextField(help_text="Patient's symptoms or reason for visit")
    notes = models.TextField(blank=True, help_text="Additional notes from patient")
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_id = models.CharField(max_length=20, unique=True, editable=False)
    
    # Chatbot conversation reference
    session_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
        indexes = [
            models.Index(fields=['doctor', 'appointment_date', 'appointment_time']),
            models.Index(fields=['status']),
            models.Index(fields=['patient_phone']),
        ]
    
    def __str__(self):
        return f"{self.patient_name} - {self.doctor.name} on {self.appointment_date} at {self.appointment_time}"
    
    def save(self, *args, **kwargs):
        if not self.booking_id:
            # Generate unique booking ID
            import uuid
            self.booking_id = f"APT{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class AppointmentHistory(models.Model):
    """
    Track changes to appointments including cancellations and reschedules
    """
    ACTION_CHOICES = [
        ('status_change', 'Status Change'),
        ('reschedule', 'Reschedule'),
        ('cancellation', 'Cancellation'),
        ('creation', 'Creation'),
        ('update', 'Update'),
    ]

    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.CASCADE,
        related_name='history'
    )
    status = models.CharField(max_length=20)
    notes = models.TextField(blank=True)
    changed_by = models.CharField(max_length=100)  # 'patient', 'doctor', 'admin', 'system'
    changed_at = models.DateTimeField(auto_now_add=True)

    # Action type
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        default='status_change',
        help_text="Type of change made to the appointment"
    )

    # For reschedule tracking
    old_date = models.DateField(null=True, blank=True, help_text="Previous appointment date")
    old_time = models.TimeField(null=True, blank=True, help_text="Previous appointment time")
    new_date = models.DateField(null=True, blank=True, help_text="New appointment date")
    new_time = models.TimeField(null=True, blank=True, help_text="New appointment time")

    # Reason for change
    reason = models.TextField(blank=True, help_text="Reason for cancellation or reschedule")

    class Meta:
        ordering = ['-changed_at']
        verbose_name_plural = "Appointment Histories"

    def __str__(self):
        return f"{self.appointment.booking_id} - {self.action} at {self.changed_at}"
