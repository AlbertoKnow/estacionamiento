from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from auditlog.registry import auditlog


class Role(models.TextChoices):
    RECTOR = 'rector', 'Rector'
    DIRECTOR = 'director', 'Director'
    JEFE_OPERACIONES = 'jefe_operaciones', 'Jefe de Operaciones'
    JEFE_SEGURIDAD = 'jefe_seguridad', 'Jefe de Seguridad'
    ASISTENTE_OPERACIONES = 'asistente_operaciones', 'Asistente de Operaciones'
    AGENTE_SEGURIDAD = 'agente_seguridad', 'Agente de Seguridad'
    ADMINISTRATIVO = 'administrativo', 'Administrativo'
    ACADEMICO = 'academico', 'Académico'
    ALUMNO = 'alumno', 'Alumno'


class UserState(models.TextChoices):
    ACTIVO = 'activo', 'Activo'
    SUSPENDIDO = 'suspendido', 'Suspendido'
    INACTIVO = 'inactivo', 'Inactivo'


class UserManager(BaseUserManager):
    def create_user(self, codigo_institucional, email, password=None, **extra_fields):
        if not codigo_institucional:
            raise ValueError('El código institucional es obligatorio')
        email = self.normalize_email(email)
        user = self.model(
            codigo_institucional=codigo_institucional,
            email=email,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, codigo_institucional, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', Role.RECTOR)
        return self.create_user(codigo_institucional, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    codigo_institucional = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    rol = models.CharField(max_length=30, choices=Role.choices)
    campus_asignado = models.ForeignKey(
        'spaces.Campus',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='users',
    )
    estado = models.CharField(
        max_length=20, choices=UserState.choices, default=UserState.ACTIVO
    )
    suspension_hasta = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'codigo_institucional'
    REQUIRED_FIELDS = ['email', 'nombre', 'apellido', 'rol']

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f'{self.codigo_institucional} — {self.get_full_name()}'

    def get_full_name(self):
        return f'{self.nombre} {self.apellido}'

    def get_short_name(self):
        return self.nombre

    @property
    def is_national_scope(self):
        return self.rol == Role.RECTOR

    @property
    def is_suspended(self):
        from django.utils import timezone
        if self.estado == UserState.SUSPENDIDO:
            if self.suspension_hasta is None:
                return True
            return self.suspension_hasta >= timezone.now().date()
        return False


class VehicleType(models.TextChoices):
    AUTO = 'auto', 'Auto'
    MOTO = 'moto', 'Moto'
    BICICLETA = 'bicicleta', 'Bicicleta'


class Vehicle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    placa = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=15, choices=VehicleType.choices)
    marca = models.CharField(max_length=50, blank=True)
    modelo = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=30, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'vehicles'
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'

    def __str__(self):
        return f'{self.placa} ({self.user.codigo_institucional})'

    def clean(self):
        active_count = Vehicle.objects.filter(
            user=self.user, activo=True
        ).exclude(pk=self.pk).count()
        if active_count >= 2:
            raise ValidationError(
                {'user': 'Un usuario puede tener máximo 2 vehículos activos.'}
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


auditlog.register(User)
auditlog.register(Vehicle)
