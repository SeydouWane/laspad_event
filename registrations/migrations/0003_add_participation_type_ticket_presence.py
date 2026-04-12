# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0002_participant_newsletter'),
    ]

    operations = [
        migrations.AddField(
            model_name='registration',
            name='attended_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Date/heure de pointage'),
        ),
        migrations.AddField(
            model_name='registration',
            name='attended_online',
            field=models.BooleanField(default=False, verbose_name='Présence confirmée (en ligne)'),
        ),
        migrations.AddField(
            model_name='registration',
            name='attended_onsite',
            field=models.BooleanField(default=False, verbose_name='Présence confirmée (présentiel)'),
        ),
        migrations.AddField(
            model_name='registration',
            name='participation_type',
            field=models.CharField(
                choices=[
                    ('onsite', 'Présentiel'),
                    ('online', 'En ligne'),
                    ('both', 'Les deux (présentiel + en ligne)'),
                ],
                default='online',
                max_length=10,
                verbose_name='Mode de participation',
            ),
        ),
        migrations.AddField(
            model_name='registration',
            name='ticket_number',
            field=models.CharField(
                blank=True,
                help_text='Ex: LASPAD-2026-0001',
                max_length=50,
                verbose_name='Numéro de ticket',
            ),
        ),
        migrations.AddField(
            model_name='registration',
            name='ticket_pdf',
            field=models.FileField(
                blank=True, null=True,
                upload_to='tickets/',
                verbose_name='Fichier ticket PDF',
            ),
        ),
        migrations.AddField(
            model_name='registration',
            name='ticket_sent',
            field=models.BooleanField(default=False, verbose_name='Ticket PDF envoyé'),
        ),
    ]