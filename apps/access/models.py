from django.db import models
from django.utils import timezone


class AccessState(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    COMPLETADO = 'completado', 'Completado'


class AccessRecord(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.PROTECT, related_name='access_records')
    vehicle = models.ForeignKey(
        'users.Vehicle', on_delete=models.PROTECT, null=True, blank=True, related_name='access_records'
    )
    campus = models.ForeignKey('spaces.Campus', on_delete=models.PROTECT, related_name='access_records')
    space = models.ForeignKey(
        'spaces.ParkingSpace', on_delete=models.PROTECT, null=True, blank=True, related_name='access_records'
    )
    entrada_at = models.DateTimeField(default=timezone.now)
    salida_at = models.DateTimeField(null=True, blank=True)
    registrado_por = models.ForeignKey(
        'users.User', on_delete=models.PROTECT, related_name='registered_access_records'
    )
    estado = models.CharField(max_length=15, choices=AccessState.choices, default=AccessState.ACTIVO)

    class Meta:
        db_table = 'access_records'
        ordering = ['-entrada_at']

    def __str__(self):
        return f'{self.user.codigo_institucional} — {self.entrada_at:%Y-%m-%d %H:%M}'


class UsedQRToken(models.Model):
    jti = models.CharField(max_length=64, unique=True)
    user_id = models.IntegerField()
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'used_qr_tokens'

    @classmethod
    def is_used(cls, jti: str) -> bool:
        return cls.objects.filter(jti=jti).exists()

    @classmethod
    def mark_used(cls, jti: str, user_id: int):
        cls.objects.create(jti=jti, user_id=user_id)
