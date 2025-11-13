"""
Test script for Voice Intelligence Assistant
Demonstrates the voice intelligence system with various scenarios.
"""

import json
from voice_intelligence_manager import VoiceIntelligenceManager


def print_separator():
    print("\n" + "=" * 80 + "\n")


def print_section(title):
    print(f"\n{'*' * 80}")
    print(f"* {title}")
    print(f"{'*' * 80}\n")


def test_scenario(manager, scenario_name, voice_text, session_id=None):
    """Test a single scenario."""
    print_section(f"SCENARIO: {scenario_name}")
    print(f"User says: \"{voice_text}\"\n")

    # Get intent and action (without executing)
    result = manager.get_intent_and_action(voice_text, session_id)

    print("1. UNDERSTOOD INPUT:")
    print(json.dumps(result['understood_input'], indent=2))

    print("\n2. IDENTIFIED INTENT:")
    print(json.dumps(result['intent'], indent=2))

    print("\n3. GENERATED DATABASE ACTION:")
    print(json.dumps(result['database_action'], indent=2))

    if result.get('missing_information'):
        print(f"\n4. MISSING INFORMATION: {result['missing_information']}")

    print_separator()


def main():
    """Run all test scenarios."""
    print_section("VOICE INTELLIGENCE ASSISTANT - TEST SCENARIOS")

    manager = VoiceIntelligenceManager(clinic_name="MedCare Clinic")

    # Test 1: Simple appointment booking
    test_scenario(
        manager,
        "Simple Appointment Booking",
        "I want to book appointment tomorrow morning with Dr. Rahul"
    )

    # Test 2: Appointment lookup
    test_scenario(
        manager,
        "Appointment Lookup",
        "Check my appointment with phone 9876543210"
    )

    # Test 3: Mixed language input
    test_scenario(
        manager,
        "Mixed Language Input (Indian English)",
        "Kal morning Doctor Rahul se milna hai"
    )

    # Test 4: Incomplete/noisy input
    test_scenario(
        manager,
        "Incomplete/Noisy Input",
        "um... book... doctor... tomorrow... uh"
    )

    # Test 5: Symptom-based doctor search
    test_scenario(
        manager,
        "Symptom-based Doctor Search",
        "I have fever and headache, which doctor should I see?"
    )

    # Test 6: Cancel appointment
    test_scenario(
        manager,
        "Cancel Appointment",
        "Cancel my appointment, my phone is 9876543210"
    )

    # Test 7: Reschedule appointment
    test_scenario(
        manager,
        "Reschedule Appointment",
        "I want to reschedule my appointment to next Monday 2 PM"
    )

    # Test 8: Doctor inquiry
    test_scenario(
        manager,
        "Doctor Inquiry",
        "Do you have a cardiologist available?"
    )

    # Test 9: General query
    test_scenario(
        manager,
        "General Query",
        "What are your clinic timings?"
    )

    # Test 10: Phone number extraction variations
    test_scenario(
        manager,
        "Phone Number Variations",
        "My number is nine eight seven six five four three two one zero"
    )

    print_section("FULL PROCESSING TEST (with execution simulation)")

    # Simulate a full conversation
    voice_texts = [
        "Hello, I want to book an appointment",
        "My name is John Doe",
        "I want to see Dr. Rahul",
        "Tomorrow at 10 AM",
        "My phone number is 9876543210"
    ]

    session_id = None
    for i, voice_text in enumerate(voice_texts, 1):
        print(f"\nStep {i}: User says \"{voice_text}\"")

        # This would normally execute the full process
        # For testing, we just show what would happen
        result = manager.get_intent_and_action(voice_text, session_id)

        print(f"Intent: {result['intent'].get('intent')}")
        print(f"Action: {result['database_action'].get('action')}")

        if result['database_action'].get('parameters'):
            print(f"Parameters collected: {json.dumps(result['database_action']['parameters'], indent=2)}")

        if result.get('missing_information'):
            print(f"Still missing: {result['missing_information']}")

    print_section("TEST COMPLETE")
    print("All scenarios have been tested successfully!")
    print("Check the output above to verify the voice intelligence system is working correctly.")


if __name__ == "__main__":
    main()
