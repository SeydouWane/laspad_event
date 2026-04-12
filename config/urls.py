"""LASPAD Event - URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('events.urls', namespace='events')),
    path('inscription/', include('registrations.urls', namespace='registrations')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personnalisation admin
admin.site.site_header = 'LASPAD Event — Administration'
admin.site.site_title = 'LASPAD Event'
admin.site.index_title = 'Gestion de la plateforme'
