# Deployment Guide

Complete guide for deploying the Medical Appointment System with REST API and React frontend.

## Overview

The system consists of:
1. **Django Backend** - REST API with Django REST Framework
2. **React Frontend** - Modern SPA built with React and Material-UI
3. **Database** - SQLite (development) / PostgreSQL (production)
4. **Optional Services** - Twilio SMS, Google AI

## Prerequisites

### Backend Requirements
- Python 3.8+
- pip
- Virtual environment (recommended)

### Frontend Requirements
- Node.js 16+
- npm or yarn

### Production Requirements
- PostgreSQL database
- Nginx (recommended)
- Gunicorn or uWSGI
- SSL certificate (Let's Encrypt)

## Development Setup

### 1. Backend Setup

```bash
# Clone repository
git clone <repository-url>
cd claud-appoimnet

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install django-filter  # Additional dependency

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Load sample data (optional)
python setup_sample_data.py

# Run development server
python manage.py runserver
```

Backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create environment file
echo "REACT_APP_API_URL=http://localhost:8000/api/v1" > .env

# Start development server
npm start
```

Frontend will be available at `http://localhost:3000`

## Production Deployment

### Option 1: Single Server Deployment (Django + React)

This is the recommended approach for small to medium deployments.

#### Step 1: Prepare Django Backend

```bash
# Update settings for production
vim config/settings.py
```

**Production Settings:**
```python
DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Use PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'appointment_db',
        'USER': 'db_user',
        'PASSWORD': 'secure_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Static and Media files
STATIC_ROOT = '/var/www/your-domain/static/'
MEDIA_ROOT = '/var/www/your-domain/media/'
```

#### Step 2: Build React Frontend

```bash
cd frontend
npm run build
```

#### Step 3: Copy React Build to Django

```bash
# Create directory for frontend
mkdir -p /var/www/your-domain/static/frontend

# Copy build files
cp -r frontend/build/* /var/www/your-domain/static/frontend/

# Or integrate directly
python manage.py collectstatic --noinput
```

#### Step 4: Configure Django URL for React

**config/urls.py:**
```python
from django.views.generic import TemplateView
from django.urls import path, include, re_path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    # ... other API paths ...

    # Serve React app for all other routes
    re_path(r'^.*', TemplateView.as_view(template_name='frontend/index.html')),
]
```

#### Step 5: Setup Gunicorn

```bash
pip install gunicorn

# Create Gunicorn service file
sudo vim /etc/systemd/system/appointment-backend.service
```

**/etc/systemd/system/appointment-backend.service:**
```ini
[Unit]
Description=Medical Appointment System
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/your-domain
Environment="PATH=/var/www/your-domain/venv/bin"
ExecStart=/var/www/your-domain/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 config.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
# Start and enable service
sudo systemctl start appointment-backend
sudo systemctl enable appointment-backend
```

#### Step 6: Configure Nginx

```bash
sudo vim /etc/nginx/sites-available/appointment-system
```

**/etc/nginx/sites-available/appointment-system:**
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Frontend (React)
    location / {
        root /var/www/your-domain/static/frontend;
        try_files $uri $uri/ /index.html;
    }

    # API endpoints
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Static files
    location /static/ {
        alias /var/www/your-domain/static/;
    }

    # Media files
    location /media/ {
        alias /var/www/your-domain/media/;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/appointment-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 7: Setup SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

### Option 2: Separate Frontend Hosting

Deploy React app to Netlify, Vercel, or AWS S3.

#### Build Frontend

```bash
cd frontend
npm run build
```

#### Deploy to Netlify

```bash
npm install -g netlify-cli
netlify deploy --prod --dir=build
```

Set environment variable:
```
REACT_APP_API_URL=https://api.your-domain.com/api/v1
```

#### Configure CORS on Backend

**config/settings.py:**
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend.netlify.app",
    "https://www.your-domain.com",
]
```

## Database Migration

### Backup Current Database

```bash
python manage.py dumpdata > backup.json
```

### PostgreSQL Setup

```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql

CREATE DATABASE appointment_db;
CREATE USER db_user WITH PASSWORD 'secure_password';
ALTER ROLE db_user SET client_encoding TO 'utf8';
ALTER ROLE db_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE db_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE appointment_db TO db_user;
\q

# Install Python PostgreSQL adapter
pip install psycopg2-binary

# Update settings.py with PostgreSQL config
# Run migrations
python manage.py migrate

# Load backup data
python manage.py loaddata backup.json
```

## Environment Variables

Create `.env` file in project root:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
DB_NAME=appointment_db
DB_USER=db_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432

# AI Services
ANTHROPIC_API_KEY=your-claude-api-key
GOOGLE_AI_API_KEY=your-gemini-api-key

# Twilio SMS
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# Optional
USE_GOOGLE_CLOUD_SPEECH=False
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

## Post-Deployment Checklist

- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Media directory permissions set
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Backup system in place
- [ ] Monitoring setup
- [ ] Environment variables secured
- [ ] Django DEBUG=False
- [ ] ALLOWED_HOSTS configured
- [ ] CORS settings updated
- [ ] SMS service tested
- [ ] Email notifications working
- [ ] Log rotation configured

## Monitoring

### Setup Logs

```bash
# Django logs
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/appointment-system/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

### Monitor Services

```bash
# Check status
sudo systemctl status appointment-backend
sudo systemctl status nginx

# View logs
sudo journalctl -u appointment-backend -f
sudo tail -f /var/log/nginx/error.log
```

## Backup Strategy

### Automated Database Backup

```bash
#!/bin/bash
# /usr/local/bin/backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/appointment-system"
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump -U db_user appointment_db > $BACKUP_DIR/db_$DATE.sql

# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz /var/www/your-domain/media/

# Keep only last 7 days
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "media_*.tar.gz" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /usr/local/bin/backup-db.sh
```

## Troubleshooting

### Static Files Not Loading

```bash
python manage.py collectstatic --noinput
sudo systemctl restart appointment-backend
sudo systemctl reload nginx
```

### Database Connection Error

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -U db_user -d appointment_db -h localhost
```

### CORS Errors

Ensure backend CORS settings include frontend domain:
```python
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
]
```

### 502 Bad Gateway

```bash
# Check if Gunicorn is running
sudo systemctl status appointment-backend

# Check Gunicorn logs
sudo journalctl -u appointment-backend -n 50
```

## Security Best Practices

1. **Never commit `.env` file**
2. **Use strong SECRET_KEY**
3. **Keep dependencies updated**
4. **Enable HTTPS only**
5. **Implement rate limiting**
6. **Regular security audits**
7. **Monitor error logs**
8. **Use environment variables**
9. **Restrict database access**
10. **Regular backups**

## Performance Optimization

### Django

```python
# settings.py

# Enable caching
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Database optimization
CONN_MAX_AGE = 600
```

### Nginx

```nginx
# Enable gzip
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript;

# Browser caching
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## Support

For issues and questions:
- Check API documentation: `API_DOCUMENTATION.md`
- Check React README: `frontend/README.md`
- View system logs
- Contact support team
