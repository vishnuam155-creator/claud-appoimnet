# Generated migration for enhanced patient information collection
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0002_smsnotification_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='medical_history',
            field=models.TextField(blank=True, help_text="Patient's relevant medical history, chronic conditions, previous surgeries, etc."),
        ),
        migrations.AddField(
            model_name='appointment',
            name='allergies',
            field=models.TextField(blank=True, help_text='Known allergies (medications, food, environmental, etc.)'),
        ),
        migrations.AddField(
            model_name='appointment',
            name='current_medications',
            field=models.TextField(blank=True, help_text='Current medications the patient is taking'),
        ),
    ]
