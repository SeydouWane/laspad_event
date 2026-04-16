"""LASPAD Event - URL Configuration"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('events.urls', namespace='events')),
    path('inscription/', include('registrations.urls', namespace='registrations')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('dashboard/password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='dashboard/password_reset.html',
             email_template_name='emails/password_reset.html',
             subject_template_name='emails/password_reset_subject.txt',
             success_url='/dashboard/password-reset/done/',
         ),
         name='password_reset'),
    path('dashboard/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='dashboard/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('dashboard/password-reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='dashboard/password_reset_confirm.html',
             success_url='/dashboard/password-reset/complete/',
         ),
         name='password_reset_confirm'),
    path('dashboard/password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='dashboard/password_reset_complete.html',
         ),
         name='password_reset_complete'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Personnalisation admin
admin.site.site_header = 'LASPAD Event — Administration'
admin.site.site_title = 'LASPAD Event'
admin.site.index_title = 'Gestion de la plateforme'
