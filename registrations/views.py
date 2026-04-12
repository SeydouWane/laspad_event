from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from events.models import Event
from .models import Participant, Registration
from .forms import RegistrationForm
import logging

logger = logging.getLogger(__name__)


def register(request, slug):
    """Formulaire d'inscription à un événement (gestion hybride)."""
    event = get_object_or_404(Event, slug=slug, status=Event.STATUS_PUBLISHED)

    if not event.is_upcoming:
        messages.warning(request, "Les inscriptions pour cet événement sont closes.")
        return redirect('events:detail', slug=slug)

    # Vérifier si l'événement est complet (tous modes)
    mode = getattr(event, 'participation_mode', 'online_only')
    if mode == 'onsite_only' and event.is_full_onsite:
        messages.error(request, "Désolé, cet événement est complet.")
        return redirect('events:detail', slug=slug)
    if mode == 'online_only' and event.is_full_online:
        messages.error(request, "Désolé, cet événement est complet.")
        return redirect('events:detail', slug=slug)
    if mode == 'hybrid' and event.is_full_onsite and event.is_full_online:
        messages.error(request, "Désolé, cet événement est complet (présentiel et en ligne).")
        return redirect('events:detail', slug=slug)

    if request.method == 'POST':
        form = RegistrationForm(request.POST, event=event)
        if form.is_valid():
            data              = form.cleaned_data
            participation_type = data['participation_type']

            # ── Créer ou mettre à jour le participant ──
            participant, _ = Participant.objects.get_or_create(
                email=data['email'],
                defaults={
                    'first_name':  data['first_name'],
                    'last_name':   data['last_name'],
                    'institution': data['institution'],
                    'role':        data['role'],
                    'phone':       data.get('phone', ''),
                },
            )
            participant.first_name  = data['first_name']
            participant.last_name   = data['last_name']
            participant.institution = data['institution']
            participant.role        = data['role']
            if data.get('phone'):
                participant.phone = data['phone']
            if request.POST.get('newsletter') == 'on':
                participant.newsletter = True
            participant.save()

            # ── Vérifier si déjà inscrit ──
            existing = Registration.objects.filter(event=event, participant=participant).first()
            if existing:
                messages.warning(request, "Vous êtes déjà inscrit(e) à cet événement.")
                return redirect('events:detail', slug=slug)

            # ── Déterminer le statut selon le mode de participation ──
            status = _determine_status(event, participation_type)

            # ── Créer l'inscription ──
            registration = Registration.objects.create(
                event              = event,
                participant        = participant,
                status             = status,
                participation_type = participation_type,
                motivation         = data.get('motivation', ''),
            )

            # ── Auto-accept si seuil atteint ──
            _check_auto_accept(event, registration)

            # ── Envoyer emails ──
            registration.refresh_from_db()
            _send_emails(registration)

            return redirect('registrations:success', token=registration.token)

    else:
        form = RegistrationForm(event=event, initial={'newsletter': True})

    return render(request, 'registrations/register.html', {
        'event': event,
        'form':  form,
        'participation_mode': getattr(event, 'participation_mode', 'online_only'),
    })


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def _determine_status(event, participation_type):
    """Détermine le statut initial selon le mode d'accès configuré."""
    mode = getattr(event, 'participation_mode', 'online_only')

    if mode == 'onsite_only':
        access = getattr(event, 'access_onsite', event.access_mode)
    elif mode == 'online_only':
        access = getattr(event, 'access_online', event.access_mode)
    else:  # hybrid
        if participation_type == Registration.PARTICIPATION_ONSITE:
            access = getattr(event, 'access_onsite', 'direct')
        elif participation_type == Registration.PARTICIPATION_ONLINE:
            access = getattr(event, 'access_online', 'direct')
        else:  # both — le plus restrictif l'emporte
            access_onsite = getattr(event, 'access_onsite', 'direct')
            access_online = getattr(event, 'access_online', 'direct')
            access = 'validation' if 'validation' in [access_onsite, access_online] else 'direct'

    return (
        Registration.STATUS_ACCEPTED
        if access == Event.ACCESS_DIRECT
        else Registration.STATUS_PENDING
    )


def _check_auto_accept(event, registration):
    """
    Si auto_accept est configuré et que le seuil n'est pas encore atteint,
    accepte automatiquement les N premiers.
    """
    if registration.status == Registration.STATUS_ACCEPTED:
        return  # déjà accepté

    ptype = registration.participation_type
    mode  = getattr(event, 'participation_mode', 'online_only')

    auto_onsite = getattr(event, 'auto_accept_onsite', None)
    auto_online = getattr(event, 'auto_accept_online', None)

    should_accept = False

    if ptype in [Registration.PARTICIPATION_ONSITE, Registration.PARTICIPATION_BOTH]:
        if auto_onsite and event.accepted_onsite < auto_onsite:
            should_accept = True

    if ptype in [Registration.PARTICIPATION_ONLINE, Registration.PARTICIPATION_BOTH]:
        if auto_online and event.accepted_online < auto_online:
            should_accept = True

    if should_accept:
        registration.status       = Registration.STATUS_ACCEPTED
        registration.validated_at = timezone.now()
        registration.save(update_fields=['status', 'validated_at'])


def _send_emails(registration):
    """Envoie l'email de confirmation ou d'attente."""
    try:
        from notifications.email_service import (
            send_registration_confirmation,
            send_registration_pending,
        )
        if registration.status == Registration.STATUS_ACCEPTED:
            send_registration_confirmation(registration)
            registration.confirmation_sent = True
            registration.save(update_fields=['confirmation_sent'])
        else:
            send_registration_pending(registration)
    except Exception as e:
        logger.warning(f"Email non envoyé : {e}")


def registration_success(request, token):
    """Page de confirmation après inscription."""
    registration = get_object_or_404(Registration, token=token)
    return render(request, 'registrations/success.html', {'registration': registration})


def registration_confirm(request, token):
    """Confirmation par lien email."""
    registration = get_object_or_404(Registration, token=token)
    return render(request, 'registrations/confirm.html', {'registration': registration})