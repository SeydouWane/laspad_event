from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from slugify import slugify
import uuid


class Organizer(models.Model):
    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organizer_profile')
    bio         = models.TextField(blank=True)
    institution = models.CharField(max_length=200, blank=True)
    photo       = models.ImageField(upload_to='organizers/', blank=True, null=True)
    phone       = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.get_full_name()} — {self.institution}"

    class Meta:
        verbose_name        = 'Organisateur'
        verbose_name_plural = 'Organisateurs'


class Location(models.Model):
    MODE_ONLINE  = 'online'
    MODE_ONSITE  = 'onsite'
    MODE_HYBRID  = 'hybrid'
    MODE_CHOICES = [
        (MODE_ONLINE, 'En ligne'),
        (MODE_ONSITE, 'Présentiel'),
        (MODE_HYBRID, 'Hybride'),
    ]
    PLATFORM_MEET    = 'meet'
    PLATFORM_ZOOM    = 'zoom'
    PLATFORM_YOUTUBE = 'youtube'
    PLATFORM_OTHER   = 'other'
    PLATFORM_CHOICES = [
        (PLATFORM_MEET,    'Google Meet'),
        (PLATFORM_ZOOM,    'Zoom'),
        (PLATFORM_YOUTUBE, 'YouTube Live'),
        (PLATFORM_OTHER,   'Autre'),
    ]
    mode            = models.CharField(max_length=10, choices=MODE_CHOICES, default=MODE_ONLINE)
    platform        = models.CharField(max_length=10, choices=PLATFORM_CHOICES, blank=True, null=True)
    online_link     = models.URLField(blank=True, null=True, verbose_name='Lien de diffusion')
    address         = models.CharField(max_length=500, blank=True, verbose_name='Adresse')
    city            = models.CharField(max_length=100, blank=True, verbose_name='Ville')
    country         = models.CharField(max_length=100, default='Sénégal', verbose_name='Pays')
    google_maps_url = models.URLField(blank=True, null=True, verbose_name='Lien Google Maps')

    def __str__(self):
        if self.mode == self.MODE_ONLINE:
            return f"En ligne — {self.get_platform_display()}"
        return f"{self.address}, {self.city}"

    class Meta:
        verbose_name        = 'Lieu'
        verbose_name_plural = 'Lieux'


class Event(models.Model):
    # ── Types ──
    TYPE_WEBINAR    = 'webinaire'
    TYPE_CONFERENCE = 'conference'
    TYPE_WORKSHOP   = 'atelier'
    TYPE_SEMINAR    = 'seminaire'
    TYPE_OTHER      = 'autre'
    TYPE_CHOICES    = [
        (TYPE_WEBINAR,    'Webinaire'),
        (TYPE_CONFERENCE, 'Conférence'),
        (TYPE_WORKSHOP,   'Atelier'),
        (TYPE_SEMINAR,    'Séminaire'),
        (TYPE_OTHER,      'Autre'),
    ]

    # ── Accès ──
    ACCESS_DIRECT     = 'direct'
    ACCESS_VALIDATION = 'validation'
    ACCESS_CHOICES    = [
        (ACCESS_DIRECT,     'Inscription directe'),
        (ACCESS_VALIDATION, 'Avec validation'),
    ]

    # ── Statuts ──
    STATUS_DRAFT     = 'brouillon'
    STATUS_PUBLISHED = 'publie'
    STATUS_CANCELLED = 'annule'
    STATUS_FINISHED  = 'termine'
    STATUS_CHOICES   = [
        (STATUS_DRAFT,     'Brouillon'),
        (STATUS_PUBLISHED, 'Publié'),
        (STATUS_CANCELLED, 'Annulé'),
        (STATUS_FINISHED,  'Terminé'),
    ]

    # ── Mode de participation ──
    PARTICIPATION_ONSITE_ONLY = 'onsite_only'
    PARTICIPATION_ONLINE_ONLY = 'online_only'
    PARTICIPATION_HYBRID      = 'hybrid'
    PARTICIPATION_CHOICES     = [
        (PARTICIPATION_ONSITE_ONLY, 'Présentiel uniquement'),
        (PARTICIPATION_ONLINE_ONLY, 'En ligne uniquement'),
        (PARTICIPATION_HYBRID,      'Hybride (présentiel + en ligne)'),
    ]

    # ── Identification ──
    id   = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=255, unique=True, blank=True)

    # ── Infos principales ──
    title       = models.CharField(max_length=300, verbose_name='Titre')
    description = models.TextField(verbose_name='Description scientifique')
    event_type  = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_WEBINAR, verbose_name='Type')
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PUBLISHED, verbose_name='Statut')

    # ── Dates ──
    start_datetime = models.DateTimeField(verbose_name='Date et heure de début')
    end_datetime   = models.DateTimeField(verbose_name='Date et heure de fin')

    # ── Mode de participation global ──
    participation_mode = models.CharField(
        max_length=20,
        choices=PARTICIPATION_CHOICES,
        default=PARTICIPATION_ONLINE_ONLY,
        verbose_name='Mode de participation',
    )

    # ── Capacité & accès PRÉSENTIEL ──
    max_onsite = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Nombre max de places en présentiel',
        help_text='Laisser vide pour illimité',
    )
    access_onsite = models.CharField(
        max_length=20, choices=ACCESS_CHOICES,
        default=ACCESS_DIRECT,
        verbose_name="Mode d'accès présentiel",
    )
    auto_accept_onsite = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Accepter automatiquement les N premiers (présentiel)',
    )

    # ── Capacité & accès EN LIGNE ──
    max_online = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Nombre max de places en ligne',
        help_text='Laisser vide pour illimité',
    )
    access_online = models.CharField(
        max_length=20, choices=ACCESS_CHOICES,
        default=ACCESS_DIRECT,
        verbose_name="Mode d'accès en ligne",
    )
    auto_accept_online = models.PositiveIntegerField(
        null=True, blank=True,
        verbose_name='Accepter automatiquement les N premiers (en ligne)',
    )

    # ── Champs legacy ──
    is_capacity_limited = models.BooleanField(default=False, verbose_name='Places limitées (legacy)')
    max_participants    = models.PositiveIntegerField(null=True, blank=True, verbose_name='Nombre max (legacy)')
    access_mode         = models.CharField(
        max_length=20, choices=ACCESS_CHOICES,
        default=ACCESS_DIRECT,
        verbose_name="Mode d'accès (legacy)",
    )

    # ── Lieu ──
    location = models.ForeignKey(
        Location, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='events',
    )

    # ── Organisateurs & intervenants ──
    organizer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name='organized_events',
        verbose_name='Organisateur principal',
    )
    speakers = models.ManyToManyField(
        Organizer, blank=True,
        related_name='speaking_events',
        verbose_name='Intervenants',
    )

    # ── Médias ──
    banner = models.ImageField(
        upload_to='events/banners/', blank=True, null=True,
        verbose_name='Affiche / Bannière',
    )
    program_pdf = models.FileField(
        upload_to='programs/', null=True, blank=True,
        verbose_name='Programme PDF',
    )
    registration_qr = models.ImageField(
        upload_to='events/qrcodes/', null=True, blank=True,
        verbose_name='QR code inscription',
    )

    # ── Google Calendar ──
    google_calendar_event_id = models.CharField(max_length=500, blank=True, null=True)

    # ── Timestamps ──
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug      = base_slug
            counter   = 1
            while Event.objects.filter(slug=slug).exists():
                slug    = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('events:detail', kwargs={'slug': self.slug})

    def get_registration_url(self):
        return reverse('registrations:register', kwargs={'slug': self.slug})

    # ── Properties générales ──
    @property
    def is_upcoming(self):
        return self.start_datetime > timezone.now()

    @property
    def is_ongoing(self):
        return self.start_datetime <= timezone.now() <= self.end_datetime

    @property
    def is_finished(self):
        return self.end_datetime < timezone.now()

    @property
    def is_multiday(self):
        return self.start_datetime.date() != self.end_datetime.date()

    # ── Properties PRÉSENTIEL ──
    @property
    def accepted_onsite(self):
        return self.registrations.filter(
            status='accepte',
            participation_type__in=['onsite', 'both'],
        ).count()

    @property
    def spots_remaining_onsite(self):
        if self.max_onsite is None:
            return None
        return max(0, self.max_onsite - self.accepted_onsite)

    @property
    def is_full_onsite(self):
        if self.max_onsite is None:
            return False
        return self.spots_remaining_onsite == 0

    # ── Properties EN LIGNE ──
    @property
    def accepted_online(self):
        return self.registrations.filter(
            status='accepte',
            participation_type__in=['online', 'both'],
        ).count()

    @property
    def spots_remaining_online(self):
        if self.max_online is None:
            return None
        return max(0, self.max_online - self.accepted_online)

    @property
    def is_full_online(self):
        if self.max_online is None:
            return False
        return self.spots_remaining_online == 0

    # ── Properties legacy ──
    @property
    def spots_remaining(self):
        if not self.is_capacity_limited:
            return None
        accepted = self.registrations.filter(status='accepte').count()
        return max(0, self.max_participants - accepted)

    @property
    def is_full(self):
        if not self.is_capacity_limited:
            return False
        return self.spots_remaining == 0

    @property
    def total_registrations(self):
        return self.registrations.count()

    @property
    def accepted_registrations(self):
        return self.registrations.filter(status='accepte').count()

    def __str__(self):
        return self.title

    class Meta:
        verbose_name        = 'Événement'
        verbose_name_plural = 'Événements'
        ordering            = ['-start_datetime']


class EventDay(models.Model):
    event       = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='days')
    date        = models.DateField(verbose_name='Date')
    title       = models.CharField(max_length=200, blank=True, verbose_name='Titre du jour')
    description = models.TextField(blank=True, verbose_name='Description du jour')
    order       = models.PositiveSmallIntegerField(default=1, verbose_name='Ordre')

    def __str__(self):
        return f"{self.event.title} — {self.date.strftime('%d/%m/%Y')} ({self.title})"

    class Meta:
        verbose_name        = "Jour d'événement"
        verbose_name_plural = "Jours d'événement"
        ordering            = ['date', 'order']
        unique_together     = ['event', 'date']


class Session(models.Model):
    SESSION_MODE_ONSITE  = 'onsite'
    SESSION_MODE_ONLINE  = 'online'
    SESSION_MODE_BOTH    = 'both'
    SESSION_MODE_CHOICES = [
        (SESSION_MODE_ONSITE, 'Présentiel'),
        (SESSION_MODE_ONLINE, 'En ligne'),
        (SESSION_MODE_BOTH,   'Les deux'),
    ]

    day           = models.ForeignKey(EventDay, on_delete=models.CASCADE, related_name='sessions')
    start_time    = models.TimeField(verbose_name='Heure de début')
    end_time      = models.TimeField(verbose_name='Heure de fin')
    title         = models.CharField(max_length=300, verbose_name='Titre de la session')
    description   = models.TextField(blank=True, verbose_name='Description')
    speaker       = models.ForeignKey(
        Organizer, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='sessions',
        verbose_name='Intervenant',
    )
    location_note = models.CharField(max_length=200, blank=True, verbose_name='Lieu / Salle')
    mode          = models.CharField(
        max_length=10, choices=SESSION_MODE_CHOICES,
        default=SESSION_MODE_BOTH,
        verbose_name='Mode de la session',
    )
    order         = models.PositiveSmallIntegerField(default=1, verbose_name='Ordre')

    def __str__(self):
        return f"{self.day.date} {self.start_time:%H:%M} — {self.title}"

    class Meta:
        verbose_name        = 'Session'
        verbose_name_plural = 'Sessions'
        ordering            = ['day__date', 'start_time', 'order']