from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import JsonResponse
from datetime import datetime, timedelta
from appointments.models import Appointment
from doctors.models import Doctor
import calendar
import json


@staff_member_required
def dashboard(request):
    """Admin dashboard with statistics"""
    today = datetime.now().date()
    
    # Statistics
    total_appointments = Appointment.objects.count()
    today_appointments = Appointment.objects.filter(appointment_date=today).count()
    pending_appointments = Appointment.objects.filter(status='pending').count()
    confirmed_appointments = Appointment.objects.filter(status='confirmed').count()
    
    # Upcoming appointments (next 7 days)
    upcoming = Appointment.objects.filter(
        appointment_date__gte=today,
        appointment_date__lte=today + timedelta(days=7),
        status__in=['pending', 'confirmed']
    ).order_by('appointment_date', 'appointment_time')[:10]
    
    # Recent appointments
    recent = Appointment.objects.all().order_by('-created_at')[:10]
    
    context = {
        'total_appointments': total_appointments,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'confirmed_appointments': confirmed_appointments,
        'upcoming_appointments': upcoming,
        'recent_appointments': recent,
    }
    
    return render(request, 'admin_panel/dashboard.html', context)


@staff_member_required
def appointment_list(request):
    """List all appointments with filters"""
    appointments = Appointment.objects.all().select_related('doctor', 'doctor__specialization')
    
    # Filters
    status = request.GET.get('status')
    doctor_id = request.GET.get('doctor')
    date = request.GET.get('date')
    search = request.GET.get('search')
    
    if status:
        appointments = appointments.filter(status=status)
    
    if doctor_id:
        appointments = appointments.filter(doctor_id=doctor_id)
    
    if date:
        appointments = appointments.filter(appointment_date=date)
    
    if search:
        appointments = appointments.filter(
            Q(patient_name__icontains=search) |
            Q(patient_phone__icontains=search) |
            Q(booking_id__icontains=search)
        )
    
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    
    # Get doctors for filter
    doctors = Doctor.objects.filter(is_active=True)
    
    context = {
        'appointments': appointments,
        'doctors': doctors,
        'selected_status': status,
        'selected_doctor': doctor_id,
        'selected_date': date,
        'search_query': search,
    }
    
    return render(request, 'admin_panel/appointment_list.html', context)


@staff_member_required
def appointment_detail(request, booking_id):
    """View appointment details"""
    appointment = get_object_or_404(Appointment, booking_id=booking_id)
    
    context = {
        'appointment': appointment,
    }
    
    return render(request, 'admin_panel/appointment_detail.html', context)


@staff_member_required
def update_appointment_status(request, booking_id):
    """Update appointment status"""
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, booking_id=booking_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(Appointment.STATUS_CHOICES).keys():
            appointment.status = new_status
            appointment.save()
            
            # Create history entry
            from appointments.models import AppointmentHistory
            AppointmentHistory.objects.create(
                appointment=appointment,
                status=new_status,
                notes=request.POST.get('notes', ''),
                changed_by='admin'
            )
            
            messages.success(request, f'Appointment status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status')
    
    return redirect('admin_panel:appointment_detail', booking_id=booking_id)


@staff_member_required
def calendar_view(request):
    """Calendar view of all appointments"""
    # Get selected month and year
    today = datetime.now().date()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Get appointments for this month
    appointments = Appointment.objects.filter(
        appointment_date__year=year,
        appointment_date__month=month
    ).select_related('doctor', 'doctor__specialization')

    # Group by date with count (JSON serializable)
    appointments_by_date = {}
    appointments_by_date_json = {}
    for apt in appointments:
        date_key = apt.appointment_date.strftime('%Y-%m-%d')
        if date_key not in appointments_by_date:
            appointments_by_date[date_key] = {'count': 0, 'appointments': []}
            appointments_by_date_json[date_key] = {'count': 0}
        appointments_by_date[date_key]['count'] += 1
        appointments_by_date[date_key]['appointments'].append(apt)
        appointments_by_date_json[date_key]['count'] += 1

    # Generate calendar data
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    # Calculate previous and next month/year
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'calendar_weeks': cal,
        'appointments_by_date': appointments_by_date,
        'appointments_by_date_json': json.dumps(appointments_by_date_json),
        'today': today.strftime('%Y-%m-%d'),
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }

    return render(request, 'admin_panel/calendar.html', context)


@staff_member_required
def get_appointments_by_date(request):
    """API endpoint to fetch appointments for a specific date"""
    date_str = request.GET.get('date')

    if not date_str:
        return JsonResponse({'success': False, 'error': 'Date parameter is required'}, status=400)

    try:
        # Parse the date
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Fetch appointments for this date
        appointments = Appointment.objects.filter(
            appointment_date=date_obj
        ).select_related('doctor', 'doctor__specialization').order_by('appointment_time')

        # Format the data
        appointments_data = []
        for apt in appointments:
            appointments_data.append({
                'booking_id': apt.booking_id,
                'patient_name': apt.patient_name,
                'patient_phone': apt.patient_phone,
                'patient_email': apt.patient_email,
                'doctor_name': apt.doctor.name,
                'specialization': apt.doctor.specialization.name if apt.doctor.specialization else 'N/A',
                'appointment_time': apt.appointment_time.strftime('%I:%M %p'),
                'symptoms': apt.symptoms,
                'status': apt.status,
                'status_display': dict(Appointment.STATUS_CHOICES).get(apt.status, apt.status),
                'created_at': apt.created_at.strftime('%Y-%m-%d %I:%M %p'),
            })

        return JsonResponse({
            'success': True,
            'date': date_str,
            'appointments': appointments_data,
            'count': len(appointments_data)
        })

    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid date format'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
