from django.contrib import admin
from .models import Event, Location, Organizer


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['mode', 'platform', 'city', 'country']
    list_filter = ['mode', 'platform']


@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
    list_display = ['user', 'institution', 'phone']
    search_fields = ['user__first_name', 'user__last_name', 'institution']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'status', 'start_datetime', 'access_mode', 'accepted_registrations']
    list_filter = ['status', 'event_type', 'access_mode']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'google_calendar_event_id']
    filter_horizontal = ['speakers']
    date_hierarchy = 'start_datetime'
