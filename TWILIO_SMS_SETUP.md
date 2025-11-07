# Twilio SMS Confirmation Setup

This document explains how to set up and use the Twilio SMS notification feature for appointment confirmations.

## Overview

The appointment booking system now sends SMS confirmations to patients via Twilio when:
- A new appointment is booked
- An appointment is cancelled
- An appointment is rescheduled

## Features

- **Automatic SMS Notifications**: Sends SMS confirmations automatically when appointments are created
- **SMS Logging**: All SMS notifications are logged in the database for tracking and debugging
- **Error Handling**: Graceful error handling - appointment booking won't fail if SMS fails
- **Phone Number Normalization**: Automatically handles Indian phone numbers (+91 country code)
- **Admin Panel Integration**: View SMS logs directly in the Django admin panel

## Setup Instructions

### 1. Create a Twilio Account

1. Go to [Twilio](https://www.twilio.com/) and sign up for an account
2. For testing, you can use a free trial account
3. Once logged in, navigate to the Twilio Console

### 2. Get Your Twilio Credentials

You need three pieces of information from your Twilio account:

1. **Account SID**: Found on your Twilio Console Dashboard
2. **Auth Token**: Found on your Twilio Console Dashboard (click to reveal)
3. **Twilio Phone Number**:
   - Go to Phone Numbers → Manage → Active numbers
   - Or buy a new number if you don't have one
   - Format: `+1234567890` (E.164 format)

### 3. Configure Environment Variables

Add the following to your `.env` file:

```bash
# Twilio SMS Configuration
TWILIO_ACCOUNT_SID=your-account-sid-here
TWILIO_AUTH_TOKEN=your-auth-token-here
TWILIO_PHONE_NUMBER=+1234567890
```

**Example:**
```bash
TWILIO_ACCOUNT_SID=AC1234567890abcdef1234567890abcdef
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
```

### 4. Verify Setup

The SMS service will automatically initialize when Django starts. Check the logs for:

```
SMS confirmation sent successfully. SID: SM...
```

If Twilio is not configured, you'll see:
```
Twilio SMS service is not configured. SMS notifications will be disabled.
```

## Usage

### Automatic SMS on Booking

When a patient completes a booking through the chatbot, an SMS is automatically sent with:

```
🏥 Appointment Confirmed!

Hello [Patient Name],

Your appointment has been confirmed:

👨‍⚕️ Doctor: Dr. [Doctor Name]
📅 Date: [Date]
🕒 Time: [Time]
🏥 Department: [Specialization]

Booking ID: [Booking ID]

Please arrive 10 minutes early. For any changes, contact the clinic.

Thank you!
```

### Cancellation SMS

To send a cancellation SMS programmatically:

```python
from twilio_service import get_twilio_service

twilio_service = get_twilio_service()
result = twilio_service.send_cancellation_notification(appointment)
```

### Reschedule SMS

To send a reschedule SMS:

```python
from twilio_service import get_twilio_service

old_date = appointment.appointment_date
old_time = appointment.appointment_time

# Update appointment date/time
appointment.appointment_date = new_date
appointment.appointment_time = new_time
appointment.save()

# Send notification
twilio_service = get_twilio_service()
result = twilio_service.send_reschedule_notification(appointment, old_date, old_time)
```

## Phone Number Format

The service automatically handles phone number formatting:

- **10-digit Indian numbers**: `9876543210` → `+919876543210`
- **Already formatted**: `+919876543210` → `+919876543210`
- **With country code**: `919876543210` → `+919876543210`

For other countries, update the `_normalize_phone_number()` method in `twilio_service.py`.

## Database Logging

All SMS notifications are logged in the `SMSNotification` model with:

- Appointment reference
- Notification type (confirmation, cancellation, reschedule, reminder)
- Phone number
- Message body
- Twilio message SID
- Status (sent, delivered, failed, undelivered)
- Error message (if failed)
- Timestamps

### View SMS Logs in Admin

1. Log in to Django Admin: `http://localhost:8000/admin/`
2. Navigate to **Appointments** → **SMS Notifications**
3. Filter by notification type, status, or date
4. Click on an appointment to see all related SMS notifications

## Testing

### Test with Twilio Trial Account

With a Twilio trial account:

1. You can only send SMS to verified phone numbers
2. Add phone numbers to verify: Twilio Console → Phone Numbers → Verified Caller IDs
3. All SMS will include a trial account notice

### Test SMS Sending

Create a test script:

```python
from appointments.models import Appointment
from twilio_service import get_twilio_service

# Get an appointment
appointment = Appointment.objects.first()

# Send test SMS
twilio_service = get_twilio_service()
result = twilio_service.send_appointment_confirmation(appointment)

print(f"Success: {result['success']}")
print(f"Message SID: {result['message_sid']}")
print(f"Error: {result['error']}")
```

## Troubleshooting

### SMS Not Sending

**Issue**: `Twilio SMS service is not configured`

**Solution**: Verify that all three environment variables are set in `.env`:
```bash
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=...
```

### Invalid Phone Number Error

**Issue**: `The 'To' number +XX... is not a valid phone number`

**Solution**:
- Ensure phone numbers are in E.164 format: `+[country code][number]`
- For India: `+919876543210`
- Update `_normalize_phone_number()` for your country

### Permission Denied Error

**Issue**: `Unable to create record: Permission to send an SMS has not been enabled`

**Solution**: Check Twilio account status and ensure:
- Phone number is active and SMS-enabled
- Account has sufficient credits
- Phone number is verified (for trial accounts)

### Authentication Error

**Issue**: `Authenticate`

**Solution**: Verify your Account SID and Auth Token are correct

## Cost Considerations

- **SMS Costs**: Twilio charges per SMS sent (~$0.0075 per SMS in the US)
- **Trial Account**: Free credits available (usually ~$15)
- **Estimate**: For 100 appointments/day = ~$0.75/day

Check [Twilio Pricing](https://www.twilio.com/sms/pricing) for your country.

## Advanced Configuration

### Custom SMS Templates

Edit SMS templates in `twilio_service.py`:

```python
def _format_confirmation_message(self, appointment):
    # Customize your SMS template here
    message = f"""Your custom message here..."""
    return message
```

### Add SMS Reminders

To send reminders before appointments, create a scheduled task using:

- Django Celery Beat (recommended)
- Cron jobs
- Django-cron

Example:
```python
from datetime import datetime, timedelta
from appointments.models import Appointment
from twilio_service import get_twilio_service

# Get appointments for tomorrow
tomorrow = datetime.now().date() + timedelta(days=1)
appointments = Appointment.objects.filter(
    appointment_date=tomorrow,
    status='confirmed'
)

# Send reminders
twilio_service = get_twilio_service()
for appointment in appointments:
    message = f"Reminder: Your appointment with Dr. {appointment.doctor.name} is tomorrow at {appointment.appointment_time}"
    twilio_service.send_sms(appointment.patient_phone, message)
```

## Integration with External Project

As mentioned, this SMS feature can connect to another project/application. To integrate:

### Option 1: API Endpoint

Create an API endpoint to trigger SMS:

```python
# appointments/api_views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Appointment
from twilio_service import get_twilio_service

@api_view(['POST'])
def send_appointment_sms(request):
    booking_id = request.data.get('booking_id')
    appointment = Appointment.objects.get(booking_id=booking_id)

    twilio_service = get_twilio_service()
    result = twilio_service.send_appointment_confirmation(appointment)

    return Response(result)
```

### Option 2: Webhook

Set up a webhook endpoint that other applications can call:

```python
# appointments/webhooks.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def sms_webhook(request):
    data = json.loads(request.body)

    # Process webhook data
    # Send SMS

    return JsonResponse({'status': 'success'})
```

### Option 3: Shared Database

If both projects share the same database, create appointments from the other project and SMS will be sent automatically.

## Security Best Practices

1. **Never commit `.env` file** - Keep credentials secret
2. **Use environment variables** - Don't hardcode credentials
3. **Rotate Auth Tokens** - Periodically change Twilio auth tokens
4. **Rate Limiting** - Implement rate limiting to prevent SMS spam
5. **Validate Phone Numbers** - Validate phone numbers before sending
6. **Monitor Logs** - Regularly check SMS logs for suspicious activity

## Support

For issues or questions:

- **Twilio Documentation**: https://www.twilio.com/docs/sms
- **Twilio Support**: https://support.twilio.com/
- **Django Documentation**: https://docs.djangoproject.com/

## License

This feature is part of the main appointment booking system.
