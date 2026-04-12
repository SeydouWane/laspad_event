from django.contrib import admin
from django.utils.html import format_html
from .models import Participant, Registration


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'institution', 'role', 'newsletter', 'created_at']
    list_filter  = ['newsletter']
    search_fields = ['first_name', 'last_name', 'email', 'institution']
    readonly_fields = ['id', 'created_at']


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['participant', 'event', 'status_badge', 'registered_at', 'calendar_invite_sent']
    list_filter = ['status', 'event', 'calendar_invite_sent']
    search_fields = ['participant__email', 'participant__first_name', 'participant__last_name']
    readonly_fields = ['id', 'token', 'registered_at', 'validated_at']
    actions = ['accept_registrations', 'refuse_registrations']

    def status_badge(self, obj):
        colors = {
            'en_attente': '#f59e0b',
            'accepte': '#10b981',
            'refuse': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:4px;font-size:12px">{}</span>',
            color,
            obj.get_status_display(),
        )
    status_badge.short_description = 'Statut'

    def accept_registrations(self, request, queryset):
        for reg in queryset.filter(status=Registration.STATUS_PENDING):
            reg.accept()
        self.message_user(request, f"{queryset.count()} inscription(s) acceptée(s).")
    accept_registrations.short_description = "Accepter les inscriptions sélectionnées"

    def refuse_registrations(self, request, queryset):
        for reg in queryset.filter(status=Registration.STATUS_PENDING):
            reg.refuse()
        self.message_user(request, f"{queryset.count()} inscription(s) refusée(s).")
    refuse_registrations.short_description = "Refuser les inscriptions sélectionnées"
