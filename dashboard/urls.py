from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('login/', views.dashboard_login, name='login'),
    path('logout/', views.dashboard_logout, name='logout'),
    path('', views.dashboard_home, name='home'),
    path('stats/', views.stats, name='stats'),

    # ── Événements ──
    path('evenements/', views.event_list, name='event_list'),
    path('evenements/creer/', views.event_create, name='event_create'),
    path('evenements/<uuid:pk>/', views.event_detail, name='event_detail'),
    path('evenements/<uuid:pk>/modifier/', views.event_edit, name='event_edit'),
    path('evenements/<uuid:pk>/export-csv/', views.export_registrations_csv, name='export_csv'),
    path('evenements/<uuid:pk>/contacter/', views.contact_participants, name='contact_participants'),

    # ── Inscriptions ──
    path('inscriptions/<uuid:pk>/accepter/', views.registration_accept, name='registration_accept'),
    path('inscriptions/<uuid:pk>/refuser/', views.registration_refuse, name='registration_refuse'),

    # ── Participants publics ──
    path('participants/', views.participants_list, name='participants_list'),
    path('participants/<uuid:pk>/contacter/', views.contact_one_participant, name='contact_participant'),

    # ── Intervenants ──
    path('intervenants/', views.organizer_list, name='organizer_list'),
    path('intervenants/ajouter/', views.organizer_create, name='organizer_create'),
    path('intervenants/<int:pk>/modifier/', views.organizer_edit, name='organizer_edit'),
    path('intervenants/<int:pk>/supprimer/', views.organizer_delete, name='organizer_delete'),

    # ── Utilisateurs ──
    path('utilisateurs/', views.user_list, name='user_list'),
    path('utilisateurs/inviter/', views.user_invite, name='user_invite'),
    path('utilisateurs/<int:pk>/modifier/', views.user_edit, name='user_edit'),
    path('utilisateurs/<int:pk>/suspendre/', views.user_suspend, name='user_suspend'),
    path('utilisateurs/<int:pk>/reactiver/', views.user_activate, name='user_activate'),
    path('utilisateurs/<int:pk>/supprimer/', views.user_delete, name='user_delete'),
    path('inscriptions/<uuid:pk>/accepter-masse/', views.registration_accept_bulk, name='registration_accept_bulk'),
    path('inscriptions/<uuid:pk>/refuser-masse/',  views.registration_refuse_bulk,  name='registration_refuse_bulk'),
    path('inscriptions/<uuid:pk>/ticket/', views.resend_ticket, name='resend_ticket'),
    path('evenements/<uuid:pk>/chronogramme/', views.schedule_manage, name='schedule_manage'),
    path('scan/', views.scan_home, name='scan_home'),
    path('scan/<uuid:token>/', views.scan_ticket, name='scan_ticket'),
    path('scan/lookup/', views.scan_lookup, name='scan_lookup'),
    path('evenements/<uuid:pk>/export-presences/', views.export_presence_csv, name='export_presence_csv'),
]