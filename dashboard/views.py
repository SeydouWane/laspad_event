from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Q
import csv
import io

from events.models import Event, Location
from events.forms import EventForm, LocationForm
from registrations.models import Registration, Participant
from notifications.tasks import send_confirmation_email, send_refused_email


def is_staff(user):
    return user.is_staff or user.is_superuser


def dashboard_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('dashboard:home')
    else:
        form = AuthenticationForm()
    return render(request, 'dashboard/login.html', {'form': form})


def dashboard_logout(request):
    logout(request)
    return redirect('events:list')


@login_required
@user_passes_test(is_staff)
def dashboard_home(request):
    """Vue principale du dashboard — statistiques globales."""
    total_events = Event.objects.count()
    published_events = Event.objects.filter(status=Event.STATUS_PUBLISHED).count()
    upcoming_events = Event.objects.filter(
        status=Event.STATUS_PUBLISHED,
        start_datetime__gte=timezone.now()
    ).count()
    total_registrations = Registration.objects.count()
    pending_registrations = Registration.objects.filter(status=Registration.STATUS_PENDING).count()
    accepted_registrations = Registration.objects.filter(status=Registration.STATUS_ACCEPTED).count()
    total_participants = Participant.objects.count()

    recent_registrations = Registration.objects.select_related(
        'event', 'participant'
    ).order_by('-registered_at')[:10]

    recent_events = Event.objects.order_by('-created_at')[:5]

    context = {
        'total_events': total_events,
        'published_events': published_events,
        'upcoming_events': upcoming_events,
        'total_registrations': total_registrations,
        'pending_registrations': pending_registrations,
        'accepted_registrations': accepted_registrations,
        'total_participants': total_participants,
        'recent_registrations': recent_registrations,
        'recent_events': recent_events,
    }
    return render(request, 'dashboard/home.html', context)


@login_required
@user_passes_test(is_staff)
def event_list(request):
    events = Event.objects.annotate(
        reg_count=Count('registrations'),
        pending_count=Count('registrations', filter=Q(registrations__status='en_attente')),
    ).order_by('-created_at')
    return render(request, 'dashboard/events/list.html', {'events': events})



@login_required
@user_passes_test(is_staff)
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        location_form = LocationForm(request.POST, instance=event.location)
        if form.is_valid() and location_form.is_valid():
            location_form.save()
            form.save()
            messages.success(request, "Événement mis à jour.")
            return redirect('dashboard:event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)
        location_form = LocationForm(instance=event.location)
    return render(request, 'dashboard/events/form.html', {
        'form': form,
        'location_form': location_form,
        'event': event,
        'action': 'Modifier',
        'newsletter_count': Participant.objects.filter(newsletter=True).count(),
    })


@login_required
@user_passes_test(is_staff)
def event_detail(request, pk):
    event         = get_object_or_404(Event, pk=pk)
    registrations = event.registrations.select_related('participant').order_by('-registered_at')
    pending       = registrations.filter(status=Registration.STATUS_PENDING)
    accepted      = registrations.filter(status=Registration.STATUS_ACCEPTED)
    refused       = registrations.filter(status=Registration.STATUS_REFUSED)

    # Ventilation hybride
    pending_onsite  = pending.filter(participation_type__in=['onsite', 'both'])
    pending_online  = pending.filter(participation_type__in=['online', 'both'])
    accepted_onsite = accepted.filter(participation_type__in=['onsite', 'both'])
    accepted_online = accepted.filter(participation_type__in=['online', 'both'])

    context = {
        'event':            event,
        'registrations':    registrations,
        'pending':          pending,
        'accepted':         accepted,
        'refused':          refused,
        'pending_onsite':   pending_onsite,
        'pending_online':   pending_online,
        'accepted_onsite':  accepted_onsite,
        'accepted_online':  accepted_online,
        'participation_mode': getattr(event, 'participation_mode', 'online_only'),
    }
    return render(request, 'dashboard/events/detail.html', context)

# ═══════════════════════════════════════════════════════════════
# CHRONOGRAMME
# ═══════════════════════════════════════════════════════════════

@login_required
@user_passes_test(is_staff)
def schedule_manage(request, pk):
    """Gérer le chronogramme d'un événement (jours + sessions)."""
    from events.models import EventDay, Session, Organizer
    from events.forms import EventDayForm, SessionForm

    event = get_object_or_404(Event, pk=pk)
    days  = event.days.prefetch_related('sessions__speaker').order_by('date', 'order')

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Ajouter un jour ──
        if action == 'add_day':
            form = EventDayForm(request.POST)
            if form.is_valid():
                day = form.save(commit=False)
                day.event = event
                day.save()
                messages.success(request, f"Jour du {day.date.strftime('%d/%m/%Y')} ajouté.")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field} : {error}")

        # ── Modifier un jour ──
        elif action == 'edit_day':
            from events.models import EventDay
            day_pk = request.POST.get('day_pk')
            day    = get_object_or_404(EventDay, pk=day_pk, event=event)
            form   = EventDayForm(request.POST, instance=day)
            if form.is_valid():
                form.save()
                messages.success(request, "Jour mis à jour.")
            else:
                messages.error(request, "Erreur lors de la mise à jour du jour.")

        # ── Supprimer un jour ──
        elif action == 'delete_day':
            from events.models import EventDay
            day_pk = request.POST.get('day_pk')
            day    = get_object_or_404(EventDay, pk=day_pk, event=event)
            day.delete()
            messages.warning(request, "Jour supprimé (ainsi que ses sessions).")

        # ── Ajouter une session ──
        elif action == 'add_session':
            from events.models import EventDay
            day_pk = request.POST.get('day_pk')
            day    = get_object_or_404(EventDay, pk=day_pk, event=event)
            form   = SessionForm(request.POST)
            if form.is_valid():
                session       = form.save(commit=False)
                session.day   = day
                session.save()
                messages.success(request, f"Session « {session.title} » ajoutée.")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field} : {error}")

        # ── Modifier une session ──
        elif action == 'edit_session':
            from events.models import Session
            session_pk = request.POST.get('session_pk')
            session    = get_object_or_404(Session, pk=session_pk, day__event=event)
            form       = SessionForm(request.POST, instance=session)
            if form.is_valid():
                form.save()
                messages.success(request, "Session mise à jour.")
            else:
                messages.error(request, "Erreur lors de la mise à jour de la session.")

        # ── Supprimer une session ──
        elif action == 'delete_session':
            from events.models import Session
            session_pk = request.POST.get('session_pk')
            session    = get_object_or_404(Session, pk=session_pk, day__event=event)
            session.delete()
            messages.warning(request, "Session supprimée.")

        return redirect('dashboard:schedule_manage', pk=pk)

    # ── GET ──
    speakers  = __import__('events.models', fromlist=['Organizer']).Organizer.objects.select_related('user').all()
    day_form  = EventDayForm(initial={'order': days.count() + 1})

    context = {
        'event':    event,
        'days':     days,
        'day_form': day_form,
        'speakers': speakers,
        'SessionForm': SessionForm,
    }
    return render(request, 'dashboard/events/schedule.html', context)

@login_required
@user_passes_test(is_staff)
def registration_accept(request, pk):
    reg = get_object_or_404(Registration, pk=pk)
    if reg.status == Registration.STATUS_PENDING:
        reg.accept()
        try:
            from notifications.email_service import send_registration_confirmation
            send_registration_confirmation(reg)
            reg.confirmation_sent = True
            reg.save(update_fields=['confirmation_sent'])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Email non envoyé : {e}")
        messages.success(request, f"{reg.participant.full_name} accepté(e).")
    return redirect('dashboard:event_detail', pk=reg.event.pk)


@login_required
@user_passes_test(is_staff)
def registration_refuse(request, pk):
    reg = get_object_or_404(Registration, pk=pk)
    if reg.status == Registration.STATUS_PENDING:
        reg.refuse()
        try:
            from notifications.email_service import send_registration_refused
            send_registration_refused(reg)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Email non envoyé : {e}")
        messages.warning(request, f"{reg.participant.full_name} refusé(e).")
    return redirect('dashboard:event_detail', pk=reg.event.pk)

@login_required
@user_passes_test(is_staff)
def registration_accept_bulk(request, pk):
    """Accepter en masse les inscriptions en attente d'un événement."""
    event = get_object_or_404(Event, pk=pk)

    if request.method != 'POST':
        return redirect('dashboard:event_detail', pk=pk)

    mode   = request.POST.get('mode', 'all')   # 'onsite' | 'online' | 'both' | 'all'
    limit  = request.POST.get('limit', '')      # nombre max ou vide = tous
    ids    = request.POST.getlist('reg_ids')    # sélection manuelle

    # Construire le queryset selon le mode
    qs = event.registrations.filter(status=Registration.STATUS_PENDING)

    if mode == 'onsite':
        qs = qs.filter(participation_type__in=['onsite', 'both'])
    elif mode == 'online':
        qs = qs.filter(participation_type__in=['online', 'both'])
    elif ids:
        qs = qs.filter(pk__in=ids)

    qs = qs.order_by('registered_at')

    # Appliquer la limite si précisée
    if limit:
        try:
            qs = qs[:int(limit)]
        except (ValueError, TypeError):
            pass

    count = 0
    for reg in qs:
        reg.status       = Registration.STATUS_ACCEPTED
        reg.validated_at = timezone.now()
        reg.save(update_fields=['status', 'validated_at'])
        count += 1
        try:
            from notifications.email_service import send_registration_confirmation
            send_registration_confirmation(reg)
            reg.confirmation_sent = True
            reg.save(update_fields=['confirmation_sent'])
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Email non envoyé : {e}")

    mode_label = {'onsite': 'présentiel', 'online': 'en ligne', 'both': 'les deux', 'all': ''}.get(mode, '')
    messages.success(request, f"{count} inscription(s) {mode_label} acceptée(s).")
    return redirect('dashboard:event_detail', pk=pk)


@login_required
@user_passes_test(is_staff)
def registration_refuse_bulk(request, pk):
    """Refuser en masse des inscriptions sélectionnées."""
    event = get_object_or_404(Event, pk=pk)

    if request.method != 'POST':
        return redirect('dashboard:event_detail', pk=pk)

    ids = request.POST.getlist('reg_ids')
    qs  = event.registrations.filter(status=Registration.STATUS_PENDING)
    if ids:
        qs = qs.filter(pk__in=ids)

    count = 0
    for reg in qs:
        reg.status       = Registration.STATUS_REFUSED
        reg.validated_at = timezone.now()
        reg.save(update_fields=['status', 'validated_at'])
        count += 1
        try:
            from notifications.email_service import send_registration_refused
            send_registration_refused(reg)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Email non envoyé : {e}")

    messages.warning(request, f"{count} inscription(s) refusée(s).")
    return redirect('dashboard:event_detail', pk=pk)

@login_required
@user_passes_test(is_staff)
def export_registrations_csv(request, pk):
    """Export CSV des inscriptions d'un événement."""
    event = get_object_or_404(Event, pk=pk)
    registrations = event.registrations.select_related('participant').all()

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="inscriptions_{event.slug}.csv"'
    response.write('\ufeff')  # BOM UTF-8 pour Excel

    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Prénom', 'Nom', 'Email', 'Institution', 'Fonction', 'Téléphone', 'Statut', 'Date inscription', 'Motivation'])

    for reg in registrations:
        p = reg.participant
        writer.writerow([
            p.first_name, p.last_name, p.email,
            p.institution, p.role, p.phone,
            reg.get_status_display(),
            reg.registered_at.strftime('%d/%m/%Y %H:%M'),
            reg.motivation,
        ])
    return response


@login_required
@user_passes_test(is_staff)
def participants_list(request):
    participants = Participant.objects.annotate(
        event_count=Count('registrations')
    ).order_by('-created_at')
    return render(request, 'dashboard/participants/list.html', {'participants': participants})


@login_required
@user_passes_test(is_staff)
def stats(request):
    """Page de statistiques globales."""
    events = Event.objects.annotate(reg_count=Count('registrations')).order_by('-reg_count')[:10]
    registrations_by_status = {
        'en_attente': Registration.objects.filter(status='en_attente').count(),
        'accepte':    Registration.objects.filter(status='accepte').count(),
        'refuse':     Registration.objects.filter(status='refuse').count(),
    }
    context = {
        'top_events':               events,
        'registrations_by_status':  registrations_by_status,
        'onsite_count':             Registration.objects.filter(participation_type='onsite').count(),
        'online_count':             Registration.objects.filter(participation_type='online').count(),
        'both_count':               Registration.objects.filter(participation_type='both').count(),
        'attended_onsite':          Registration.objects.filter(attended_onsite=True).count(),
        'attended_online':          Registration.objects.filter(attended_online=True).count(),
    }
    return render(request, 'dashboard/stats.html', context)

@login_required
@user_passes_test(is_staff)
def contact_participants(request, pk):
    """Envoyer un email groupé à tous les participants acceptés d'un événement."""
    event = get_object_or_404(Event, pk=pk)
    registrations = event.registrations.filter(
        status=Registration.STATUS_ACCEPTED
    ).select_related('participant')

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        target = request.POST.get('target', 'accepted')

        if not subject or not body:
            messages.error(request, "Le sujet et le message sont obligatoires.")
            return redirect('dashboard:event_detail', pk=pk)

        # Filtrer selon la cible
        if target == 'all':
            regs = event.registrations.select_related('participant').all()
        elif target == 'pending':
            regs = event.registrations.filter(
                status=Registration.STATUS_PENDING
            ).select_related('participant')
        else:
            regs = registrations

        recipients = [r.participant.email for r in regs]

        if not recipients:
            messages.warning(request, "Aucun participant dans cette sélection.")
            return redirect('dashboard:event_detail', pk=pk)

        # Envoi
        from django.core.mail import send_mass_mail
        from django.conf import settings

        emails = tuple(
            (subject, body, settings.DEFAULT_FROM_EMAIL, [email])
            for email in recipients
        )
        try:
            send_mass_mail(emails, fail_silently=False)
            messages.success(
                request,
                f"Message envoyé à {len(recipients)} participant(s)."
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur envoi groupé : {e}")
            messages.error(
                request,
                "Erreur lors de l'envoi. Vérifiez la configuration SMTP dans .env"
            )

        return redirect('dashboard:event_detail', pk=pk)

    # GET — afficher le formulaire
    context = {
        'event': event,
        'registrations': registrations,
        'accepted_count': event.registrations.filter(status=Registration.STATUS_ACCEPTED).count(),
        'pending_count': event.registrations.filter(status=Registration.STATUS_PENDING).count(),
        'all_count': event.registrations.count(),
    }
    return render(request, 'dashboard/events/contact.html', context)


@login_required
@user_passes_test(is_staff)
def contact_one_participant(request, pk):
    """Envoyer un email à un participant unique."""
    from registrations.models import Participant
    participant = get_object_or_404(Participant, pk=pk)

    if request.method == 'POST':
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()

        if not subject or not body:
            messages.error(request, "Le sujet et le message sont obligatoires.")
            return redirect('dashboard:participants_list')

        from django.core.mail import send_mail
        from django.conf import settings
        try:
            send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [participant.email])
            messages.success(request, f"Message envoyé à {participant.full_name}.")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Erreur envoi : {e}")
            messages.error(request, "Erreur lors de l'envoi. Vérifiez la configuration SMTP.")

        return redirect('dashboard:participants_list')

    return render(request, 'dashboard/participants/contact.html', {'participant': participant})

@login_required
@user_passes_test(is_staff)
def event_create(request):
    from registrations.models import Participant
    newsletter_count = Participant.objects.filter(newsletter=True).count()

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        location_form = LocationForm(request.POST)
        if form.is_valid() and location_form.is_valid():
            location = location_form.save()
            event = form.save(commit=False)
            event.location = location
            event.organizer = request.user
            event.save()
            form.save_m2m()

            # Pré-inscrits
            first_names  = request.POST.getlist('pre_first_name[]')
            last_names   = request.POST.getlist('pre_last_name[]')
            emails       = request.POST.getlist('pre_email[]')
            phones       = request.POST.getlist('pre_phone[]')
            institutions = request.POST.getlist('pre_institution[]')
            roles        = request.POST.getlist('pre_role[]')

            from registrations.models import Registration
            count = 0
            for i, email in enumerate(emails):
                if not email:
                    continue
                try:
                    participant, _ = Participant.objects.get_or_create(
                        email=email.lower().strip(),
                        defaults={
                            'first_name':  first_names[i]  if i < len(first_names)  else '',
                            'last_name':   last_names[i]   if i < len(last_names)   else '',
                            'institution': institutions[i] if i < len(institutions) else '',
                            'role':        roles[i]        if i < len(roles)        else '',
                            'phone':       phones[i]       if i < len(phones)       else '',
                        }
                    )
                    if not Registration.objects.filter(event=event, participant=participant).exists():
                        reg = Registration.objects.create(
                            event=event, participant=participant,
                            status=Registration.STATUS_ACCEPTED,
                        )
                        count += 1
                        try:
                            from notifications.email_service import send_registration_confirmation
                            send_registration_confirmation(reg)
                        except Exception:
                            pass
                except Exception:
                    pass

            # Notification newsletter
            if request.POST.get('notify_newsletter') == '1' and event.status == Event.STATUS_PUBLISHED:
                subscribers = Participant.objects.filter(newsletter=True)
                notified = 0
                for sub in subscribers:
                    try:
                        from django.core.mail import send_mail
                        from django.conf import settings
                        send_mail(
                            subject=f"[LASPAD Event] Nouvel événement : {event.title}",
                            message=f"Bonjour,\n\nLe LASPAD a le plaisir de vous annoncer un nouvel événement :\n\n{event.title}\n{event.start_datetime.strftime('%d/%m/%Y à %Hh%M')}\n\nPour en savoir plus et vous inscrire :\n{settings.SITE_URL}{event.get_absolute_url()}\n\nCordialement,\nL'équipe LASPAD",
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[sub.email],
                            fail_silently=True,
                        )
                        notified += 1
                    except Exception:
                        pass
                if notified:
                    messages.info(request, f"Newsletter envoyée à {notified} abonné(s).")

            msg = f"L'événement « {event.title} » a été créé."
            if count:
                msg += f" {count} participant(s) pré-inscrit(s)."
            messages.success(request, msg)
            return redirect('dashboard:event_detail', pk=event.pk)
    else:
        form = EventForm()
        location_form = LocationForm()

    return render(request, 'dashboard/events/form.html', {
        'form': form,
        'location_form': location_form,
        'action': 'Créer',
        'newsletter_count': newsletter_count,
    })

# ═══════════════════════════════════════════════════════════════
# GESTION DES UTILISATEURS
# ═══════════════════════════════════════════════════════════════

@login_required
@user_passes_test(is_staff)
def user_list(request):
    """Liste de tous les utilisateurs de la plateforme."""
    from django.contrib.auth.models import User
    users = User.objects.all().order_by('-date_joined')
    context = {
        'users': users,
        'total': users.count(),
        'active': users.filter(is_active=True).count(),
        'suspended': users.filter(is_active=False).count(),
        'admins': users.filter(is_superuser=True).count(),
        'managers': users.filter(is_staff=True, is_superuser=False).count(),
    }
    return render(request, 'dashboard/users/list.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)  # Seul le super-admin peut inviter
def user_invite(request):
    """Créer un nouvel utilisateur (admin ou gestionnaire)."""
    from django.contrib.auth.models import User
    if request.method == 'POST':
        username    = request.POST.get('username', '').strip()
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        email       = request.POST.get('email', '').strip()
        password    = request.POST.get('password', '').strip()
        password2   = request.POST.get('password2', '').strip()
        role        = request.POST.get('role', 'manager')  # 'admin' ou 'manager'

        # Validations
        if not all([username, first_name, last_name, email, password]):
            messages.error(request, "Tous les champs obligatoires doivent être remplis.")
            return render(request, 'dashboard/users/invite.html', {'post': request.POST})

        if password != password2:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'dashboard/users/invite.html', {'post': request.POST})

        if len(password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return render(request, 'dashboard/users/invite.html', {'post': request.POST})

        if User.objects.filter(username=username).exists():
            messages.error(request, f"Le nom d'utilisateur « {username} » est déjà pris.")
            return render(request, 'dashboard/users/invite.html', {'post': request.POST})

        if User.objects.filter(email=email).exists():
            messages.error(request, f"L'email « {email} » est déjà utilisé.")
            return render(request, 'dashboard/users/invite.html', {'post': request.POST})

        # Créer l'utilisateur
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        else:  # manager
            user.is_staff = True
            user.is_superuser = False

        user.save()

        role_label = 'Administrateur' if role == 'admin' else 'Gestionnaire'
        messages.success(request, f"{role_label} « {user.get_full_name() or username} » créé avec succès.")
        return redirect('dashboard:user_list')

    return render(request, 'dashboard/users/invite.html', {'post': {}})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_edit(request, pk):
    """Modifier le rôle et les infos d'un utilisateur."""
    from django.contrib.auth.models import User
    target = get_object_or_404(User, pk=pk)

    # Empêcher de modifier son propre compte depuis ici
    if target == request.user:
        messages.warning(request, "Vous ne pouvez pas modifier votre propre compte depuis cette interface.")
        return redirect('dashboard:user_list')

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip()
        role       = request.POST.get('role', 'manager')
        new_pw     = request.POST.get('new_password', '').strip()

        target.first_name = first_name
        target.last_name  = last_name
        target.email      = email

        if role == 'admin':
            target.is_staff = True
            target.is_superuser = True
        elif role == 'manager':
            target.is_staff = True
            target.is_superuser = False
        else:
            target.is_staff = False
            target.is_superuser = False

        if new_pw:
            if len(new_pw) < 8:
                messages.error(request, "Le nouveau mot de passe doit contenir au moins 8 caractères.")
                return render(request, 'dashboard/users/edit.html', {'target': target})
            target.set_password(new_pw)

        target.save()
        messages.success(request, f"Compte de « {target.get_full_name() or target.username} » mis à jour.")
        return redirect('dashboard:user_list')

    return render(request, 'dashboard/users/edit.html', {'target': target})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_suspend(request, pk):
    """Suspendre (désactiver) un compte utilisateur."""
    from django.contrib.auth.models import User
    target = get_object_or_404(User, pk=pk)

    if target == request.user:
        messages.error(request, "Vous ne pouvez pas suspendre votre propre compte.")
        return redirect('dashboard:user_list')

    target.is_active = False
    target.save()
    messages.warning(request, f"Le compte de « {target.get_full_name() or target.username} » a été suspendu.")
    return redirect('dashboard:user_list')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_activate(request, pk):
    """Réactiver un compte suspendu."""
    from django.contrib.auth.models import User
    target = get_object_or_404(User, pk=pk)
    target.is_active = True
    target.save()
    messages.success(request, f"Le compte de « {target.get_full_name() or target.username} » a été réactivé.")
    return redirect('dashboard:user_list')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def user_delete(request, pk):
    """Supprimer définitivement un compte utilisateur."""
    from django.contrib.auth.models import User
    target = get_object_or_404(User, pk=pk)

    if target == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect('dashboard:user_list')

    if request.method == 'POST':
        name = target.get_full_name() or target.username
        target.delete()
        messages.success(request, f"Le compte « {name} » a été supprimé définitivement.")
        return redirect('dashboard:user_list')

    return render(request, 'dashboard/users/delete_confirm.html', {'target': target})

# ═══════════════════════════════════════════════════════════════
# GESTION DES INTERVENANTS
# ═══════════════════════════════════════════════════════════════

@login_required
@user_passes_test(is_staff)
def organizer_list(request):
    from events.models import Organizer
    organizers = Organizer.objects.select_related('user').all()
    return render(request, 'dashboard/organizers/list.html', {'organizers': organizers})


@login_required
@user_passes_test(is_staff)
def organizer_create(request):
    from django.contrib.auth.models import User
    if request.method == 'POST':
        first_name  = request.POST.get('first_name', '').strip()
        last_name   = request.POST.get('last_name', '').strip()
        email       = request.POST.get('email', '').strip()
        institution = request.POST.get('institution', '').strip()
        bio         = request.POST.get('bio', '').strip()
        phone       = request.POST.get('phone', '').strip()
        photo       = request.FILES.get('photo')

        if not all([first_name, last_name, email]):
            messages.error(request, "Prénom, Nom et Email sont obligatoires.")
            return render(request, 'dashboard/organizers/form.html', {'action': 'Ajouter', 'post': request.POST})

        # Créer ou récupérer le User associé
        username = f"{first_name.lower()}.{last_name.lower()}".replace(' ', '')
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True,
            }
        )
        if not created:
            user.first_name = first_name
            user.last_name  = last_name
            user.save()

        # Créer le profil Organizer
        from events.models import Organizer
        organizer, _ = Organizer.objects.get_or_create(user=user)
        organizer.institution = institution
        organizer.bio         = bio
        organizer.phone       = phone
        if photo:
            organizer.photo = photo
        organizer.save()

        messages.success(request, f"Intervenant « {first_name} {last_name} » ajouté avec succès.")

        # Retourner à la création d'événement si on venait de là
        next_url = request.GET.get('next', '')
        if next_url:
            return redirect(next_url)
        return redirect('dashboard:organizer_list')

    return render(request, 'dashboard/organizers/form.html', {'action': 'Ajouter', 'post': {}})


@login_required
@user_passes_test(is_staff)
def organizer_edit(request, pk):
    from events.models import Organizer
    organizer = get_object_or_404(Organizer, pk=pk)
    if request.method == 'POST':
        organizer.user.first_name = request.POST.get('first_name', '').strip()
        organizer.user.last_name  = request.POST.get('last_name', '').strip()
        organizer.user.email      = request.POST.get('email', '').strip()
        organizer.user.save()
        organizer.institution = request.POST.get('institution', '').strip()
        organizer.bio         = request.POST.get('bio', '').strip()
        organizer.phone       = request.POST.get('phone', '').strip()
        if request.FILES.get('photo'):
            organizer.photo = request.FILES['photo']
        organizer.save()
        messages.success(request, "Intervenant mis à jour.")
        return redirect('dashboard:organizer_list')
    return render(request, 'dashboard/organizers/form.html', {
        'action': 'Modifier', 'organizer': organizer, 'post': {}
    })


@login_required
@user_passes_test(is_staff)
def organizer_delete(request, pk):
    from events.models import Organizer
    organizer = get_object_or_404(Organizer, pk=pk)
    if request.method == 'POST':
        name = organizer.user.get_full_name()
        organizer.delete()
        messages.success(request, f"Intervenant « {name} » supprimé.")
        return redirect('dashboard:organizer_list')
    return render(request, 'dashboard/organizers/delete_confirm.html', {'organizer': organizer})

@login_required
@user_passes_test(is_staff)
def resend_ticket(request, pk):
    """Renvoyer le ticket PDF à un participant depuis le dashboard."""
    reg = get_object_or_404(Registration, pk=pk)

    if not reg.needs_ticket:
        messages.warning(request, "Ce participant ne nécessite pas de ticket PDF.")
        return redirect('dashboard:event_detail', pk=reg.event.pk)

    try:
        from notifications.email_service import resend_ticket as send_ticket
        send_ticket(reg)
        messages.success(request, f"Ticket renvoyé à {reg.participant.full_name}.")
    except Exception as e:
        messages.error(request, f"Erreur lors de l'envoi : {e}")

    return redirect('dashboard:event_detail', pk=reg.event.pk)

# ═══════════════════════════════════════════════════════════════
# SCAN QR CODE
# ═══════════════════════════════════════════════════════════════

@login_required
@user_passes_test(is_staff)
def scan_home(request):
    """Interface de scan QR — optimisée mobile."""
    from events.models import Event
    # Événements en cours ou à venir pour filtrer
    events = Event.objects.filter(
        status=Event.STATUS_PUBLISHED,
        end_datetime__gte=timezone.now(),
    ).order_by('start_datetime')

    return render(request, 'dashboard/scan/home.html', {'events': events})


@login_required
@user_passes_test(is_staff)
def scan_ticket(request, token):
    """
    Page de validation d'un ticket.
    Appelée après scan du QR code ou saisie manuelle du token.
    """
    reg = get_object_or_404(Registration, token=token)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'mark_onsite' and not reg.attended_onsite:
            reg.mark_attended_onsite()
            messages.success(
                request,
                f"✅ Présence confirmée — {reg.participant.full_name}"
            )

        elif action == 'mark_online' and not reg.attended_online:
            reg.mark_attended_online()
            messages.success(
                request,
                f"✅ Connexion confirmée — {reg.participant.full_name}"
            )

        elif action == 'mark_onsite' and reg.attended_onsite:
            messages.warning(request, "Ce ticket a déjà été scanné.")

        return redirect('dashboard:scan_ticket', token=token)

    # Vérifications
    is_valid   = reg.status == Registration.STATUS_ACCEPTED
    is_onsite  = reg.is_onsite
    is_online  = reg.is_online
    event      = reg.event

    context = {
        'registration': reg,
        'event':        event,
        'participant':  reg.participant,
        'is_valid':     is_valid,
        'is_onsite':    is_onsite,
        'is_online':    is_online,
        'already_attended_onsite': reg.attended_onsite,
        'already_attended_online': reg.attended_online,
    }
    return render(request, 'dashboard/scan/ticket.html', context)

@login_required
@user_passes_test(is_staff)
def scan_lookup(request):
    """Recherche un ticket par numéro (LASPAD-2026-0001) → retourne le token UUID."""
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'token': None})

    # Chercher par numéro de ticket
    reg = Registration.objects.filter(ticket_number__iexact=q).first()
    if not reg:
        # Chercher par token UUID partiel
        reg = Registration.objects.filter(token__startswith=q).first()
    if not reg:
        # Chercher par email
        reg = Registration.objects.filter(
            participant__email__iexact=q,
            status=Registration.STATUS_ACCEPTED,
        ).first()

    if reg:
        return JsonResponse({'token': str(reg.token), 'name': reg.participant.full_name})
    return JsonResponse({'token': None})

@login_required
@user_passes_test(is_staff)
def export_presence_csv(request, pk):
    """Export CSV des présences d'un événement."""
    event         = get_object_or_404(Event, pk=pk)
    registrations = event.registrations.filter(
        status=Registration.STATUS_ACCEPTED,
    ).select_related('participant').order_by('participant__last_name')

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = (
        f'attachment; filename="presences_{event.slug}.csv"'
    )
    response.write('\ufeff')  # BOM UTF-8 pour Excel

    writer = csv.writer(response, delimiter=';')

    # ── En-tête ──
    mode = getattr(event, 'participation_mode', 'online_only')
    if mode == 'hybrid':
        writer.writerow([
            'Prénom', 'Nom', 'Email', 'Institution', 'Fonction', 'Téléphone',
            'Mode participation', 'N° Ticket',
            'Présent (présentiel)', 'Heure pointage présentiel',
            'Connecté (en ligne)',  'Heure connexion en ligne',
            'Date inscription',
        ])
    elif mode == 'onsite_only':
        writer.writerow([
            'Prénom', 'Nom', 'Email', 'Institution', 'Fonction', 'Téléphone',
            'N° Ticket',
            'Présent', 'Heure de pointage',
            'Date inscription',
        ])
    else:  # online_only
        writer.writerow([
            'Prénom', 'Nom', 'Email', 'Institution', 'Fonction', 'Téléphone',
            'Connecté', 'Heure de connexion',
            'Date inscription',
        ])

    # ── Lignes ──
    for reg in registrations:
        p = reg.participant

        attended_onsite_str = 'Oui' if reg.attended_onsite else 'Non'
        attended_online_str = 'Oui' if reg.attended_online else 'Non'
        attended_at_str     = (
            reg.attended_at.strftime('%d/%m/%Y %H:%M')
            if reg.attended_at else '—'
        )

        mode_labels = {
            'onsite': 'Présentiel',
            'online': 'En ligne',
            'both':   'Présentiel + En ligne',
        }
        ptype_str = mode_labels.get(
            getattr(reg, 'participation_type', 'online'), 'En ligne'
        )

        if mode == 'hybrid':
            writer.writerow([
                p.first_name, p.last_name, p.email,
                p.institution, p.role, p.phone or '—',
                ptype_str,
                reg.ticket_number or '—',
                attended_onsite_str, attended_at_str if reg.attended_onsite else '—',
                attended_online_str, attended_at_str if reg.attended_online else '—',
                reg.registered_at.strftime('%d/%m/%Y %H:%M'),
            ])
        elif mode == 'onsite_only':
            writer.writerow([
                p.first_name, p.last_name, p.email,
                p.institution, p.role, p.phone or '—',
                reg.ticket_number or '—',
                attended_onsite_str,
                attended_at_str if reg.attended_onsite else '—',
                reg.registered_at.strftime('%d/%m/%Y %H:%M'),
            ])
        else:
            writer.writerow([
                p.first_name, p.last_name, p.email,
                p.institution, p.role, p.phone or '—',
                attended_online_str,
                attended_at_str if reg.attended_online else '—',
                reg.registered_at.strftime('%d/%m/%Y %H:%M'),
            ])

    return response