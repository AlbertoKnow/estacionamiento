import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('access', '0002_initial'),
        ('spaces', '0002_update_spaces_models'),
        ('users', '0003_resolve_campus_fk'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='accessrecord',
            name='vehicle',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='access_records',
                to='users.vehicle',
            ),
        ),
        migrations.AlterField(
            model_name='accessrecord',
            name='space',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='access_records',
                to='spaces.parkingspace',
            ),
        ),
        migrations.AlterField(
            model_name='accessrecord',
            name='registrado_por',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='registered_entries',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterModelOptions(
            name='accessrecord',
            options={
                'ordering': ['-entrada_at'],
                'verbose_name': 'Registro de acceso',
                'verbose_name_plural': 'Registros de acceso',
            },
        ),
    ]
