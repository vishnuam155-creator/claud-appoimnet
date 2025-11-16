"""
RAG Retriever - Database Context Retrieval for Appointment Booking
Retrieves relevant information from database to provide context to LLM
"""

from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db.models import Q, Count, F
from doctors.models import Doctor, DoctorSchedule, Specialization, DoctorLeave
from appointments.models import Appointment


class RAGRetriever:
    """
    Retrieves relevant context from database for RAG-based conversation
    """

    def __init__(self):
        self.cache = {}

    def get_all_context_for_conversation(self, session_data):
        """
        Retrieve all relevant context for current conversation state

        Returns comprehensive context including:
        - Available doctors
        - Specializations
        - Appointment slots
        - Patient history (if applicable)
        """
        context = {
            'doctors': self.get_all_doctors_context(),
            'specializations': self.get_specializations_context(),
            'current_booking': self.extract_current_booking_state(session_data)
        }

        # Add doctor-specific context if doctor is selected
        if session_data.get('doctor_id'):
            context['selected_doctor'] = self.get_doctor_details(session_data['doctor_id'])
            context['doctor_availability'] = self.get_doctor_availability_summary(session_data['doctor_id'])

        # Add slot context if date is selected
        if session_data.get('doctor_id') and session_data.get('appointment_date'):
            try:
                date_obj = datetime.fromisoformat(session_data['appointment_date']).date()
                context['available_slots'] = self.get_available_slots_context(
                    session_data['doctor_id'],
                    date_obj
                )
            except Exception as e:
                print(f"Error getting slots context: {e}")

        return context

    def get_all_doctors_context(self):
        """Get all active doctors with their details"""
        doctors = Doctor.objects.filter(is_active=True).select_related('specialization')

        return [
            {
                'id': doc.id,
                'name': doc.name,
                'specialization': doc.specialization.name if doc.specialization else 'General',
                'qualification': doc.qualification,
                'experience_years': doc.experience_years,
                'consultation_fee': float(doc.consultation_fee) if doc.consultation_fee else 0,
                'keywords': doc.specialization.keywords if doc.specialization else ''
            }
            for doc in doctors
        ]

    def get_specializations_context(self):
        """Get all specializations with keywords for symptom matching"""
        specializations = Specialization.objects.all()

        return [
            {
                'name': spec.name,
                'description': spec.description,
                'keywords': spec.keywords,
                'doctor_count': Doctor.objects.filter(
                    specialization=spec,
                    is_active=True
                ).count()
            }
            for spec in specializations
        ]

    def get_doctor_details(self, doctor_id):
        """Get detailed information about a specific doctor"""
        try:
            doctor = Doctor.objects.select_related('specialization').get(id=doctor_id)
            return {
                'id': doctor.id,
                'name': doctor.name,
                'specialization': doctor.specialization.name if doctor.specialization else 'General',
                'qualification': doctor.qualification,
                'experience_years': doctor.experience_years,
                'consultation_fee': float(doctor.consultation_fee) if doctor.consultation_fee else 0,
                'bio': doctor.bio,
                'phone': doctor.phone,
                'email': doctor.email
            }
        except Doctor.DoesNotExist:
            return None

    def get_doctor_availability_summary(self, doctor_id, days_ahead=14):
        """
        Get summary of doctor's availability for next N days
        """
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            today = timezone.now().date()
            availability = []

            for i in range(days_ahead):
                check_date = today + timedelta(days=i)
                slots = self.get_available_slots_count(doctor_id, check_date)

                if slots > 0:
                    availability.append({
                        'date': check_date.isoformat(),
                        'day_name': check_date.strftime('%A'),
                        'available_slots': slots
                    })

            return availability[:7]  # Return next 7 days with availability

        except Doctor.DoesNotExist:
            return []

    def get_available_slots_count(self, doctor_id, date):
        """Count available slots for a doctor on a specific date"""
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            day_name = date.strftime('%A')

            # Get day of week (0=Monday, 6=Sunday)
            day_mapping = {
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6
            }
            day_of_week = day_mapping.get(day_name, -1)

            # Check if doctor has schedule for this day
            schedules = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=day_of_week,
                is_active=True
            )

            if not schedules.exists():
                return 0

            # Check for leaves
            is_on_leave = DoctorLeave.objects.filter(
                doctor=doctor,
                start_date__lte=date,
                end_date__gte=date
            ).exists()

            if is_on_leave:
                return 0

            # Count booked appointments
            booked_count = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                status__in=['pending', 'confirmed']
            ).count()

            # Calculate total possible slots
            total_slots = 0
            for schedule in schedules:
                start = datetime.combine(date, schedule.start_time)
                end = datetime.combine(date, schedule.end_time)
                duration = timedelta(minutes=schedule.slot_duration)

                current = start
                while current + duration <= end:
                    total_slots += 1
                    current += duration

            return max(0, total_slots - booked_count)

        except Exception as e:
            print(f"Error counting slots: {e}")
            return 0

    def get_available_slots_context(self, doctor_id, date):
        """Get detailed available slots for a specific date"""
        try:
            doctor = Doctor.objects.get(id=doctor_id)
            day_name = date.strftime('%A')

            # Get day of week (0=Monday, 6=Sunday)
            day_mapping = {
                'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3,
                'Friday': 4, 'Saturday': 5, 'Sunday': 6
            }
            day_of_week = day_mapping.get(day_name, -1)

            schedules = DoctorSchedule.objects.filter(
                doctor=doctor,
                day_of_week=day_of_week,
                is_active=True
            )

            if not schedules.exists():
                return {'available': False, 'reason': 'Doctor not available on this day', 'slots': []}

            # Check for leaves
            is_on_leave = DoctorLeave.objects.filter(
                doctor=doctor,
                start_date__lte=date,
                end_date__gte=date
            ).exists()

            if is_on_leave:
                return {'available': False, 'reason': 'Doctor is on leave', 'slots': []}

            # Get booked times
            booked_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=date,
                status__in=['pending', 'confirmed']
            ).values_list('appointment_time', flat=True)

            booked_times = [time.strftime('%I:%M %p') for time in booked_appointments]

            # Generate all slots
            all_slots = []
            for schedule in schedules:
                current_time = datetime.combine(date, schedule.start_time)
                end_time = datetime.combine(date, schedule.end_time)

                while current_time < end_time:
                    time_str = current_time.strftime('%I:%M %p')
                    all_slots.append({
                        'time': time_str,
                        'available': time_str not in booked_times
                    })
                    current_time += timedelta(minutes=schedule.slot_duration)

            available_count = sum(1 for slot in all_slots if slot['available'])

            return {
                'available': available_count > 0,
                'total_slots': len(all_slots),
                'available_count': available_count,
                'slots': all_slots
            }

        except Exception as e:
            print(f"Error getting slots context: {e}")
            return {'available': False, 'reason': f'Error: {str(e)}', 'slots': []}

    def find_alternative_doctors(self, specialization_name, current_doctor_id=None, limit=3):
        """
        Find alternative doctors in same specialization with availability
        """
        try:
            # Find specialization
            specialization = Specialization.objects.filter(
                Q(name__iexact=specialization_name) |
                Q(name__icontains=specialization_name)
            ).first()

            if not specialization:
                return []

            # Get alternative doctors
            query = Doctor.objects.filter(
                specialization=specialization,
                is_active=True
            ).order_by('consultation_fee')

            if current_doctor_id:
                query = query.exclude(id=current_doctor_id)

            alternative_doctors = query[:limit]

            results = []
            today = timezone.now().date()

            for doctor in alternative_doctors:
                # Find next available date
                next_available = self.find_next_available_date(doctor.id, today, max_days=30)

                if next_available:
                    results.append({
                        'id': doctor.id,
                        'name': doctor.name,
                        'consultation_fee': float(doctor.consultation_fee) if doctor.consultation_fee else 0,
                        'next_available_date': next_available.isoformat(),
                        'days_away': (next_available - today).days
                    })

            return results

        except Exception as e:
            print(f"Error finding alternatives: {e}")
            return []

    def find_next_available_date(self, doctor_id, start_date, max_days=30):
        """Find next available date for a doctor"""
        current_date = start_date

        for _ in range(max_days):
            slots_count = self.get_available_slots_count(doctor_id, current_date)
            if slots_count > 0:
                return current_date
            current_date += timedelta(days=1)

        return None

    def search_doctors_by_symptoms(self, symptoms_text):
        """
        Search for doctors based on symptom keywords
        Returns relevant specializations and doctors
        """
        symptoms_lower = symptoms_text.lower()

        # Search specializations by keywords
        matching_specializations = []

        for spec in Specialization.objects.all():
            keywords = spec.keywords.lower() if spec.keywords else ''
            keyword_list = [k.strip() for k in keywords.split(',')]

            # Check if any keyword matches symptoms
            matches = [kw for kw in keyword_list if kw and kw in symptoms_lower]

            if matches:
                matching_specializations.append({
                    'specialization': spec,
                    'match_count': len(matches),
                    'matched_keywords': matches
                })

        # Sort by match count
        matching_specializations.sort(key=lambda x: x['match_count'], reverse=True)

        results = []
        for match in matching_specializations[:3]:
            spec = match['specialization']
            doctors = Doctor.objects.filter(
                specialization=spec,
                is_active=True
            ).order_by('consultation_fee')[:2]

            results.append({
                'specialization': spec.name,
                'matched_keywords': match['matched_keywords'],
                'doctors': [
                    {
                        'id': doc.id,
                        'name': doc.name,
                        'fee': float(doc.consultation_fee) if doc.consultation_fee else 0
                    }
                    for doc in doctors
                ]
            })

        return results

    def extract_current_booking_state(self, session_data):
        """Extract current booking state for context"""
        return {
            'stage': session_data.get('stage', 'greeting'),
            'patient_name': session_data.get('patient_name'),
            'doctor_id': session_data.get('doctor_id'),
            'doctor_name': session_data.get('doctor_name'),
            'appointment_date': session_data.get('appointment_date'),
            'appointment_time': session_data.get('appointment_time'),
            'phone': session_data.get('phone')
        }

    def get_patient_history(self, phone_number):
        """
        Get patient's booking history if available
        """
        try:
            appointments = Appointment.objects.filter(
                patient_phone=phone_number
            ).select_related('doctor', 'doctor__specialization').order_by('-appointment_date')[:5]

            return [
                {
                    'doctor': apt.doctor.name,
                    'specialization': apt.doctor.specialization.name if apt.doctor.specialization else 'General',
                    'date': apt.appointment_date.isoformat(),
                    'status': apt.status
                }
                for apt in appointments
            ]

        except Exception as e:
            print(f"Error getting patient history: {e}")
            return []
