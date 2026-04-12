from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registrations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='newsletter',
            field=models.BooleanField(default=False, verbose_name='Abonné aux actualités LASPAD'),
        ),
    ]