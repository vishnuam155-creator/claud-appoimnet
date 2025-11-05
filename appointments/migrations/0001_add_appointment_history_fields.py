# Generated migration for AppointmentHistory enhancements

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('doctors', '__first__'),  # Depends on doctors app
    ]

    operations = [
        migrations.CreateModel(
            name='Appointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_name', models.CharField(max_length=200)),
                ('patient_phone', models.CharField(max_length=15)),
                ('patient_email', models.EmailField(blank=True, max_length=254)),
                ('patient_age', models.IntegerField(blank=True, null=True)),
                ('patient_gender', models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], max_length=10)),
                ('appointment_date', models.DateField()),
                ('appointment_time', models.TimeField()),
                ('symptoms', models.TextField(help_text="Patient's symptoms or reason for visit")),
                ('notes', models.TextField(blank=True, help_text='Additional notes from patient')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled'), ('completed', 'Completed'), ('no_show', 'No Show')], default='pending', max_length=20)),
                ('booking_id', models.CharField(editable=False, max_length=20, unique=True)),
                ('session_id', models.CharField(blank=True, max_length=100)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('doctor', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='appointments', to='doctors.doctor')),
            ],
            options={
                'ordering': ['-appointment_date', '-appointment_time'],
            },
        ),
        migrations.CreateModel(
            name='AppointmentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=20)),
                ('notes', models.TextField(blank=True)),
                ('changed_by', models.CharField(max_length=100)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('action', models.CharField(choices=[('status_change', 'Status Change'), ('reschedule', 'Reschedule'), ('cancellation', 'Cancellation'), ('creation', 'Creation'), ('update', 'Update')], default='status_change', help_text='Type of change made to the appointment', max_length=20)),
                ('old_date', models.DateField(blank=True, help_text='Previous appointment date', null=True)),
                ('old_time', models.TimeField(blank=True, help_text='Previous appointment time', null=True)),
                ('new_date', models.DateField(blank=True, help_text='New appointment date', null=True)),
                ('new_time', models.TimeField(blank=True, help_text='New appointment time', null=True)),
                ('reason', models.TextField(blank=True, help_text='Reason for cancellation or reschedule')),
                ('appointment', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='history', to='appointments.appointment')),
            ],
            options={
                'verbose_name_plural': 'Appointment Histories',
                'ordering': ['-changed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['doctor', 'appointment_date', 'appointment_time'], name='appointment_doctor__idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['status'], name='appointment_status_idx'),
        ),
        migrations.AddIndex(
            model_name='appointment',
            index=models.Index(fields=['patient_phone'], name='appointment_patient_idx'),
        ),
    ]
