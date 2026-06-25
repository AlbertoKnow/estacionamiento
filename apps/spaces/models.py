from django.db import models
from auditlog.registry import auditlog


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


class Campus(models.Model):
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    horario_operacion = models.JSONField(
        default=dict,
        help_text='Horarios por tipo de día: {lunes_sabado: {inicio, fin}, domingo: {inicio, fin}}'
    )
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'campus'
        verbose_name = 'Campus'
        verbose_name_plural = 'Campus'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class ParkingLot(models.Model):
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='lots')
    nombre = models.CharField(max_length=50)
    nivel = models.IntegerField(help_text='Número de nivel (negativo para sótanos, ej: -2)')

    class Meta:
        db_table = 'parking_lots'
        verbose_name = 'Nivel de estacionamiento'
        verbose_name_plural = 'Niveles de estacionamiento'
        unique_together = ('campus', 'nombre')
        ordering = ['campus', 'nivel']

    def __str__(self):
        return f'{self.campus.nombre} — {self.nombre}'


class ParkingSpace(models.Model):
    lot = models.ForeignKey(ParkingLot, on_delete=models.CASCADE, related_name='spaces')
    numero = models.CharField(max_length=10, help_text='Ej: A-01, MOTO-05')
    tipo = models.CharField(max_length=15, choices=SpaceType.choices)
    estado = models.CharField(
        max_length=15, choices=SpaceState.choices, default=SpaceState.LIBRE
    )

    class Meta:
        db_table = 'parking_spaces'
        verbose_name = 'Espacio de estacionamiento'
        verbose_name_plural = 'Espacios de estacionamiento'
        unique_together = ('lot', 'numero')
        ordering = ['lot', 'numero']

    def __str__(self):
        return f'{self.numero} ({self.lot.nombre})'


auditlog.register(Campus)
auditlog.register(ParkingSpace)
