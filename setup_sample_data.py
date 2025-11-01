#!/usr/bin/env python
"""
Sample Data Setup Script
Run this after migrations to populate the database with sample data
Usage: python manage.py shell < setup_sample_data.py
"""

from doctors.models import Specialization, Doctor, DoctorSchedule
from datetime import time

print("Creating sample data...")

# Create Specializations
specializations_data = [
    {
        'name': 'Orthopedic',
        'description': 'Specializes in bones, joints, and musculoskeletal system',
        'keywords': 'leg pain, bone, fracture, joint, back pain, arthritis, knee pain, shoulder pain, spine'
    },
    {
        'name': 'Cardiologist',
        'description': 'Heart and cardiovascular system specialist',
        'keywords': 'chest pain, heart, blood pressure, palpitations, cardiovascular, heart attack, cholesterol'
    },
    {
        'name': 'General Physician',
        'description': 'General health checkup and common ailments',
        'keywords': 'fever, cold, flu, general checkup, headache, cough, common ailments, routine checkup'
    },
    {
        'name': 'Dermatologist',
        'description': 'Skin, hair, and nail specialist',
        'keywords': 'skin, rash, acne, hair fall, nail problems, skin infection, allergy'
    },
    {
        'name': 'Neurologist',
        'description': 'Brain and nervous system specialist',
        'keywords': 'headache, migraine, dizziness, seizure, stroke, nerve pain, brain'
    }
]

created_specializations = {}
for spec_data in specializations_data:
    spec, created = Specialization.objects.get_or_create(
        name=spec_data['name'],
        defaults={
            'description': spec_data['description'],
            'keywords': spec_data['keywords']
        }
    )
    created_specializations[spec.name] = spec
    print(f"{'Created' if created else 'Found'} specialization: {spec.name}")

# Create Doctors
doctors_data = [
    {
        'name': 'John Smith',
        'specialization': 'Orthopedic',
        'phone': '9876543210',
        'email': 'dr.smith@hospital.com',
        'qualification': 'MBBS, MS Orthopedics',
        'experience_years': 15,
        'consultation_fee': 800.00,
        'bio': 'Specialized in sports injuries and joint replacement surgeries'
    },
    {
        'name': 'Sarah Johnson',
        'specialization': 'Cardiologist',
        'phone': '9876543211',
        'email': 'dr.johnson@hospital.com',
        'qualification': 'MBBS, MD Cardiology',
        'experience_years': 12,
        'consultation_fee': 1000.00,
        'bio': 'Expert in preventive cardiology and heart disease management'
    },
    {
        'name': 'Michael Brown',
        'specialization': 'General Physician',
        'phone': '9876543212',
        'email': 'dr.brown@hospital.com',
        'qualification': 'MBBS, MD General Medicine',
        'experience_years': 8,
        'consultation_fee': 500.00,
        'bio': 'Provides comprehensive primary care for all age groups'
    },
    {
        'name': 'Emily Davis',
        'specialization': 'Dermatologist',
        'phone': '9876543213',
        'email': 'dr.davis@hospital.com',
        'qualification': 'MBBS, MD Dermatology',
        'experience_years': 10,
        'consultation_fee': 700.00,
        'bio': 'Specializes in cosmetic dermatology and skin diseases'
    },
    {
        'name': 'Robert Wilson',
        'specialization': 'Neurologist',
        'phone': '9876543214',
        'email': 'dr.wilson@hospital.com',
        'qualification': 'MBBS, DM Neurology',
        'experience_years': 18,
        'consultation_fee': 1200.00,
        'bio': 'Expert in stroke management and epilepsy treatment'
    }
]

created_doctors = []
for doc_data in doctors_data:
    doctor, created = Doctor.objects.get_or_create(
        email=doc_data['email'],
        defaults={
            'name': doc_data['name'],
            'specialization': created_specializations[doc_data['specialization']],
            'phone': doc_data['phone'],
            'qualification': doc_data['qualification'],
            'experience_years': doc_data['experience_years'],
            'consultation_fee': doc_data['consultation_fee'],
            'bio': doc_data['bio'],
            'is_active': True
        }
    )
    created_doctors.append(doctor)
    print(f"{'Created' if created else 'Found'} doctor: Dr. {doctor.name}")
    
    # Create schedules for the doctor
    # Monday to Friday: 9 AM - 5 PM
    for day in range(5):  # 0-4 = Mon-Fri
        schedule, created = DoctorSchedule.objects.get_or_create(
            doctor=doctor,
            day_of_week=day,
            defaults={
                'start_time': time(9, 0),
                'end_time': time(17, 0),
                'slot_duration': 30,
                'is_active': True
            }
        )
        if created:
            print(f"  Added schedule for {schedule.get_day_of_week_display()}")
    
    # Saturday: 9 AM - 1 PM
    if doc_data['specialization'] in ['General Physician', 'Orthopedic']:
        schedule, created = DoctorSchedule.objects.get_or_create(
            doctor=doctor,
            day_of_week=5,  # Saturday
            defaults={
                'start_time': time(9, 0),
                'end_time': time(13, 0),
                'slot_duration': 30,
                'is_active': True
            }
        )
        if created:
            print(f"  Added schedule for Saturday")

print("\n" + "="*50)
print("Sample data setup complete!")
print("="*50)
print(f"\nCreated/Found:")
print(f"  - {len(created_specializations)} specializations")
print(f"  - {len(created_doctors)} doctors")
print(f"\nYou can now:")
print("  1. Visit http://127.0.0.1:8000/chatbot/ to test the chatbot")
print("  2. Visit http://127.0.0.1:8000/admin/ to manage data")
print("\nExample symptoms to try:")
print("  - 'I have leg pain'")
print("  - 'My knee hurts'")
print("  - 'I have chest pain'")
print("  - 'I need a general checkup'")
print("  - 'I have a skin rash'")
