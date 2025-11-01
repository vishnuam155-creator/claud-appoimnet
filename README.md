# 🏥 Medical Appointment System with AI Chatbot

A Django-based appointment booking system with Claude AI-powered chatbot for intelligent symptom analysis and doctor recommendations.

## ✨ Features

### Patient Side
- 🤖 **AI Chatbot Interface** - Natural conversation flow for booking appointments
- 🔍 **Symptom Analysis** - Claude AI analyzes symptoms and suggests appropriate doctors
- 👨‍⚕️ **Doctor Selection** - View available doctors by specialization
- 📅 **Date & Time Selection** - Real-time availability checking
- ✅ **Instant Confirmation** - Get booking ID immediately

### Admin Side
- 📊 **Dashboard** - Overview of all appointments and statistics
- 📋 **Appointment Management** - View, filter, and manage all bookings
- 📆 **Calendar View** - Visual representation of appointments
- 👨‍⚕️ **Doctor Management** - Add/edit doctors, schedules, and specializations
- 📈 **Status Tracking** - Track appointment history and changes

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Installation

1. **Extract the ZIP file**
   ```bash
   unzip appointment_system.zip
   cd appointment_system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   - Copy `.env.example` to `.env`
   ```bash
   cp .env.example .env
   ```
   
   - Edit `.env` and add your Claude API key:
   ```
   ANTHROPIC_API_KEY=your-api-key-here
   ```
   
   **Get Claude API Key:** 
   - Visit https://console.anthropic.com/
   - Sign up/login
   - Go to API Keys section
   - Create new API key

5. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser (admin account)**
   ```bash
   python manage.py createsuperuser
   ```
   Follow prompts to create admin credentials.

7. **Load sample data (Optional)**
   ```bash
   python manage.py shell < setup_sample_data.py
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Patient Interface: http://127.0.0.1:8000/
   - Chatbot: http://127.0.0.1:8000/chatbot/
   - Admin Panel: http://127.0.0.1:8000/admin/
   - Custom Admin Dashboard: http://127.0.0.1:8000/admin-panel/

## 📂 Project Structure

```
appointment_system/
├── config/                     # Main Django settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── doctors/                    # Doctor management app
│   ├── models.py              # Doctor, Specialization, Schedule models
│   └── admin.py               # Admin configuration
├── appointments/               # Appointment booking app
│   ├── models.py              # Appointment, History models
│   └── admin.py               # Admin configuration
├── chatbot/                    # AI chatbot logic
│   ├── claude_service.py      # Claude AI integration
│   └── conversation_manager.py # Conversation flow management
├── patient_booking/            # Patient-facing views
│   ├── views.py               # Chatbot API endpoints
│   └── urls.py
├── admin_panel/                # Custom admin dashboard
│   ├── views.py               # Dashboard, calendar views
│   └── urls.py
├── templates/                  # HTML templates
│   └── patient_booking/
│       ├── home.html
│       └── chatbot.html
├── static/                     # CSS, JS, images
├── media/                      # Uploaded files
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## 🎯 Usage Guide

### For Patients

1. **Visit the Home Page**
   - Go to http://127.0.0.1:8000/

2. **Click "Book Appointment Now"**
   - Opens the AI chatbot interface

3. **Chat with the Bot**
   - Describe your symptoms or select a doctor directly
   - AI will suggest the best doctor specialization
   - Choose a doctor from the list
   - Select date and time
   - Provide your details (name, phone, email)
   - Get instant booking confirmation with Booking ID

### For Admin/Staff

1. **Login to Admin Panel**
   - Go to http://127.0.0.1:8000/admin/
   - Use superuser credentials

2. **Manage Doctors**
   - Add new doctors
   - Set specializations
   - Configure weekly schedules
   - Set consultation fees

3. **View Appointments**
   - Dashboard: http://127.0.0.1:8000/admin-panel/
   - Filter by status, doctor, date
   - Update appointment status
   - View patient details

4. **Calendar View**
   - Visual overview of all bookings
   - Click dates to see appointments

## 🔧 Configuration

### Adding Specializations

In Django admin (http://127.0.0.1:8000/admin/):

1. Go to **Specializations**
2. Click **Add Specialization**
3. Fill in:
   - **Name**: e.g., "Orthopedic"
   - **Description**: Brief description
   - **Keywords**: Comma-separated (e.g., "leg pain, bone, fracture, joint, back pain")
4. Save

**Important:** Keywords help the AI match patient symptoms to the right specialization.

### Adding Doctors

1. Go to **Doctors** in admin
2. Click **Add Doctor**
3. Fill in details:
   - Name, email, phone
   - Select specialization
   - Add qualifications, experience
   - Upload photo (optional)
4. Add **Doctor Schedules**:
   - Select days of the week
   - Set start/end times
   - Set slot duration (default 30 minutes)

### Sample Data

Create a file `setup_sample_data.py` in the project root:

```python
from doctors.models import Specialization, Doctor, DoctorSchedule
from datetime import time

# Create specializations
ortho = Specialization.objects.create(
    name="Orthopedic",
    description="Bone and joint specialist",
    keywords="leg pain, bone, fracture, joint, back pain, arthritis"
)

cardio = Specialization.objects.create(
    name="Cardiologist",
    description="Heart specialist",
    keywords="chest pain, heart, blood pressure, palpitations"
)

general = Specialization.objects.create(
    name="General Physician",
    description="General health checkup",
    keywords="fever, cold, flu, general checkup, headache"
)

# Create doctors
dr_smith = Doctor.objects.create(
    name="John Smith",
    specialization=ortho,
    phone="1234567890",
    email="dr.smith@hospital.com",
    qualification="MBBS, MS Orthopedics",
    experience_years=10,
    consultation_fee=500.00
)

# Add schedule (Monday to Friday, 9 AM - 5 PM)
for day in range(5):  # 0-4 = Mon-Fri
    DoctorSchedule.objects.create(
        doctor=dr_smith,
        day_of_week=day,
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration=30
    )

print("Sample data created successfully!")
```

Run with: `python manage.py shell < setup_sample_data.py`

## 🤖 How the AI Works

### Symptom Analysis

When a patient describes symptoms, Claude AI:

1. **Analyzes the text** - Understands medical terminology and common descriptions
2. **Matches keywords** - Compares with specialization keywords in database
3. **Returns suggestion** - Recommends the most appropriate specialization
4. **Provides reasoning** - Explains why this doctor type is recommended

### Conversation Flow

```
1. Greeting → Ask what user needs
2. Symptoms Input → User describes problem
3. AI Analysis → Claude suggests doctor type
4. Doctor Selection → Show available doctors
5. Date Selection → Show next 3 days (configurable)
6. Time Selection → Show only available slots
7. Patient Details → Collect name, phone, email
8. Confirmation → Create booking, return ID
```

## 📊 Database Models

### Specialization
- Name, description, keywords
- Used for AI matching

### Doctor
- Personal details, qualifications
- Linked to specialization
- Can have multiple schedules

### DoctorSchedule
- Day of week (0-6)
- Start/end times
- Slot duration
- Can be activated/deactivated

### Appointment
- Patient details
- Doctor, date, time
- Symptoms, notes
- Status tracking
- Unique booking ID

## 🔐 Security Notes

- Change `SECRET_KEY` in production
- Set `DEBUG = False` in production
- Use HTTPS in production
- Protect API keys (never commit `.env`)
- Add authentication for admin panel
- Implement rate limiting for API

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'anthropic'"
```bash
pip install anthropic
```

### "No such table" errors
```bash
python manage.py makemigrations
python manage.py migrate
```

### Chatbot not responding
1. Check if `ANTHROPIC_API_KEY` is set in `.env`
2. Verify API key is valid
3. Check console for errors
4. Ensure doctors and specializations exist in database

### Static files not loading
```bash
python manage.py collectstatic
```

## 🚀 Deployment (Production)

### Settings for Production

1. **Update `config/settings.py`:**
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['your-domain.com']
   ```

2. **Use PostgreSQL instead of SQLite:**
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'your_db',
           'USER': 'your_user',
           'PASSWORD': 'your_password',
           'HOST': 'localhost',
           'PORT': '5432',
       }
   }
   ```

3. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

4. **Use production server:**
   - Gunicorn, uWSGI, or Daphne
   - Nginx as reverse proxy
   - SSL certificate (Let's Encrypt)

## 📝 API Documentation

### Chatbot API

**Endpoint:** `/api/chatbot/`

**Method:** POST

**Request:**
```json
{
    "message": "I have leg pain",
    "session_id": "session_123456789"
}
```

**Response:**
```json
{
    "success": true,
    "session_id": "session_123456789",
    "message": "Based on your symptoms, I recommend seeing an Orthopedic...",
    "action": "select_doctor",
    "options": [
        {
            "label": "Dr. John Smith",
            "value": "1",
            "description": "Orthopedic - 10 years exp."
        }
    ]
}
```

## 🛠️ Customization

### Change Chat Colors
Edit `templates/patient_booking/chatbot.html`:
```css
background: linear-gradient(135deg, #your-color-1 0%, #your-color-2 100%);
```

### Change Time Slot Duration
In admin, edit Doctor Schedule:
- Default: 30 minutes
- Change to 15, 45, or 60 minutes as needed

### Add More Patient Fields
Edit `appointments/models.py`:
```python
additional_field = models.CharField(max_length=100)
```
Run migrations after changes.

## 📞 Support

For issues or questions:
1. Check this README
2. Review Django documentation
3. Check Claude API documentation
4. Review error logs in console

## 📄 License

This project is created for educational and commercial purposes.

## 🙏 Credits

- **Django** - Web framework
- **Claude AI by Anthropic** - Conversational AI
- **Bootstrap Icons** - UI icons (optional)

---

**Enjoy building your medical appointment system! 🏥🤖**
