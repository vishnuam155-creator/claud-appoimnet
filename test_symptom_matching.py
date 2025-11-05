#!/usr/bin/env python
"""
Test script to verify improved symptom matching
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from chatbot.claude_service import ClaudeService
from doctors.models import Specialization

print("=" * 60)
print("TESTING IMPROVED SYMPTOM MATCHING")
print("=" * 60)

# Initialize service
service = ClaudeService()

# Test cases
test_cases = [
    {
        'input': 'I have leg pain',
        'expected': 'Orthopedic',
        'reason': 'leg pain is explicitly in Orthopedic keywords'
    },
    {
        'input': 'My knee hurts when I walk',
        'expected': 'Orthopedic',
        'reason': 'knee pain is in Orthopedic keywords'
    },
    {
        'input': 'I have chest pain and palpitations',
        'expected': 'Cardiologist',
        'reason': 'chest pain and palpitations are Cardiologist keywords'
    },
    {
        'input': 'I have a fever and cold',
        'expected': 'General Physician',
        'reason': 'fever and cold are General Physician keywords'
    },
    {
        'input': 'I have a skin rash',
        'expected': 'Dermatologist',
        'reason': 'skin and rash are Dermatologist keywords'
    },
    {
        'input': 'I have severe headache and dizziness',
        'expected': 'Neurologist',
        'reason': 'headache and dizziness are Neurologist keywords'
    },
    {
        'input': 'My back hurts',
        'expected': 'Orthopedic',
        'reason': 'back pain is in Orthopedic keywords'
    }
]

# Show available specializations
print("\n📋 Available Specializations and Keywords:")
print("-" * 60)
specializations = Specialization.objects.all()
for spec in specializations:
    print(f"\n{spec.name}:")
    print(f"  Keywords: {spec.keywords}")

print("\n" + "=" * 60)
print("RUNNING TESTS")
print("=" * 60)

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n[Test {i}] Input: \"{test['input']}\"")
    print(f"Expected: {test['expected']}")
    print(f"Reason: {test['reason']}")

    result = service.analyze_symptoms(test['input'])

    print(f"Result: {result['specialization']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Reasoning: {result['reasoning']}")

    if result['specialization'] == test['expected']:
        print("✅ PASSED")
        passed += 1
    else:
        print("❌ FAILED")
        failed += 1

print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 60)

if failed == 0:
    print("🎉 All tests passed!")
else:
    print(f"⚠️  {failed} test(s) failed. Please review the logic.")
