# Quick Fix for Template Error

## Error: `TemplateDoesNotExist at / patient_booking/home.html`

This error means Django cannot find your templates. Here's how to fix it:

## Solution 1: Verify Templates Exist (Most Common Issue)

Run the verification script from your project directory:

```bash
# Navigate to your project directory
cd /path/to/claud-appoimnet

# Run verification script
python verify_setup.py
```

## Solution 2: Ensure Correct Django Version

Your error shows Django 5.2.8 but this project uses Django 4.2.7:

```bash
# Uninstall current Django
pip uninstall django

# Install correct version
pip install Django==4.2.7

# Or install all requirements
pip install -r requirements.txt
```

## Solution 3: Manual Template Check

Check if templates exist in your project:

```bash
# From project root
ls -la templates/patient_booking/

# You should see:
# - home.html
# - chatbot.html
# - voice_assistant.html
```

If templates are missing, you didn't copy them from the repository. Re-clone or copy the entire project.

## Solution 4: Verify Django Settings

Check `config/settings.py` has correct TEMPLATES configuration:

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # This line is important
        'APP_DIRS': True,
        # ...
    },
]
```

## Solution 5: Restart Django Server

Sometimes Django needs a restart after code changes:

```bash
# Stop the server (Ctrl+C)
# Then start again
python manage.py runserver
```

## Complete Setup (If Nothing Works)

Start fresh:

```bash
# 1. Navigate to project
cd /path/to/claud-appoimnet

# 2. Create virtual environment (if not exists)
python -m venv venv

# 3. Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run migrations
python manage.py migrate

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Start server
python manage.py runserver
```

## Test Your Setup

After fixing, test these URLs:

1. **Home Page**: http://127.0.0.1:8000/
2. **Chatbot**: http://127.0.0.1:8000/chatbot/
3. **Voice Assistant**: http://127.0.0.1:8000/voice-assistant/
4. **REST API**: http://127.0.0.1:8000/api/v1/
5. **Admin**: http://127.0.0.1:8000/admin/

## Still Having Issues?

Check your project structure looks like this:

```
claud-appoimnet/
├── config/
│   ├── settings.py
│   └── urls.py
├── templates/
│   ├── patient_booking/
│   │   ├── home.html          ← Must exist
│   │   ├── chatbot.html       ← Must exist
│   │   └── voice_assistant.html ← Must exist
│   └── admin_panel/
├── patient_booking/
│   ├── views.py
│   ├── urls.py
│   └── api_views.py
├── manage.py                   ← Must exist
└── requirements.txt            ← Must exist
```

## Common Mistakes

1. ❌ Running from wrong directory
   - ✅ Must run `python manage.py runserver` from project root

2. ❌ Templates not copied from repository
   - ✅ Ensure you have the complete project files

3. ❌ Wrong Django version installed
   - ✅ Use Django 4.2.7 as specified in requirements.txt

4. ❌ Virtual environment not activated
   - ✅ Always activate venv before running Django

5. ❌ Missing dependencies
   - ✅ Run `pip install -r requirements.txt`

## Quick Command Reference

```bash
# Check if templates exist
ls templates/patient_booking/

# Check Django version
python -c "import django; print(django.get_version())"

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Run verification script
python verify_setup.py

# Restart server
# Press Ctrl+C, then:
python manage.py runserver

# Check for errors
python manage.py check

# Run migrations
python manage.py migrate
```

## Need More Help?

If none of these work:

1. Ensure you have the COMPLETE project from git repository
2. Check that you're in the correct directory
3. Verify Python version (should be 3.8+)
4. Make sure virtual environment is activated
5. Try creating a fresh virtual environment

The most common issue is that the templates folder was not copied from the repository or you're running from the wrong directory!
