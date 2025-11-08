# SMS Integration - Flow Diagrams & Architecture

## 1. Complete Appointment Booking & SMS Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER SENDS MESSAGE                              │
│                    (WhatsApp or Web Chat)                            │
└────────────────────┬────────────────────────────────────────────────┘
                     │
                     ▼
         ┌──────────────────────────────┐
         │  WhatsApp Webhook Handler    │
         │  whatsapp_integration/       │
         │  views.py:19-211             │
         │                              │
         │ - Parse incoming message     │
         │ - Create/update session      │
         │ - Log incoming message       │
         └────────┬─────────────────────┘
                  │
                  ▼
         ┌──────────────────────────────┐
         │  ConversationManager         │
         │  chatbot/conversation_       │
         │  manager.py                  │
         │                              │
         │ Stages:                      │
         │ 1. greeting                  │
         │ 2. symptoms                  │
         │ 3. doctor_selection          │
         │ 4. date_selection            │
         │ 5. time_selection            │
         │ 6. patient_details           │
         │ 7. confirmation              │
         └────────┬─────────────────────┘
                  │
                  ▼
         ┌──────────────────────────────┐
         │  Is Rescheduling?            │
         └──┬──────────────────────┬────┘
            │ YES                  │ NO
            │                      │
            ▼                      ▼
    ┌────────────────────┐  ┌──────────────────┐
    │ Update existing    │  │ Create new       │
    │ appointment with   │  │ appointment      │
    │ new date/time      │  │                  │
    │                    │  │                  │
    │ (Lines 556-569)    │  │ (Lines 1338-1348)│
    └────────┬───────────┘  └────────┬─────────┘
             │                       │
             ▼                       ▼
    ┌────────────────────────────────────────┐
    │  Send SMS Confirmation                 │
    │                                        │
    │  twilio_service.py:1354                │
    │  send_appointment_confirmation()       │
    │                                        │
    │  Status: ✓ WORKING                    │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────────┐
    │  Log SMS to Database                   │
    │                                        │
    │  SMSNotification model                 │
    │  - notification_type: 'confirmation'   │
    │  - message_sid (Twilio ID)             │
    │  - status: 'sent' or 'failed'          │
    │  - error_message (if failed)           │
    │                                        │
    │  Status: ✓ ALWAYS LOGGED              │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌────────────────────────────────────────┐
    │  Return Confirmation to User           │
    │                                        │
    │  "✅ Appointment Confirmed!"           │
    │  Booking ID, doctor, date, time        │
    │  "You'll receive a confirmation SMS"   │
    └────────────────────────────────────────┘
```

---

## 2. Cancellation Flow (BROKEN - SMS NOT SENT)

```
┌────────────────────────────────────┐
│  USER CANCELS APPOINTMENT          │
│  Via WhatsApp Chatbot              │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  ConversationManager               │
│  _handle_appointment_action()      │
│  (Lines 220-273)                   │
│                                    │
│  if action == 'cancel_appointment' │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Validate Cancellation Timing      │
│  Minimum 2 hours notice required   │
│  (Lines 225-235)                   │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Update Appointment Status         │
│  appointment.status = 'cancelled'  │
│  appointment.save()                │
│  (Line 241)                        │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Create AppointmentHistory Record  │
│  Track cancellation event          │
│  (Lines 245-254)                   │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  SHOULD: Send Cancellation SMS     │
│  send_cancellation_notification()  │
│                                    │
│  Status: ✗ NOT CALLED              │
│  Method exists but never invoked   │
│  (Missing implementation)          │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Return Response to User           │
│  "✅ Appointment Cancelled"        │
│  (User never receives SMS)         │
└────────────────────────────────────┘
```

---

## 3. Reschedule Flow (PARTIALLY BROKEN - SMS NOT SENT)

```
┌────────────────────────────────────┐
│  USER RESCHEDULES APPOINTMENT      │
│  Via WhatsApp Chatbot              │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Select New Date & Time            │
│  (Lines 438-632)                   │
│                                    │
│  ConversationManager handles       │
│  date_selection & time_selection   │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Update Appointment Record         │
│  appointment.appointment_date=new  │
│  appointment.appointment_time=new  │
│  appointment.save()                │
│  (Lines 567-569)                   │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Create AppointmentHistory Record  │
│  Store old_date, old_time          │
│  Store new_date, new_time          │
│  (Lines 573-584)                   │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  SHOULD: Send Reschedule SMS       │
│  send_reschedule_notification()    │
│  (old_date, old_time)              │
│                                    │
│  Status: ✗ NOT CALLED              │
│  Method exists but never invoked   │
│  (Missing implementation)          │
└────────┬─────────────────────────┘
         │
         ▼
┌────────────────────────────────────┐
│  Return Response to User           │
│  "✅ Appointment Rescheduled"      │
│  (User never receives SMS)         │
└────────────────────────────────────┘
```

---

## 4. Twilio Service Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                   Django Settings                            │
│           config/settings.py (Lines 138-141)                 │
│                                                              │
│  TWILIO_ACCOUNT_SID = os.getenv('...')                      │
│  TWILIO_AUTH_TOKEN = os.getenv('...')                       │
│  TWILIO_PHONE_NUMBER = os.getenv('...')                     │
└──────────────┬───────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────┐
│         TwilioSMSService Singleton Instance                  │
│              twilio_service.py (Lines 34-307)                │
│                                                              │
│  Class TwilioSMSService:                                    │
│    __init__()                                               │
│    ├─ Initialize Twilio Client                            │
│    ├─ Set enabled=True/False based on credentials         │
│    └─ Log warning if not configured                       │
│                                                             │
│    Methods:                                                 │
│    ├─ send_sms()                                          │
│    ├─ send_appointment_confirmation()                     │
│    ├─ send_cancellation_notification()                    │
│    ├─ send_reschedule_notification()                      │
│    ├─ _normalize_phone_number()                           │
│    └─ _format_*_message()                                 │
└──────────────┬──────────────────────────────────────────────┘
               │
               ▼
        ┌──────────────┐
        │ send_sms()   │
        │ (Core Method)│
        └──────┬───────┘
               │
        ┌──────┴──────────┐
        │                 │
        ▼                 ▼
  ┌─────────────┐   ┌──────────────────┐
  │Normalize    │   │Twilio API Call   │
  │Phone Number │   │messages.create() │
  │             │   │                  │
  │India: +91   │   │Return: message_id│
  │handling     │   │                  │
  └─────┬───────┘   └────────┬─────────┘
        └──────┬─────────────┘
               │
               ▼
      ┌────────────────────────┐
      │ Error Handling         │
      │                        │
      │ 1. TwilioRestException │
      │ 2. General Exception   │
      │ 3. Return result dict  │
      │    {success, msg_id,   │
      │     error}             │
      └────────┬───────────────┘
               │
               ▼
      ┌────────────────────────┐
      │ Log SMS to Database    │
      │                        │
      │ SMSNotification model  │
      │ - Track all SMS        │
      │ - Success/failure      │
      │ - Error messages       │
      └────────────────────────┘
```

---

## 5. SMS Logging Flow

```
┌─────────────────────────────────────────┐
│     Any SMS Method Called               │
│     - send_appointment_confirmation()   │
│     - send_cancellation_notification()  │
│     - send_reschedule_notification()    │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Call send_sms() with:                  │
│  - to_phone: patient phone              │
│  - message: formatted SMS text          │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Normalize Phone Number                 │
│  (For Indian numbers: add +91 prefix)   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Call Twilio API                        │
│  client.messages.create()               │
└────────────┬────────────────────────────┘
             │
      ┌──────┴──────┐
      │             │
    SUCCESS       FAILURE
      │             │
      ▼             ▼
 ┌────────┐   ┌──────────┐
 │Get SID │   │Get Error │
 │        │   │          │
 │Return: │   │Return:   │
 │success │   │success=  │
 │=True   │   │False     │
 └────┬───┘   └────┬─────┘
      │            │
      └──────┬─────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Log SMS Notification to Database        │
│  twilio_service.py:13-31                 │
│  log_sms_notification()                  │
│                                          │
│  Create SMSNotification record:          │
│  ├─ appointment_id                       │
│  ├─ notification_type                    │
│  ├─ phone_number                         │
│  ├─ message_body                         │
│  ├─ message_sid (Twilio ID)              │
│  ├─ status ('sent' or 'failed')          │
│  ├─ error_message (if failed)            │
│  └─ timestamps                           │
└──────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│  View in Django Admin                    │
│  Admin → Appointments → SMS Notifications│
│                                          │
│  Features:                               │
│  ├─ Filter by type, status, date        │
│  ├─ Search by booking ID, phone, SID    │
│  ├─ View inline with appointment        │
│  └─ Read-only (cannot edit)             │
└──────────────────────────────────────────┘
```

---

## 6. Phone Number Normalization Flow

```
┌──────────────────────────────────────┐
│  Input: Patient Phone Number         │
│  (Any format from user input)        │
└────────────┬──────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  _normalize_phone_number()           │
│  twilio_service.py:170-199           │
│                                      │
│  Step 1: Remove all non-digits       │
│  "9876543210" → "9876543210"        │
│  "98-765-43210" → "9876543210"      │
│  "+91 9876543210" → "919876543210"  │
└────────────┬──────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  Step 2: Check Format                │
│                                      │
│  if starts with '91' AND len=12?    │
│  "919876543210" → "+919876543210"   │
│  ✓ YES                              │
│                                      │
│  elif len=10?                        │
│  "9876543210" → "+919876543210"     │
│  ✓ YES (assume India)               │
│                                      │
│  elif starts with '+'?               │
│  "+1234567890" → "+1234567890"      │
│  ✓ YES (already formatted)           │
│                                      │
│  else?                               │
│  ✗ Unusual format (log warning)     │
└────────────┬──────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  Output: E.164 Format Phone Number   │
│  "+919876543210" (Ready for Twilio) │
└──────────────────────────────────────┘
```

---

## 7. Admin Status Update Flow (No SMS)

```
┌──────────────────────────────────────────┐
│  Admin Updates Appointment Status        │
│  admin_panel/views.py:103-126            │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  update_appointment_status()             │
│  Fetch appointment by booking_id         │
│  Get new_status from POST request        │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Update Appointment                      │
│  appointment.status = new_status         │
│  appointment.save()                      │
│  (Line 110)                              │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Create AppointmentHistory Record        │
│  Track status change                     │
│  changed_by = 'admin'                    │
│  (Lines 115-120)                         │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  MISSING: Send SMS Based on Status      │
│                                          │
│  if new_status == 'cancelled':          │
│    ✗ NO CALL to                         │
│      send_cancellation_notification()   │
│                                          │
│  if new_status == 'completed':          │
│    ✗ NO LOGIC for completion SMS        │
│                                          │
│  Status: ✗ NOT IMPLEMENTED              │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────┐
│  Show Success Message                    │
│  "Appointment status updated to X"       │
│  Redirect to appointment detail          │
│                                          │
│  Note: Patient never notified via SMS   │
└──────────────────────────────────────────┘
```

---

## 8. Error Handling Decision Tree

```
                    ┌─────────────────────┐
                    │  Send SMS Request   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Is service enabled? │
                    │ (Credentials set?)  │
                    └──────────┬──────────┘
                               │
                        ┌──────┴────────┐
                        │               │
                       NO              YES
                        │               │
                        ▼               ▼
                  ┌─────────────┐  ┌──────────────┐
                  │Log Warning  │  │Send to       │
                  │"SMS not     │  │Twilio API    │
                  │configured"  │  │              │
                  │             │  │Try/Except    │
                  │Return:      │  │block         │
                  │success=False│  └──────┬───────┘
                  └─────────────┘         │
                        │         ┌───────┴──────────┐
                        │         │                  │
                        │       SUCCESS          EXCEPTION
                        │         │                  │
                        │         ▼                  ▼
                        │    ┌─────────────┐  ┌─────────────┐
                        │    │Log INFO     │  │Check Error  │
                        │    │"SMS sent    │  │Type         │
                        │    │SID: ..."    │  │             │
                        │    │             │  └──┬──────┬──┐
                        │    │Return:      │     │      │  │
                        │    │success=True │  Twilio  Other
                        │    │msg_sid=id   │     │      │  │
                        │    └─────────────┘     │      │  │
                        │         │              │      │  │
                        └─────┬───┴──────────────┴──┬───┴──┘
                              │                    │
                              ▼                    ▼
                       ┌──────────────────┐  ┌──────────────┐
                       │Log SMS Result    │  │Log ERROR     │
                       │to Database       │  │"Twilio error" or
                       │SMSNotification   │  │"Unexpected error"
                       │status='sent'     │  │              │
                       └──────────────────┘  │Log to database│
                                             │status='failed'│
                                             │error=message  │
                                             └──────────────┘
```

---

## Summary of Broken Flows

| Flow | Status | Location | Fix |
|------|--------|----------|-----|
| Appointment Confirmation | ✓ WORKING | `conversation_manager.py:1354` | None needed |
| Cancellation SMS | ✗ BROKEN | `conversation_manager.py:241` | Add SMS call after status update |
| Reschedule SMS | ✗ BROKEN | `conversation_manager.py:569` | Add SMS call after history creation |
| Admin Status SMS | ✗ NOT IMPL | `admin_panel/views.py:110` | Add SMS logic based on status change |

