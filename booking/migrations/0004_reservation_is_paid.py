

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0003_room_is_available_alter_hotelinfo_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
    ]
