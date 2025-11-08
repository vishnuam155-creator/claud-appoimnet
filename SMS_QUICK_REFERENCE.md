# SMS & Twilio Integration - Quick Reference Guide

## SMS Sending Entry Points

### 1. Appointment Confirmation SMS (WORKING)
- **When:** New appointment is created after booking
- **File:** `chatbot/conversation_manager.py` (Line 1354)
- **Method:** `send_appointment_confirmation(appointment)`
- **Status:** ✓ IMPLEMENTED

### 2. Cancellation SMS (NOT WORKING)
- **When:** User cancels appointment via chatbot
- **File:** `chatbot/conversation_manager.py` (Line 241)
- **Expected Method:** `send_cancellation_notification(appointment)`
- **Status:** ✗ NOT CALLED (Method exists but never invoked)
- **Fix Required:** Add call after line 242 (after `appointment.save()`)

### 3. Reschedule SMS (NOT WORKING)
- **When:** User reschedules appointment via chatbot
- **File:** `chatbot/conversation_manager.py` (Line 569)
- **Expected Method:** `send_reschedule_notification(appointment, old_date, old_time)`
- **Status:** ✗ NOT CALLED (Method exists but never invoked)
- **Fix Required:** Add call after line 584 (after history is created)

### 4. Admin Status Updates (NOT IMPLEMENTED)
- **When:** Admin changes appointment status in admin panel
- **File:** `admin_panel/views.py` (Line 110)
- **Status:** ✗ NOT IMPLEMENTED (No SMS logic)
- **Fix Required:** Add SMS trigger based on status change

---

## Environment Configuration

### Required Environment Variables
```bash
TWILIO_ACCOUNT_SID=AC1234567890abcdef1234567890abcdef
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+15551234567
```

### Configuration File
- Location: `config/settings.py` (Lines 138-141)
- If not configured: SMS service gracefully disables (no error thrown)

---

## Key Code Locations

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Twilio Service Class | `twilio_service.py` | 34-291 | ✓ |
| SMS Confirmation | `conversation_manager.py` | 1352-1362 | ✓ |
| SMS Cancellation (missing) | `conversation_manager.py` | 220-273 | ✗ |
| SMS Reschedule (missing) | `conversation_manager.py` | 554-599 | ✗ |
| Phone Normalization | `twilio_service.py` | 170-199 | ✓ |
| SMS Logging | `twilio_service.py` | 13-31 | ✓ |
| SMS Model | `appointments/models.py` | 118-170 | ✓ |
| Admin View | `appointments/admin.py` | 81-100 | ✓ |

---

## Message Templates

### Confirmation Message
```
🏥 Appointment Confirmed!

Hello {patient_name},

Your appointment has been confirmed:

👨‍⚕️ Doctor: Dr. {doctor_name}
📅 Date: {date}
🕒 Time: {time}
🏥 Department: {specialization}

Booking ID: {booking_id}

Please arrive 10 minutes early. For any changes, contact the clinic.

Thank you!
```

### Cancellation Message (Configured but not used)
```
🏥 Appointment Cancelled

Hello {patient_name},

Your appointment has been cancelled:

Booking ID: {booking_id}
Date: {date}
Time: {time}

To reschedule, please contact the clinic or book online.

Thank you!
```

### Reschedule Message (Configured but not used)
```
🏥 Appointment Rescheduled

Hello {patient_name},

Your appointment has been rescheduled:

Previous:
📅 {old_date} at {old_time}

New:
📅 {new_date} at {new_time}

Booking ID: {booking_id}
Doctor: Dr. {doctor_name}

Thank you!
```

---

## Phone Number Normalization

### Supported Input Formats
- `9876543210` → `+919876543210`
- `919876543210` → `+919876543210`
- `+919876543210` → `+919876543210`
- `+1234567890` → `+1234567890` (other countries)

### Location
- File: `twilio_service.py` (Lines 170-199)
- Method: `_normalize_phone_number(phone)`

---

## Error Handling

### Service Disabled Check
- If credentials missing: Service initializes with `enabled=False`
- Result: All SMS calls return `{'success': False, 'error': 'Twilio service is not configured'}`
- No exception thrown (graceful degradation)

### Exception Handling Levels
1. **Service not configured** → Warning log, return failed result
2. **Twilio API error** → Error log, return failed result
3. **Unexpected error** → Error log, return failed result

### SMS Failure Impact
- **Confirmation SMS:** Appointment still created (SMS failure doesn't block booking)
- **Cancellation SMS:** Appointment cancelled regardless of SMS (if feature was working)
- **Reschedule SMS:** Appointment rescheduled regardless of SMS (if feature was working)

---

## Database Logging

### SMSNotification Model
- Location: `appointments/models.py` (Lines 118-170)
- Fields Tracked:
  - `notification_type`: 'confirmation', 'cancellation', 'reschedule', 'reminder'
  - `phone_number`: Recipient phone number
  - `message_body`: Full SMS text
  - `message_sid`: Twilio message ID
  - `status`: 'sent', 'delivered', 'failed', 'undelivered'
  - `error_message`: Error details if failed
  - `sent_at`: Timestamp

### Admin View
- Navigate to: Django Admin → Appointments → SMS Notifications
- Filter by: notification type, status, date
- Search by: booking ID, phone number, Twilio SID
- View inline with appointment details

---

## Testing Checklist

### Setup Testing
- [ ] Create Twilio account
- [ ] Get Account SID, Auth Token, and Twilio Phone Number
- [ ] Set environment variables
- [ ] Restart Django server
- [ ] Check logs for "SMS service configured" message

### Functional Testing
- [ ] Create new appointment → Confirm SMS received
- [ ] Check database for SMSNotification record
- [ ] Verify message_sid is populated
- [ ] Test with trial account (limited to verified numbers)
- [ ] Add test phone numbers to Twilio Verified Caller IDs

### Error Testing
- [ ] Remove TWILIO_PHONE_NUMBER env var → SMS gracefully disabled
- [ ] Use invalid phone number → Check error handling
- [ ] Check Django logs for warnings/errors

---

## Common Issues & Solutions

### Issue: "Twilio SMS service is not configured"
- Check all 3 environment variables are set
- Restart Django after changing .env file
- Verify no trailing/leading spaces in credentials

### Issue: "Invalid phone number"
- Ensure patient phone is in E.164 format
- Verify country code is correct for patient's country
- Check phone normalization logic for your country

### Issue: SMS not received by trial account
- Verify phone number is added to Twilio Verified Caller IDs
- Trial accounts can only send to verified numbers
- All trial SMS include trial notice

### Issue: SMS logged but not actually sent
- Check Twilio account has available credits
- Verify phone number is active and SMS-enabled
- Check authentication credentials are correct

---

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| New Appointment SMS | ✓ | Working, tested |
| Cancellation SMS | ✗ | Method exists, not called |
| Reschedule SMS | ✗ | Method exists, not called |
| Admin Status SMS | ✗ | Not implemented |
| Reminder SMS | ✗ | No scheduler/task |
| Phone Normalization | ✓ | India (+91) optimized |
| Error Handling | ✓ | Graceful degradation |
| Database Logging | ✓ | All SMS logged |
| Admin Interface | ✓ | View in Django admin |

---

## Next Steps (Recommended)

1. **Test Current SMS:** Verify appointment confirmation SMS works
2. **Add Cancellation SMS:** Uncomment send_cancellation_notification() call
3. **Add Reschedule SMS:** Uncomment send_reschedule_notification() call
4. **Add Admin SMS:** Implement SMS in admin status update view
5. **Add Reminders:** Implement scheduled reminder SMS (Celery/APScheduler)
6. **Monitor:** Check SMS logs regularly for errors

