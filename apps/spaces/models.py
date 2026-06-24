from django.db import models


class Campus(models.Model):
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=255)
    horario_operacion = models.JSONField(default=dict)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'campus'
        verbose_name = 'Campus'
        verbose_name_plural = 'Campus'

    def __str__(self):
        return self.nombre


class SpaceType(models.TextChoices):
    AUTO = 'auto', 'Auto'
    MOTO = 'moto', 'Moto'
    BICICLETA = 'bicicleta', 'Bicicleta'
    DISCAPACITADO = 'discapacitado', 'Discapacitado'
    RESERVADO = 'reservado', 'Reservado'


class SpaceState(models.TextChoices):
    LIBRE = 'libre', 'Libre'
    OCUPADO = 'ocupado', 'Ocupado'
    RESERVADO = 'reservado', 'Reservado'
    MANTENIMIENTO = 'mantenimiento', 'Mantenimiento'


class ParkingLot(models.Model):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='lots')
    nombre = models.CharField(max_length=100)
    nivel = models.IntegerField(help_text='Negativo para sótanos, e.g. -2 para Sótano 2')

    class Meta:
        db_table = 'parking_lots'
        ordering = ['nivel']

    def __str__(self):
        return f'{self.campus.nombre} — {self.nombre}'


class ParkingSpace(models.Model):
    lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='spaces')
    numero = models.CharField(max_length=10, help_text='e.g. A-01')
    tipo = models.CharField(max_length=15, choices=SpaceType.choices, default=SpaceType.AUTO)
    estado = models.CharField(max_length=15, choices=SpaceState.choices, default=SpaceState.LIBRE)

    class Meta:
        db_table = 'parking_spaces'
        unique_together = ('lot', 'numero')

    def __str__(self):
        return f'{self.lot.nombre} — {self.numero} ({self.estado})'
