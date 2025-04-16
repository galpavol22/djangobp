

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='reservation',
            name='created_at',
        ),
        migrations.RemoveField(
            model_name='reservation',
            name='guests',
        ),
        migrations.AddField(
            model_name='reservation',
            name='total_price',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=8),
            preserve_default=False,
        ),
    ]
