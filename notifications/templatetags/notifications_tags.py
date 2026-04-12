from django import template
from notifications.calendar_service import generate_google_calendar_link

register = template.Library()


@register.filter
def gcal_link(event):
    """Retourne le lien Google Calendar pour un événement."""
    return generate_google_calendar_link(event)


@register.simple_tag
def google_calendar_link(event):
    """Tag simple pour le lien Google Calendar."""
    return generate_google_calendar_link(event)
