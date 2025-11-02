from django.db import models
import uuid


class PatientRecord(models.Model):
    """
    Patient booking records with all appointment details
    """
    # Booking identification
    booking_id = models.CharField(max_length=20, unique=True, editable=False)

    # Patient details
    name = models.CharField(max_length=200, help_text="Patient's full name")
    phone_number = models.CharField(max_length=15, help_text="Patient's contact number")
    mail_id = models.EmailField(help_text="Patient's email address")

    # Appointment details
    doctor_name = models.CharField(max_length=200, help_text="Doctor's name")
    department = models.CharField(max_length=100, help_text="Medical department/specialization")
    appointment_date = models.DateField(help_text="Date of appointment")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patient_record'
        ordering = ['-appointment_date', '-created_at']
        indexes = [
            models.Index(fields=['booking_id']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['appointment_date']),
        ]
        verbose_name = 'Patient Record'
        verbose_name_plural = 'Patient Records'

    def __str__(self):
        return f"{self.booking_id} - {self.name} ({self.appointment_date})"

    def save(self, *args, **kwargs):
        if not self.booking_id:
            # Generate unique booking ID
            self.booking_id = f"BK{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)
