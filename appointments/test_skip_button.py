"""
Direct test of skip button in patient details stage
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from chatbot.conversation_manager import ConversationManager

print("="*60)
print("DIRECT SKIP BUTTON TEST")
print("="*60)

# Create manager with pre-populated state
session_id = "test_direct_skip"
manager = ConversationManager(session_id)

# Manually set state to patient_details stage with all required data
manager.state = {
    'stage': 'patient_details',
    'conversation_history': [],
    'data': {
        'doctor_id': 1,
        'doctor_name': 'John Smith',
        'symptoms': 'Test symptoms',
        'appointment_date': '2025-10-31',
        'appointment_time': '09:00',
        'patient_name': 'Test Patient',
        'patient_phone': '1234567890'
    }
}
manager._save_state()

print("\nCurrent state: patient_details (ready for email)")
print("Data collected:", manager.state['data'])

# Test skip button
print("\n1. Testing 'skip_email' message...")
response = manager.process_message("skip_email")

if 'Appointment Confirmed' in response['message']:
    print("   ✅ SUCCESS! Appointment created")
    print(f"   Booking ID: {response.get('booking_id')}")
else:
    print("   ❌ FAILED!")
    print(f"   Message: {response['message'][:100]}")
    print(f"   Action: {response['action']}")

# Test again with 'skip'
print("\n2. Testing 'skip' message...")
manager.state['data'].pop('patient_email', None)  # Reset
manager.state['stage'] = 'patient_details'
manager._save_state()

response = manager.process_message("skip")

if 'Appointment Confirmed' in response['message']:
    print("   ✅ SUCCESS! Appointment created")
    print(f"   Booking ID: {response.get('booking_id')}")
else:
    print("   ❌ FAILED!")
    print(f"   Message: {response['message'][:100]}")

print("\n" + "="*60)