from django.core.exceptions import ValidationError
from django.db import models
from auditlog.registry import auditlog


class ReservationState(models.TextChoices):
    ACTIVA = 'activa', 'Activa'
    VENCIDA = 'vencida', 'Vencida'
    CANCELADA = 'cancelada', 'Cancelada'


class Reservation(models.Model):
    space = models.ForeignKey(
        'spaces.ParkingSpace', on_delete=models.PROTECT, related_name='reservations'
    )
    reservado_por = models.ForeignKey(
        'users.User', on_delete=models.PROTECT, related_name='reservations_made'
    )
    beneficiario = models.ForeignKey(
        'users.User', on_delete=models.PROTECT,
        null=True, blank=True, related_name='reservations_received',
        help_text='Vacío = reserva para uno mismo.',
    )
    campus = models.ForeignKey(
        'spaces.Campus', on_delete=models.PROTECT, related_name='reservations'
    )
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    motivo = models.CharField(max_length=255)
    estado = models.CharField(
        max_length=15, choices=ReservationState.choices, default=ReservationState.ACTIVA
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservations'
        ordering = ['-inicio']

    def clean(self):
        if self.fin <= self.inicio:
            raise ValidationError('La fecha de fin debe ser posterior al inicio.')
        overlapping = Reservation.objects.filter(
            space=self.space,
            estado=ReservationState.ACTIVA,
            inicio__lt=self.fin,
            fin__gt=self.inicio,
        ).exclude(pk=self.pk)
        if overlapping.exists():
            raise ValidationError('El espacio ya tiene una reserva activa en ese horario.')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.space} — {self.inicio:%Y-%m-%d %H:%M} → {self.fin:%H:%M}'


auditlog.register(Reservation)
