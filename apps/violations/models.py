from django.db import models
from django.utils import timezone
from auditlog.registry import auditlog


class ViolationLevel(models.TextChoices):
    LEVE = 'leve', 'Leve'
    GRAVE = 'grave', 'Grave'
    MUY_GRAVE = 'muy_grave', 'Muy Grave'


class ViolationState(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente'
    CONFIRMADA = 'confirmada', 'Confirmada'
    ANULADA = 'anulada', 'Anulada'
    APELADA = 'apelada', 'Apelada'


class SanctionType(models.TextChoices):
    ADVERTENCIA = 'advertencia', 'Advertencia (email)'
    SUSPENSION_TEMPORAL = 'suspension_temporal', 'Suspensión temporal'
    SUSPENSION_DEFINITIVA = 'suspension_definitiva', 'Suspensión definitiva'


class SanctionState(models.TextChoices):
    ACTIVA = 'activa', 'Activa'
    CUMPLIDA = 'cumplida', 'Cumplida'
    ANULADA = 'anulada', 'Anulada'
    APELADA = 'apelada', 'Apelada'


class ViolationType(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    descripcion = models.TextField()
    nivel = models.CharField(max_length=15, choices=ViolationLevel.choices)

    class Meta:
        db_table = 'violation_types'
        ordering = ['nivel', 'codigo']

    def __str__(self):
        return f'[{self.nivel.upper()}] {self.codigo}'


class SanctionRule(models.Model):
    nivel_falta = models.CharField(max_length=15, choices=ViolationLevel.choices)
    numero_reincidencia = models.PositiveSmallIntegerField(
        help_text='1 = primera vez, 2 = segunda vez, 3 = tercera vez'
    )
    tipo_sancion = models.CharField(max_length=30, choices=SanctionType.choices)
    duracion_meses = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text='Null para advertencia o suspensión definitiva'
    )

    class Meta:
        db_table = 'sanction_rules'
        unique_together = ('nivel_falta', 'numero_reincidencia')
        ordering = ['nivel_falta', 'numero_reincidencia']

    def __str__(self):
        return f'{self.nivel_falta} #{self.numero_reincidencia} → {self.tipo_sancion}'


class Violation(models.Model):
    user = models.ForeignKey(
        'users.User', on_delete=models.PROTECT, related_name='violations'
    )
    vehicle = models.ForeignKey(
        'users.Vehicle', on_delete=models.PROTECT,
        null=True, blank=True, related_name='violations'
    )
    campus = models.ForeignKey(
        'spaces.Campus', on_delete=models.PROTECT, related_name='violations'
    )
    tipo_falta = models.ForeignKey(
        ViolationType, on_delete=models.PROTECT, related_name='violations'
    )
    descripcion = models.TextField()
    evidencia_foto = models.ImageField(upload_to='violations/', null=True, blank=True)
    registrado_por = models.ForeignKey(
        'users.User', on_delete=models.PROTECT, related_name='registered_violations'
    )
    access_record = models.ForeignKey(
        'access.AccessRecord', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='violations'
    )
    fecha = models.DateTimeField(default=timezone.now)
    estado = models.CharField(
        max_length=15, choices=ViolationState.choices, default=ViolationState.PENDIENTE
    )

    class Meta:
        db_table = 'violations'
        ordering = ['-fecha']

    def __str__(self):
        return f'{self.user.codigo_institucional} — {self.tipo_falta.codigo} — {self.fecha:%Y-%m-%d}'


class Sanction(models.Model):
    user = models.ForeignKey(
        'users.User', on_delete=models.PROTECT, related_name='sanctions'
    )
    violation = models.OneToOneField(
        Violation, on_delete=models.PROTECT, related_name='sanction'
    )
    tipo = models.CharField(max_length=30, choices=SanctionType.choices)
    inicio = models.DateField(null=True, blank=True)
    fin = models.DateField(null=True, blank=True, help_text='Null para suspensión definitiva')
    aplicada_por = models.ForeignKey(
        'users.User', on_delete=models.PROTECT, related_name='applied_sanctions'
    )
    estado = models.CharField(
        max_length=15, choices=SanctionState.choices, default=SanctionState.ACTIVA
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sanctions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.codigo_institucional} — {self.tipo} — {self.estado}'


auditlog.register(Violation)
auditlog.register(Sanction)
