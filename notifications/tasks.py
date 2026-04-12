from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_confirmation_email(self, registration_id):
    """Envoie l'email de confirmation d'inscription."""
    try:
        from registrations.models import Registration
        from notifications.email_service import send_registration_confirmation
        from notifications.calendar_service import add_to_google_calendar

        registration = Registration.objects.select_related('event', 'participant').get(id=registration_id)

        send_registration_confirmation(registration)
        registration.confirmation_sent = True
        registration.save(update_fields=['confirmation_sent'])

        # Tenter d'ajouter au Google Calendar
        try:
            add_to_google_calendar(registration)
        except Exception as e:
            logger.warning(f"Impossible d'ajouter au Google Calendar: {e}")

        logger.info(f"Email de confirmation envoyé à {registration.participant.email}")
    except Exception as exc:
        logger.error(f"Erreur envoi confirmation: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_pending_email(self, registration_id):
    """Envoie l'email d'accusé de réception pour inscription en attente."""
    try:
        from registrations.models import Registration
        from notifications.email_service import send_registration_pending

        registration = Registration.objects.select_related('event', 'participant').get(id=registration_id)
        send_registration_pending(registration)
        logger.info(f"Email 'en attente' envoyé à {registration.participant.email}")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def send_refused_email(self, registration_id):
    """Envoie l'email de refus."""
    try:
        from registrations.models import Registration
        from notifications.email_service import send_registration_refused

        registration = Registration.objects.select_related('event', 'participant').get(id=registration_id)
        send_registration_refused(registration)
        logger.info(f"Email de refus envoyé à {registration.participant.email}")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@shared_task
def send_event_reminders():
    """Tâche périodique : envoie les rappels 24h et 1h avant l'événement."""
    from registrations.models import Registration
    from notifications.email_service import send_event_reminder

    now = timezone.now()

    # Rappel 24h avant
    window_24h_start = now + timedelta(hours=23, minutes=30)
    window_24h_end = now + timedelta(hours=24, minutes=30)

    # Rappel 1h avant
    window_1h_start = now + timedelta(minutes=30)
    window_1h_end = now + timedelta(hours=1, minutes=30)

    registrations_to_remind = Registration.objects.filter(
        status=Registration.STATUS_ACCEPTED,
        event__start_datetime__range=(window_24h_start, window_24h_end),
    ) | Registration.objects.filter(
        status=Registration.STATUS_ACCEPTED,
        event__start_datetime__range=(window_1h_start, window_1h_end),
    )

    for reg in registrations_to_remind:
        try:
            send_event_reminder(reg)
            logger.info(f"Rappel envoyé à {reg.participant.email} pour {reg.event.title}")
        except Exception as e:
            logger.error(f"Erreur rappel pour {reg.id}: {e}")
