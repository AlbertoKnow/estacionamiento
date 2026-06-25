import datetime
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spaces', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='campus',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='campus',
            name='direccion',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterModelOptions(
            name='campus',
            options={
                'ordering': ['nombre'],
                'verbose_name': 'Campus',
                'verbose_name_plural': 'Campus',
            },
        ),
        migrations.AlterField(
            model_name='parkinglot',
            name='nombre',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterField(
            model_name='parkinglot',
            name='nivel',
            field=models.IntegerField(
                help_text='Número de nivel (negativo para sótanos, ej: -2)'
            ),
        ),
        migrations.AlterModelOptions(
            name='parkinglot',
            options={
                'ordering': ['campus', 'nivel'],
                'verbose_name': 'Nivel de estacionamiento',
                'verbose_name_plural': 'Niveles de estacionamiento',
            },
        ),
        migrations.AlterUniqueTogether(
            name='parkinglot',
            unique_together={('campus', 'nombre')},
        ),
        migrations.AlterField(
            model_name='parkingspace',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('auto', 'Auto'),
                    ('moto', 'Moto'),
                    ('bicicleta', 'Bicicleta'),
                    ('discapacitado', 'Discapacitado'),
                    ('reservado', 'Reservado'),
                ],
                max_length=15,
            ),
        ),
        migrations.AlterModelOptions(
            name='parkingspace',
            options={
                'ordering': ['lot', 'numero'],
                'verbose_name': 'Espacio de estacionamiento',
                'verbose_name_plural': 'Espacios de estacionamiento',
            },
        ),
    ]
