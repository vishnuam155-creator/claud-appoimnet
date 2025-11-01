# 🚀 QUICK START GUIDE - Medical Appointment System

## ⚡ Get Started in 5 Minutes!

### Step 1: Extract & Setup (2 minutes)
```bash
# Extract the ZIP file
unzip appointment_system.zip
cd appointment_system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Key (1 minute)
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Claude API key
# Get it from: https://console.anthropic.com/
```

**.env file:**
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 3: Database Setup (1 minute)
```bash
# Create database tables
python manage.py migrate

# Create admin account
python manage.py createsuperuser
# Enter: username, email, password

# Load sample data (optional but recommended)
python manage.py shell < setup_sample_data.py
```

### Step 4: Run Server (30 seconds)
```bash
python manage.py runserver
```

### Step 5: Test It! (30 seconds)
Open your browser:

1. **Patient Chatbot**: http://127.0.0.1:8000/chatbot/
   - Try: "I have leg pain"
   - Try: "I need a checkup"

2. **Admin Panel**: http://127.0.0.1:8000/admin/
   - Login with superuser credentials
   - View appointments, manage doctors

3. **Home Page**: http://127.0.0.1:8000/

---

## 🎯 What You Get

### ✅ Patient Side
- AI Chatbot that understands symptoms
- Automatic doctor suggestions
- Real-time availability checking
- Instant booking confirmation

### ✅ Admin Side
- Complete appointment dashboard
- Doctor management system
- Calendar view
- Status tracking

---

## 📋 Sample Data Included

After running `setup_sample_data.py`, you'll have:

- **5 Specializations**: Orthopedic, Cardiologist, General Physician, Dermatologist, Neurologist
- **5 Doctors**: Each with schedules and experience
- **Ready to test**: Just open the chatbot and start booking!

---

## 💡 Test Scenarios

### Scenario 1: Patient with Leg Pain
1. Open chatbot
2. Type: "I have pain in my leg"
3. AI suggests: Orthopedic
4. Select: Dr. John Smith
5. Choose date and time
6. Enter details
7. Get booking confirmation

### Scenario 2: General Checkup
1. Type: "I need a routine checkup"
2. AI suggests: General Physician
3. Continue booking process

### Scenario 3: Admin Management
1. Login to admin
2. View today's appointments
3. Update appointment status
4. Check calendar view

---

## 🔧 Common Commands

```bash
# Create migrations after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run on different port
python manage.py runserver 8080

# Access from other devices on network
python manage.py runserver 0.0.0.0:8000
```

---

## 🐛 Troubleshooting

### Issue: API Key Error
**Solution**: Make sure you've:
1. Created `.env` file from `.env.example`
2. Added valid Claude API key
3. No spaces around the `=` sign

### Issue: No module named 'anthropic'
**Solution**: 
```bash
pip install anthropic
```

### Issue: No doctors showing in chatbot
**Solution**: 
```bash
python manage.py shell < setup_sample_data.py
```

### Issue: Port already in use
**Solution**: Use a different port
```bash
python manage.py runserver 8080
```

---

## 📱 Access URLs

- **Home**: http://127.0.0.1:8000/
- **Chatbot**: http://127.0.0.1:8000/chatbot/
- **Django Admin**: http://127.0.0.1:8000/admin/
- **Custom Dashboard**: http://127.0.0.1:8000/admin-panel/

---

## 🎨 Customize It!

### Change Chatbot Colors
Edit: `templates/patient_booking/chatbot.html`
Look for: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`

### Add More Specializations
Django Admin → Specializations → Add New

### Modify Appointment Duration
Django Admin → Doctor Schedules → Change slot_duration

---

## 📚 Full Documentation

See `README.md` for:
- Detailed architecture
- API documentation
- Deployment guide
- Advanced configuration

---

## 🆘 Need Help?

1. Check `README.md`
2. Review error messages in terminal
3. Check Django logs
4. Verify all dependencies installed

---

**You're all set! Start booking appointments with AI! 🏥🤖**
