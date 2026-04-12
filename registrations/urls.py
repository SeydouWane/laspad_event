from django.urls import path
from . import views

app_name = 'registrations'

urlpatterns = [
    path('<slug:slug>/', views.register, name='register'),
    path('succes/<uuid:token>/', views.registration_success, name='success'),
    path('confirmer/<uuid:token>/', views.registration_confirm, name='confirm'),
]
