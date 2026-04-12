"""
Service d'intégration Google Calendar API.

Option A (simple) : génère un lien "Ajouter à Google Calendar"
Option B (avancée) : insère directement via l'API Google Calendar

Documentation API utilisée :
  POST /calendars/calendarId/events  → crée un événement
  GET  /calendars/calendarId/events  → liste les événements
"""

from django.conf import settings
from urllib.parse import urlencode
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ─── OPTION A : Lien public "Ajouter à Google Calendar" ─────────────────────

def generate_google_calendar_link(event):
    """
    Génère un lien direct vers Google Calendar pour ajouter l'événement.
    Fonctionne sans authentification — méthode universelle.
    """
    def fmt(dt):
        return dt.strftime('%Y%m%dT%H%M%SZ')

    details = event.description
    if event.location and event.location.online_link:
        details += f"\n\nLien : {event.location.online_link}"

    location = ''
    if event.location:
        if event.location.mode == 'online':
            location = event.location.online_link or ''
        else:
            location = f"{event.location.address}, {event.location.city}, {event.location.country}"

    params = {
        'action': 'TEMPLATE',
        'text': event.title,
        'dates': f"{fmt(event.start_datetime)}/{fmt(event.end_datetime)}",
        'details': details,
        'location': location,
    }
    return f"https://calendar.google.com/calendar/render?{urlencode(params)}"


# ─── OPTION B : Insertion via Google Calendar API ───────────────────────────

def get_google_credentials(user):
    """
    Récupère les credentials OAuth2 de l'utilisateur depuis la session/DB.
    À implémenter selon votre flux OAuth.
    """
    from google.oauth2.credentials import Credentials
    # TODO: charger token stocké pour cet utilisateur
    # Exemple : token = UserGoogleToken.objects.get(user=user)
    # return Credentials(token=token.access_token, refresh_token=token.refresh_token, ...)
    raise NotImplementedError("Implémenter le stockage OAuth2 de l'utilisateur.")


def build_calendar_service(credentials):
    """Construit le service Google Calendar API."""
    from googleapiclient.discovery import build
    return build('calendar', 'v3', credentials=credentials)


def create_calendar_event(service, event, participant_email=None):
    """
    Crée un événement dans Google Calendar via l'API.
    Utilise POST /calendars/primary/events
    """
    attendees = []
    if participant_email:
        attendees.append({'email': participant_email})

    location = ''
    if event.location:
        if event.location.mode == 'online':
            location = event.location.online_link or ''
        else:
            location = f"{event.location.address}, {event.location.city}"

    description = event.description
    if event.location and event.location.online_link:
        description += f"\n\n🔗 Lien de connexion : {event.location.online_link}"

    body = {
        'summary': event.title,
        'description': description,
        'location': location,
        'start': {
            'dateTime': event.start_datetime.isoformat(),
            'timeZone': 'Africa/Dakar',
        },
        'end': {
            'dateTime': event.end_datetime.isoformat(),
            'timeZone': 'Africa/Dakar',
        },
        'attendees': attendees,
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 24 * 60},
                {'method': 'popup', 'minutes': 60},
            ],
        },
        'conferenceData': {
            'entryPoints': [{
                'entryPointType': 'video',
                'uri': event.location.online_link,
                'label': 'Rejoindre la réunion',
            }] if event.location and event.location.online_link else [],
        } if event.location and event.location.online_link else {},
    }

    result = service.events().insert(
        calendarId='primary',
        body=body,
        sendUpdates='all',
    ).execute()
    return result.get('id')


def add_to_google_calendar(registration):
    """
    Point d'entrée principal : tente d'ajouter via l'API.
    Si non configuré, génère seulement le lien Option A.
    """
    event = registration.event
    participant = registration.participant

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        logger.info("Google Calendar API non configurée, lien généré uniquement.")
        link = generate_google_calendar_link(event)
        logger.info(f"Lien GCal : {link}")
        return {'link': link, 'method': 'link'}

    try:
        credentials = get_google_credentials(registration.event.organizer)
        service = build_calendar_service(credentials)
        event_id = create_calendar_event(service, event, participant.email)

        registration.calendar_invite_sent = True
        registration.save(update_fields=['calendar_invite_sent'])
        logger.info(f"Événement ajouté au calendar de {participant.email}, id={event_id}")
        return {'event_id': event_id, 'method': 'api'}
    except NotImplementedError:
        link = generate_google_calendar_link(event)
        return {'link': link, 'method': 'link'}
    except Exception as e:
        logger.error(f"Erreur Google Calendar API: {e}")
        raise
