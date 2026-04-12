from django.db import models
from django.utils import timezone
import uuid


class Participant(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name  = models.CharField(max_length=100, verbose_name='Prénom')
    last_name   = models.CharField(max_length=100, verbose_name='Nom')
    email       = models.EmailField(unique=True, verbose_name='Email')
    institution = models.CharField(max_length=200, verbose_name='Institution / Organisation')
    role        = models.CharField(max_length=150, verbose_name='Fonction / Poste')
    phone       = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    newsletter  = models.BooleanField(default=False, verbose_name='Abonné aux actualités LASPAD')
    created_at  = models.DateTimeField(auto_now_add=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    class Meta:
        verbose_name        = 'Participant'
        verbose_name_plural = 'Participants'
        ordering            = ['last_name', 'first_name']


class Registration(models.Model):
    STATUS_PENDING  = 'en_attente'
    STATUS_ACCEPTED = 'accepte'
    STATUS_REFUSED  = 'refuse'
    STATUS_CHOICES  = [
        (STATUS_PENDING,  'En attente'),
        (STATUS_ACCEPTED, 'Accepté'),
        (STATUS_REFUSED,  'Refusé'),
    ]

    # ── Mode de participation ──────────────────────────────────────
    PARTICIPATION_ONSITE = 'onsite'
    PARTICIPATION_ONLINE = 'online'
    PARTICIPATION_BOTH   = 'both'
    PARTICIPATION_CHOICES = [
        (PARTICIPATION_ONSITE, 'Présentiel'),
        (PARTICIPATION_ONLINE, 'En ligne'),
        (PARTICIPATION_BOTH,   'Les deux (présentiel + en ligne)'),
    ]

    # ── Identifiants ───────────────────────────────────────────────
    id    = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # ── Relations ──────────────────────────────────────────────────
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name='Événement',
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name='Participant',
    )

    # ── Statut & mode ──────────────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='Statut',
    )
    participation_type = models.CharField(
        max_length=10,
        choices=PARTICIPATION_CHOICES,
        default=PARTICIPATION_ONLINE,
        verbose_name='Mode de participation',
    )

    # ── Contenu ────────────────────────────────────────────────────
    motivation = models.TextField(blank=True, verbose_name='Motivation / Message')

    # ── Présence ───────────────────────────────────────────────────
    attended_onsite = models.BooleanField(
        default=False,
        verbose_name='Présence confirmée (présentiel)',
    )
    attended_online = models.BooleanField(
        default=False,
        verbose_name='Présence confirmée (en ligne)',
    )
    attended_at = models.DateTimeField(
        null=True, blank=True,
        verbose_name='Date/heure de pointage',
    )

    # ── Ticket PDF ─────────────────────────────────────────────────
    ticket_sent = models.BooleanField(
        default=False,
        verbose_name='Ticket PDF envoyé',
    )
    ticket_pdf = models.FileField(
        upload_to='tickets/',
        null=True, blank=True,
        verbose_name='Fichier ticket PDF',
    )
    ticket_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Numéro de ticket',
        help_text='Ex: LASPAD-2026-0001',
    )

    # ── Timestamps ─────────────────────────────────────────────────
    registered_at       = models.DateTimeField(auto_now_add=True, verbose_name="Date d'inscription")
    validated_at        = models.DateTimeField(null=True, blank=True, verbose_name='Date de validation')
    calendar_invite_sent = models.BooleanField(default=False, verbose_name='Invitation calendrier envoyée')
    confirmation_sent   = models.BooleanField(default=False, verbose_name='Email de confirmation envoyé')

    # ──────────────────────────────────────────────────────────────
    def save(self, *args, **kwargs):
        # Génération automatique du numéro de ticket
        if not self.ticket_number and self.status == self.STATUS_ACCEPTED:
            year  = self.registered_at.year if self.registered_at else timezone.now().year
            count = Registration.objects.filter(
                event=self.event,
                status=self.STATUS_ACCEPTED,
            ).count() + 1
            self.ticket_number = f"LASPAD-{year}-{count:04d}"
        super().save(*args, **kwargs)

    def accept(self):
        self.status       = self.STATUS_ACCEPTED
        self.validated_at = timezone.now()
        self.save()

    def refuse(self):
        self.status       = self.STATUS_REFUSED
        self.validated_at = timezone.now()
        self.save()

    def mark_attended_onsite(self):
        """Appelé lors du scan du QR code à l'entrée."""
        self.attended_onsite = True
        self.attended_at     = timezone.now()
        self.save(update_fields=['attended_onsite', 'attended_at'])

    def mark_attended_online(self):
        """Appelé lors de la connexion en ligne."""
        self.attended_online = True
        if not self.attended_at:
            self.attended_at = timezone.now()
        self.save(update_fields=['attended_online', 'attended_at'])

    @property
    def is_onsite(self):
        return self.participation_type in [self.PARTICIPATION_ONSITE, self.PARTICIPATION_BOTH]

    @property
    def is_online(self):
        return self.participation_type in [self.PARTICIPATION_ONLINE, self.PARTICIPATION_BOTH]

    @property
    def needs_ticket(self):
        """Un ticket PDF est nécessaire seulement pour les participants en présentiel."""
        return self.is_onsite and self.status == self.STATUS_ACCEPTED

    def __str__(self):
        return f"{self.participant.full_name} → {self.event.title} [{self.get_participation_type_display()}] ({self.get_status_display()})"

    class Meta:
        verbose_name        = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        ordering            = ['-registered_at']
        # Un participant peut s'inscrire une seule fois par événement
        # (même s'il choisit 'both', c'est 1 seule inscription avec participation_type='both')
        unique_together = ['event', 'participant']