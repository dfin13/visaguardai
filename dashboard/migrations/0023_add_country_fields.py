# Generated migration for adding country_of_origin and country_of_application fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0022_config_stripe_webhook_secret_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='country_of_origin',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='country_of_application',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]

