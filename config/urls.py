from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .api_docs_views import api_documentation, api_health_check

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # API Documentation
    path('api/docs/', api_documentation, name='api_docs'),
    path('api/health/', api_health_check, name='api_health'),

    # App APIs
    path('', include('patient_booking.urls')),
    path('voicebot/', include('voicebot.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('whatsapp/', include('whatsapp_integration.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Admin site customization
admin.site.site_header = "Medical Appointment System"
admin.site.site_title = "Appointment Admin"
admin.site.index_title = "Welcome to Appointment Management"
