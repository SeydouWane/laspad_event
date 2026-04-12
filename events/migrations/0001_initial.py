from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mode', models.CharField(choices=[('online', 'En ligne'), ('onsite', 'Présentiel'), ('hybrid', 'Hybride')], default='online', max_length=10, verbose_name='Mode')),
                ('platform', models.CharField(blank=True, choices=[('meet', 'Google Meet'), ('zoom', 'Zoom'), ('youtube', 'YouTube Live'), ('other', 'Autre')], max_length=10, null=True, verbose_name='Plateforme')),
                ('online_link', models.URLField(blank=True, null=True, verbose_name='Lien de diffusion')),
                ('address', models.CharField(blank=True, max_length=500, verbose_name='Adresse')),
                ('city', models.CharField(blank=True, max_length=100, verbose_name='Ville')),
                ('country', models.CharField(default='Sénégal', max_length=100, verbose_name='Pays')),
                ('google_maps_url', models.URLField(blank=True, null=True, verbose_name='Lien Google Maps')),
            ],
            options={'verbose_name': 'Lieu', 'verbose_name_plural': 'Lieux'},
        ),
        migrations.CreateModel(
            name='Organizer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bio', models.TextField(blank=True)),
                ('institution', models.CharField(blank=True, max_length=200)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='organizers/')),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='organizer_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={'verbose_name': 'Organisateur', 'verbose_name_plural': 'Organisateurs'},
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('slug', models.SlugField(blank=True, max_length=255, unique=True)),
                ('title', models.CharField(max_length=300, verbose_name='Titre')),
                ('description', models.TextField(verbose_name='Description scientifique')),
                ('event_type', models.CharField(choices=[('webinaire', 'Webinaire'), ('conference', 'Conférence'), ('atelier', 'Atelier'), ('seminaire', 'Séminaire'), ('autre', 'Autre')], default='webinaire', max_length=20, verbose_name='Type')),
                ('status', models.CharField(choices=[('brouillon', 'Brouillon'), ('publie', 'Publié'), ('annule', 'Annulé'), ('termine', 'Terminé')], default='publie', max_length=20, verbose_name='Statut')),
                ('start_datetime', models.DateTimeField(verbose_name='Date et heure de début')),
                ('end_datetime', models.DateTimeField(verbose_name='Date et heure de fin')),
                ('is_capacity_limited', models.BooleanField(default=False, verbose_name='Places limitées')),
                ('max_participants', models.PositiveIntegerField(blank=True, null=True, verbose_name='Nombre max de participants')),
                ('access_mode', models.CharField(choices=[('direct', 'Inscription directe'), ('validation', 'Avec validation')], default='direct', max_length=20, verbose_name="Mode d'accès")),
                ('banner', models.ImageField(blank=True, null=True, upload_to='events/banners/', verbose_name='Affiche / Bannière')),
                ('google_calendar_event_id', models.CharField(blank=True, max_length=500, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='events', to='events.location')),
                ('organizer', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organized_events', to=settings.AUTH_USER_MODEL, verbose_name='Organisateur principal')),
                ('speakers', models.ManyToManyField(blank=True, related_name='speaking_events', to='events.organizer', verbose_name='Intervenants')),
            ],
            options={'verbose_name': 'Événement', 'verbose_name_plural': 'Événements', 'ordering': ['-start_datetime']},
        ),
    ]
