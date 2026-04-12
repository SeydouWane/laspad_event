# -*- coding: utf-8 -*-
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='participation_mode',
            field=models.CharField(
                choices=[
                    ('onsite_only', 'Présentiel uniquement'),
                    ('online_only', 'En ligne uniquement'),
                    ('hybrid', 'Hybride (présentiel + en ligne)'),
                ],
                default='online_only',
                max_length=20,
                verbose_name='Mode de participation',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='max_onsite',
            field=models.PositiveIntegerField(
                blank=True, null=True,
                verbose_name='Nombre max de places en présentiel',
                help_text='Laisser vide pour illimité',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='access_onsite',
            field=models.CharField(
                choices=[('direct', 'Inscription directe'), ('validation', 'Avec validation')],
                default='direct',
                max_length=20,
                verbose_name="Mode d'accès présentiel",
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='auto_accept_onsite',
            field=models.PositiveIntegerField(
                blank=True, null=True,
                verbose_name='Accepter automatiquement les N premiers (présentiel)',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='max_online',
            field=models.PositiveIntegerField(
                blank=True, null=True,
                verbose_name='Nombre max de places en ligne',
                help_text='Laisser vide pour illimité',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='access_online',
            field=models.CharField(
                choices=[('direct', 'Inscription directe'), ('validation', 'Avec validation')],
                default='direct',
                max_length=20,
                verbose_name="Mode d'accès en ligne",
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='auto_accept_online',
            field=models.PositiveIntegerField(
                blank=True, null=True,
                verbose_name='Accepter automatiquement les N premiers (en ligne)',
            ),
        ),
        migrations.CreateModel(
            name='EventDay',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Date')),
                ('title', models.CharField(blank=True, max_length=200, verbose_name='Titre du jour')),
                ('description', models.TextField(blank=True, verbose_name='Description du jour')),
                ('order', models.PositiveSmallIntegerField(default=1, verbose_name='Ordre')),
                ('event', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='days',
                    to='events.event',
                )),
            ],
            options={
                'verbose_name': "Jour d'événement",
                'verbose_name_plural': "Jours d'événement",
                'ordering': ['date', 'order'],
                'unique_together': {('event', 'date')},
            },
        ),
        migrations.CreateModel(
            name='Session',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_time', models.TimeField(verbose_name='Heure de début')),
                ('end_time', models.TimeField(verbose_name='Heure de fin')),
                ('title', models.CharField(max_length=300, verbose_name='Titre de la session')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('location_note', models.CharField(blank=True, max_length=200, verbose_name='Lieu / Salle')),
                ('mode', models.CharField(
                    choices=[
                        ('onsite', 'Présentiel'),
                        ('online', 'En ligne'),
                        ('both', 'Les deux'),
                    ],
                    default='both',
                    max_length=10,
                    verbose_name='Mode de la session',
                )),
                ('order', models.PositiveSmallIntegerField(default=1, verbose_name='Ordre')),
                ('day', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sessions',
                    to='events.eventday',
                )),
                ('speaker', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='sessions',
                    to='events.organizer',
                )),
            ],
            options={
                'verbose_name': 'Session',
                'verbose_name_plural': 'Sessions',
                'ordering': ['day__date', 'start_time', 'order'],
            },
        ),
    ]