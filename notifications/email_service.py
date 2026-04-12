# -*- coding: utf-8 -*-
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


def send_email(subject, template_name, context, recipient_email, attachments=None):
    """
    Envoie un email HTML avec fallback texte.
    attachments : liste de tuples (filename, content_bytes, mimetype)
    """
    html_content = render_to_string(f'emails/{template_name}.html', context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[recipient_email],
    )
    email.attach_alternative(html_content, 'text/html')

    if attachments:
        for filename, content, mimetype in attachments:
            email.attach(filename, content, mimetype)

    email.send(fail_silently=False)
    return True


def send_registration_confirmation(registration):
    """Email de confirmation + ticket PDF si présentiel."""
    context = {
        'registration': registration,
        'event':        registration.event,
        'participant':  registration.participant,
        'site_url':     settings.SITE_URL,
        'site_name':    settings.SITE_NAME,
    }

    attachments = []

    # Générer et joindre le ticket PDF si présentiel
    if registration.needs_ticket:
        try:
            from notifications.ticket_service import generate_ticket_pdf, save_ticket_pdf

            # Sauvegarder le PDF
            save_ticket_pdf(registration)

            # Lire le PDF pour la pièce jointe
            pdf_bytes = generate_ticket_pdf(registration)
            ticket_name = f"ticket_laspad_{registration.ticket_number or registration.token}.pdf"
            attachments.append((ticket_name, pdf_bytes, 'application/pdf'))

            # Marquer comme envoyé
            registration.ticket_sent = True
            registration.save(update_fields=['ticket_sent'])

        except Exception as e:
            logger.warning(f"Impossible de générer le ticket PDF : {e}")

    return send_email(
        subject=f"[LASPAD Event] Confirmation — {registration.event.title}",
        template_name='confirmation',
        context=context,
        recipient_email=registration.participant.email,
        attachments=attachments,
    )


def send_registration_pending(registration):
    """Email d'accusé de réception pour les inscriptions en attente."""
    context = {
        'registration': registration,
        'event':        registration.event,
        'participant':  registration.participant,
        'site_url':     settings.SITE_URL,
        'site_name':    settings.SITE_NAME,
    }
    return send_email(
        subject=f"[LASPAD Event] Inscription reçue — {registration.event.title}",
        template_name='pending',
        context=context,
        recipient_email=registration.participant.email,
    )


def send_registration_refused(registration):
    """Email de refus d'inscription."""
    context = {
        'registration': registration,
        'event':        registration.event,
        'participant':  registration.participant,
        'site_url':     settings.SITE_URL,
        'site_name':    settings.SITE_NAME,
    }
    return send_email(
        subject=f"[LASPAD Event] Inscription — {registration.event.title}",
        template_name='refused',
        context=context,
        recipient_email=registration.participant.email,
    )


def send_event_reminder(registration):
    """Email de rappel avant l'événement."""
    context = {
        'registration': registration,
        'event':        registration.event,
        'participant':  registration.participant,
        'site_url':     settings.SITE_URL,
        'site_name':    settings.SITE_NAME,
    }
    return send_email(
        subject=f"[LASPAD Event] Rappel — {registration.event.title}",
        template_name='reminder',
        context=context,
        recipient_email=registration.participant.email,
    )


def send_event_cancelled(registration):
    """Email d'annulation d'événement."""
    context = {
        'registration': registration,
        'event':        registration.event,
        'participant':  registration.participant,
        'site_url':     settings.SITE_URL,
        'site_name':    settings.SITE_NAME,
    }
    return send_email(
        subject=f"[LASPAD Event] Annulation — {registration.event.title}",
        template_name='cancelled',
        context=context,
        recipient_email=registration.participant.email,
    )


def resend_ticket(registration):
    """
    Renvoyer le ticket PDF à un participant (depuis le dashboard).
    Utilisé pour les renvois manuels.
    """
    if not registration.needs_ticket:
        return False

    try:
        from notifications.ticket_service import generate_ticket_pdf, save_ticket_pdf

        if not registration.ticket_pdf:
            save_ticket_pdf(registration)

        pdf_bytes   = generate_ticket_pdf(registration)
        ticket_name = f"ticket_laspad_{registration.ticket_number or registration.token}.pdf"

        context = {
            'registration': registration,
            'event':        registration.event,
            'participant':  registration.participant,
            'site_url':     settings.SITE_URL,
            'site_name':    settings.SITE_NAME,
            'is_resend':    True,
        }

        result = send_email(
            subject=f"[LASPAD Event] Votre ticket — {registration.event.title}",
            template_name='confirmation',
            context=context,
            recipient_email=registration.participant.email,
            attachments=[(ticket_name, pdf_bytes, 'application/pdf')],
        )

        registration.ticket_sent = True
        registration.save(update_fields=['ticket_sent'])
        return result

    except Exception as e:
        logger.error(f"Erreur renvoi ticket : {e}")
        return False