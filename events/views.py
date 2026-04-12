from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Event


def event_list(request):
    """Page d'accueil — liste des événements publiés."""
    events   = Event.objects.filter(status=Event.STATUS_PUBLISHED).select_related('location', 'organizer')
    upcoming = events.filter(start_datetime__gte=timezone.now())
    past     = events.filter(end_datetime__lt=timezone.now())

    context = {
        'upcoming_events': upcoming,
        'past_events':     past,
    }
    return render(request, 'events/list.html', context)


def event_detail(request, slug):
    """Page détail d'un événement."""
    event = get_object_or_404(
        Event.objects.select_related('location', 'organizer')
                     .prefetch_related(
                         'speakers__user',
                         'days__sessions__speaker__user',
                     ),
        slug=slug,
        status=Event.STATUS_PUBLISHED,
    )

    # Chronogramme
    days = event.days.prefetch_related(
        'sessions__speaker__user'
    ).order_by('date', 'order')

    # Vérifier si inscription possible
    mode = getattr(event, 'participation_mode', 'online_only')
    if mode == 'onsite_only':
        can_register = not event.is_full_onsite and event.is_upcoming
    elif mode == 'online_only':
        can_register = not event.is_full_online and event.is_upcoming
    else:  # hybrid
        can_register = (not event.is_full_onsite or not event.is_full_online) and event.is_upcoming

    context = {
        'event':              event,
        'days':               days,
        'has_schedule':       days.exists(),
        'can_register':       can_register,
        'participation_mode': mode,
    }
    return render(request, 'events/detail.html', context)