"""
Database Action Handler
Processes structured JSON actions and executes corresponding database operations.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, time as dt_time
from difflib import SequenceMatcher
from django.db.models import Q
from django.utils import timezone

from doctors.models import Doctor, DoctorSchedule, Specialization
from appointments.models import Appointment


class DatabaseActionHandler:
    """
    Executes database operations based on structured JSON actions.
    Receives actions from Voice Intelligence Service and returns results.
    """

    def execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute database action and return results.

        Args:
            action: JSON action from Voice Intelligence Service
            {
                "action": "query_database",
                "query_type": "create_appointment/appointment_lookup/etc",
                "parameters": {...}
            }

        Returns:
            {
                "status": "success/error",
                "message": "human readable message",
                "data": {...}
            }
        """
        action_type = action.get('action')
        query_type = action.get('query_type')
        parameters = action.get('parameters', {})

        if action_type != 'query_database':
            return {
                "status": "error",
                "message": "Invalid action type",
                "data": None
            }

        # Route to appropriate handler
        handlers = {
            'create_appointment': self.create_appointment,
            'appointment_lookup': self.lookup_appointment,
            'cancel_appointment': self.cancel_appointment,
            'reschedule_appointment': self.reschedule_appointment,
            'get_doctors': self.get_doctors,
            'check_availability': self.check_availability,
            'get_doctor_by_symptoms': self.get_doctor_by_symptoms
        }

        handler = handlers.get(query_type)

        if not handler:
            return {
                "status": "error",
                "message": f"Unknown query type: {query_type}",
                "data": None
            }

        try:
            return handler(parameters)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database operation failed: {str(e)}",
                "data": None
            }

    # ========================
    # APPOINTMENT OPERATIONS
    # ========================

    def create_appointment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new appointment.

        Required params:
            - patient_name
            - phone
            - doctor_id or doctor_name
            - date (YYYY-MM-DD)
            - time (HH:MM AM/PM)
        """
        # Validate required fields
        required = ['patient_name', 'phone', 'date', 'time']
        missing = [f for f in required if not params.get(f)]

        if missing:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}",
                "data": {"missing_fields": missing}
            }

        # Get or find doctor
        doctor = None
        if params.get('doctor_id'):
            try:
                doctor = Doctor.objects.get(id=params['doctor_id'], is_active=True)
            except Doctor.DoesNotExist:
                return {
                    "status": "error",
                    "message": "Doctor not found",
                    "data": None
                }
        elif params.get('doctor_name'):
            doctor = self._find_doctor_by_name(params['doctor_name'])
            if not doctor:
                return {
                    "status": "error",
                    "message": f"Doctor '{params['doctor_name']}' not found",
                    "data": None
                }
        else:
            return {
                "status": "error",
                "message": "Doctor ID or name is required",
                "data": None
            }

        # Parse date and time
        try:
            appointment_date = datetime.strptime(params['date'], '%Y-%m-%d').date()
            appointment_time = datetime.strptime(params['time'], '%I:%M %p').time()
        except ValueError as e:
            return {
                "status": "error",
                "message": f"Invalid date or time format: {str(e)}",
                "data": None
            }

        # Validate date is in future
        if appointment_date < timezone.now().date():
            return {
                "status": "error",
                "message": "Appointment date must be in the future",
                "data": None
            }

        # Check availability
        is_available = self._check_slot_availability(doctor, appointment_date, appointment_time)
        if not is_available:
            return {
                "status": "error",
                "message": "Selected time slot is not available",
                "data": {"reason": "slot_occupied"}
            }

        # Create appointment
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient_name=params['patient_name'],
            patient_phone=params['phone'],
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status='confirmed',
            booking_method='voice_assistant',
            notes=params.get('symptoms', '')
        )

        return {
            "status": "success",
            "message": "Appointment created successfully",
            "data": {
                "appointment_id": appointment.id,
                "booking_id": f"APT{appointment.id:06d}",
                "doctor_name": doctor.name,
                "doctor_specialization": doctor.specialization.name if doctor.specialization else "",
                "patient_name": params['patient_name'],
                "appointment_date": params['date'],
                "appointment_time": params['time'],
                "status": "confirmed"
            }
        }

    def lookup_appointment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Look up existing appointments.

        Params:
            - phone (required) or
            - appointment_id or
            - name + phone
        """
        query = Q()

        if params.get('appointment_id'):
            query &= Q(id=params['appointment_id'])
        elif params.get('phone'):
            query &= Q(patient_phone=params['phone'])
            if params.get('name'):
                query &= Q(patient_name__icontains=params['name'])
        else:
            return {
                "status": "error",
                "message": "Phone number or appointment ID is required",
                "data": None
            }

        appointments = Appointment.objects.filter(query).select_related('doctor', 'doctor__specialization').order_by('-appointment_date')

        if not appointments.exists():
            return {
                "status": "success",
                "message": "No appointments found",
                "data": []
            }

        appointments_data = []
        for apt in appointments:
            appointments_data.append({
                "appointment_id": apt.id,
                "booking_id": f"APT{apt.id:06d}",
                "doctor_name": apt.doctor.name,
                "doctor_specialization": apt.doctor.specialization.name if apt.doctor.specialization else "",
                "patient_name": apt.patient_name,
                "appointment_date": apt.appointment_date.strftime('%Y-%m-%d'),
                "appointment_time": apt.appointment_time.strftime('%I:%M %p'),
                "status": apt.status
            })

        return {
            "status": "success",
            "message": f"Found {len(appointments_data)} appointment(s)",
            "data": appointments_data
        }

    def cancel_appointment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cancel an appointment.

        Required params:
            - appointment_id
            - phone (for verification)
        """
        if not params.get('appointment_id') or not params.get('phone'):
            return {
                "status": "error",
                "message": "Appointment ID and phone number are required",
                "data": None
            }

        try:
            appointment = Appointment.objects.get(
                id=params['appointment_id'],
                patient_phone=params['phone']
            )

            # Check if already cancelled
            if appointment.status == 'cancelled':
                return {
                    "status": "success",
                    "message": "Appointment was already cancelled",
                    "data": {"appointment_id": appointment.id}
                }

            # Cancel appointment
            appointment.status = 'cancelled'
            appointment.save()

            return {
                "status": "success",
                "message": "Appointment cancelled successfully",
                "data": {
                    "appointment_id": appointment.id,
                    "booking_id": f"APT{appointment.id:06d}",
                    "doctor_name": appointment.doctor.name,
                    "original_date": appointment.appointment_date.strftime('%Y-%m-%d'),
                    "original_time": appointment.appointment_time.strftime('%I:%M %p')
                }
            }

        except Appointment.DoesNotExist:
            return {
                "status": "error",
                "message": "Appointment not found or phone number doesn't match",
                "data": None
            }

    def reschedule_appointment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reschedule an existing appointment.

        Required params:
            - appointment_id
            - phone (for verification)
            - new_date
            - new_time
        """
        required = ['appointment_id', 'phone', 'new_date', 'new_time']
        missing = [f for f in required if not params.get(f)]

        if missing:
            return {
                "status": "error",
                "message": f"Missing required fields: {', '.join(missing)}",
                "data": {"missing_fields": missing}
            }

        try:
            appointment = Appointment.objects.get(
                id=params['appointment_id'],
                patient_phone=params['phone']
            )

            # Parse new date and time
            new_date = datetime.strptime(params['new_date'], '%Y-%m-%d').date()
            new_time = datetime.strptime(params['new_time'], '%I:%M %p').time()

            # Validate new date
            if new_date < timezone.now().date():
                return {
                    "status": "error",
                    "message": "New appointment date must be in the future",
                    "data": None
                }

            # Check availability for new slot
            is_available = self._check_slot_availability(appointment.doctor, new_date, new_time, exclude_appointment_id=appointment.id)
            if not is_available:
                return {
                    "status": "error",
                    "message": "Selected time slot is not available",
                    "data": None
                }

            # Update appointment
            old_date = appointment.appointment_date.strftime('%Y-%m-%d')
            old_time = appointment.appointment_time.strftime('%I:%M %p')

            appointment.appointment_date = new_date
            appointment.appointment_time = new_time
            appointment.save()

            return {
                "status": "success",
                "message": "Appointment rescheduled successfully",
                "data": {
                    "appointment_id": appointment.id,
                    "booking_id": f"APT{appointment.id:06d}",
                    "doctor_name": appointment.doctor.name,
                    "old_date": old_date,
                    "old_time": old_time,
                    "new_date": params['new_date'],
                    "new_time": params['new_time']
                }
            }

        except Appointment.DoesNotExist:
            return {
                "status": "error",
                "message": "Appointment not found or phone number doesn't match",
                "data": None
            }
        except ValueError as e:
            return {
                "status": "error",
                "message": f"Invalid date or time format: {str(e)}",
                "data": None
            }

    # ========================
    # DOCTOR OPERATIONS
    # ========================

    def get_doctors(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get list of doctors based on criteria.

        Optional params:
            - doctor_name: Filter by name (fuzzy match)
            - specialization: Filter by specialization
            - symptoms: Find doctors by symptoms
        """
        if params.get('symptoms'):
            return self.get_doctor_by_symptoms(params)

        query = Q(is_active=True)

        if params.get('doctor_name'):
            # Fuzzy name matching
            all_doctors = Doctor.objects.filter(is_active=True)
            matched_doctors = []

            for doctor in all_doctors:
                similarity = SequenceMatcher(None, params['doctor_name'].lower(), doctor.name.lower()).ratio()
                if similarity > 0.7:  # 70% match threshold
                    matched_doctors.append(doctor)

            doctors = matched_doctors
        else:
            if params.get('specialization'):
                try:
                    specialization = Specialization.objects.get(name__icontains=params['specialization'])
                    query &= Q(specialization=specialization)
                except Specialization.DoesNotExist:
                    pass

            doctors = Doctor.objects.filter(query).select_related('specialization')

        if not doctors:
            return {
                "status": "success",
                "message": "No doctors found matching criteria",
                "data": {"doctors": []}
            }

        doctors_data = []
        for doctor in doctors:
            doctors_data.append({
                "id": doctor.id,
                "name": doctor.name,
                "specialization": doctor.specialization.name if doctor.specialization else "General Physician",
                "consultation_fee": str(doctor.consultation_fee) if doctor.consultation_fee else None
            })

        return {
            "status": "success",
            "message": f"Found {len(doctors_data)} doctor(s)",
            "data": {"doctors": doctors_data}
        }

    def get_doctor_by_symptoms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recommend doctors based on symptoms.

        Required params:
            - symptoms: List of symptoms or symptom string
        """
        symptoms = params.get('symptoms', [])
        if isinstance(symptoms, str):
            symptoms = [symptoms]

        if not symptoms:
            # Return general physicians
            doctors = Doctor.objects.filter(
                is_active=True,
                specialization__name__icontains="General"
            ).select_related('specialization')[:3]
        else:
            # Match symptoms to specializations
            symptom_text = ' '.join(symptoms).lower()

            # Try to find matching specialization
            specializations = Specialization.objects.all()
            matched_spec = None
            max_match = 0

            for spec in specializations:
                keywords = spec.keywords.lower() if spec.keywords else ""
                match_count = sum(1 for symptom in symptoms if symptom.lower() in keywords)
                if match_count > max_match:
                    max_match = match_count
                    matched_spec = spec

            if matched_spec:
                doctors = Doctor.objects.filter(
                    is_active=True,
                    specialization=matched_spec
                ).select_related('specialization')[:3]
            else:
                # Default to general physician
                doctors = Doctor.objects.filter(
                    is_active=True,
                    specialization__name__icontains="General"
                ).select_related('specialization')[:3]

        if not doctors:
            return {
                "status": "success",
                "message": "No doctors available",
                "data": {"doctors": []}
            }

        doctors_data = []
        for doctor in doctors:
            doctors_data.append({
                "id": doctor.id,
                "name": doctor.name,
                "specialization": doctor.specialization.name if doctor.specialization else "General Physician",
                "consultation_fee": str(doctor.consultation_fee) if doctor.consultation_fee else None
            })

        return {
            "status": "success",
            "message": f"Recommended {len(doctors_data)} doctor(s) for your symptoms",
            "data": {"doctors": doctors_data}
        }

    def check_availability(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check availability for a doctor on a specific date.

        Required params:
            - doctor_id or doctor_name
            - date (YYYY-MM-DD)
        """
        # Get doctor
        doctor = None
        if params.get('doctor_id'):
            try:
                doctor = Doctor.objects.get(id=params['doctor_id'], is_active=True)
            except Doctor.DoesNotExist:
                return {
                    "status": "error",
                    "message": "Doctor not found",
                    "data": None
                }
        elif params.get('doctor_name'):
            doctor = self._find_doctor_by_name(params['doctor_name'])

        if not doctor:
            return {
                "status": "error",
                "message": "Doctor not specified or not found",
                "data": None
            }

        # Parse date
        try:
            check_date = datetime.strptime(params['date'], '%Y-%m-%d').date()
        except ValueError:
            return {
                "status": "error",
                "message": "Invalid date format. Use YYYY-MM-DD",
                "data": None
            }

        # Get available slots
        available_slots = self._get_available_slots(doctor, check_date)

        return {
            "status": "success",
            "message": f"Found {len(available_slots)} available slots",
            "data": {
                "doctor_name": doctor.name,
                "date": params['date'],
                "available_slots": available_slots
            }
        }

    # ========================
    # HELPER METHODS
    # ========================

    def _find_doctor_by_name(self, name: str) -> Optional[Doctor]:
        """Find doctor by name using fuzzy matching."""
        all_doctors = Doctor.objects.filter(is_active=True)

        best_match = None
        best_similarity = 0

        for doctor in all_doctors:
            similarity = SequenceMatcher(None, name.lower(), doctor.name.lower()).ratio()
            if similarity > best_similarity and similarity > 0.7:  # 70% threshold
                best_similarity = similarity
                best_match = doctor

        return best_match

    def _check_slot_availability(
        self,
        doctor: Doctor,
        date: datetime.date,
        time: dt_time,
        exclude_appointment_id: int = None
    ) -> bool:
        """Check if a specific time slot is available."""
        # Check if doctor has schedule for this day
        weekday = date.strftime('%A')
        schedule = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week=weekday
        ).first()

        if not schedule:
            return False

        # Check if time is within schedule
        if time < schedule.start_time or time >= schedule.end_time:
            return False

        # Check if slot is already booked
        existing_query = Q(
            doctor=doctor,
            appointment_date=date,
            appointment_time=time,
            status__in=['pending', 'confirmed']
        )

        if exclude_appointment_id:
            existing_query &= ~Q(id=exclude_appointment_id)

        existing = Appointment.objects.filter(existing_query).exists()

        return not existing

    def _get_available_slots(self, doctor: Doctor, date: datetime.date) -> List[str]:
        """Get all available time slots for a doctor on a specific date."""
        weekday = date.strftime('%A')
        schedule = DoctorSchedule.objects.filter(
            doctor=doctor,
            day_of_week=weekday
        ).first()

        if not schedule:
            return []

        # Generate all possible slots
        slots = []
        current_time = datetime.combine(date, schedule.start_time)
        end_time = datetime.combine(date, schedule.end_time)
        slot_duration = schedule.slot_duration or 30  # Default 30 minutes

        while current_time < end_time:
            slots.append(current_time.time())
            current_time += timedelta(minutes=slot_duration)

        # Filter out booked slots
        booked_times = Appointment.objects.filter(
            doctor=doctor,
            appointment_date=date,
            status__in=['pending', 'confirmed']
        ).values_list('appointment_time', flat=True)

        available_slots = [
            slot.strftime('%I:%M %p')
            for slot in slots
            if slot not in booked_times
        ]

        return available_slots
