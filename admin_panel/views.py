from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Q, Count
from datetime import datetime, timedelta
from appointments.models import Appointment
from doctors.models import Doctor


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
        appointment_date__month=month,
        status__in=['pending', 'confirmed']
    ).select_related('doctor')
    
    # Group by date
    appointments_by_date = {}
    for apt in appointments:
        date_key = apt.appointment_date.strftime('%Y-%m-%d')
        if date_key not in appointments_by_date:
            appointments_by_date[date_key] = []
        appointments_by_date[date_key].append(apt)
    
    context = {
        'year': year,
        'month': month,
        'appointments_by_date': appointments_by_date,
    }
    
    return render(request, 'admin_panel/calendar.html', context)
