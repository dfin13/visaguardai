# Generated manually to fix signup issue
# The username field needs to allow blank values to prevent IntegrityError

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0023_add_country_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='username',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
    ]

