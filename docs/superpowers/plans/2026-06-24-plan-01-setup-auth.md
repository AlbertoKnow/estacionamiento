# Plan 01: Setup del proyecto + Módulo Auth/Usuarios

> **Para workers agénticos:** USA el skill superpowers:subagent-driven-development o superpowers:executing-plans para implementar tarea por tarea.

**Goal:** Proyecto Django dockerizado con modelo de usuarios (9 roles), autenticación JWT, permisos por rol y CRUD de usuarios/vehículos filtrado por campus.

**Architecture:** Monolito modular Django. Cada dominio vive en `apps/<dominio>/`. El módulo `users` es la base de la que dependen todos los demás módulos.

**Tech Stack:** Python 3.12, Django 5.x, Django REST Framework 3.15, drf-spectacular, djangorestframework-simplejwt, django-auditlog, PostgreSQL 16, Docker, pytest-django, openpyxl.

## Global Constraints

- Python 3.12+, Django 5.x, DRF 3.15+
- Toda variable de entorno sensible va en `.env` (nunca en código)
- Todos los endpoints bajo `/api/v1/`
- Aislamiento por campus: cada queryset filtra por `campus_id` del usuario autenticado, excepto Rector (ve todo)
- Tests con pytest-django; base de datos de test real (PostgreSQL), sin mocks de BD
- Commits frecuentes, un commit por tarea completada
- Idioma del código: inglés; mensajes de la API: español

---

## Estructura de archivos

```
estacionamiento/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
├── pytest.ini
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   └── development.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    └── users/
        ├── __init__.py
        ├── models.py          # User, Vehicle
        ├── serializers.py     # UserSerializer, VehicleSerializer, LoginSerializer
        ├── views.py           # Auth views + User CRUD + Vehicle CRUD
        ├── urls.py
        ├── permissions.py     # Clases de permiso por rol
        ├── admin.py
        ├── fixtures/
        │   └── initial_campus.json
        └── tests/
            ├── __init__.py
            ├── conftest.py
            ├── test_models.py
            └── test_views.py
```

---

## Tarea 1: Scaffolding del proyecto (Docker + Django + PostgreSQL)

**Archivos:**
- Crear: `Dockerfile`
- Crear: `docker-compose.yml`
- Crear: `requirements.txt`
- Crear: `.env.example`
- Crear: `config/settings/base.py`
- Crear: `config/settings/development.py`
- Crear: `config/urls.py`
- Crear: `pytest.ini`

**Interfaces:**
- Produce: Proyecto Django corriendo en `http://localhost:8000` con conexión a PostgreSQL verificada

- [ ] **Paso 1: Crear `requirements.txt`**

```
Django==5.1.*
djangorestframework==3.15.*
drf-spectacular==0.27.*
djangorestframework-simplejwt==5.3.*
django-auditlog==3.0.*
psycopg2-binary==2.9.*
python-decouple==3.8.*
openpyxl==3.1.*
reportlab==4.2.*
pytest-django==4.8.*
pytest==8.2.*
factory-boy==3.3.*
Pillow==10.4.*
```

- [ ] **Paso 2: Crear `Dockerfile`**

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

- [ ] **Paso 3: Crear `docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

volumes:
  postgres_data:
```

- [ ] **Paso 4: Crear `.env.example`**

```
SECRET_KEY=change-me-in-production
DEBUG=True
DB_NAME=estacionamiento
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
ALLOWED_HOSTS=localhost,127.0.0.1
```

Copiar a `.env` y completar con valores reales (`.env` en `.gitignore`).

- [ ] **Paso 5: Inicializar el proyecto Django**

```bash
django-admin startproject config .
mkdir -p apps config/settings
touch apps/__init__.py
mv config/settings.py config/settings/base.py
touch config/settings/__init__.py config/settings/development.py
```

- [ ] **Paso 6: Escribir `config/settings/base.py`**

```python
from decouple import config
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'auditlog',
]

LOCAL_APPS = [
    'apps.users',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'auditlog.middleware.AuditlogMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}

AUTH_USER_MODEL = 'users.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Sistema de Estacionamiento UTP',
    'DESCRIPTION': 'API para gestión de estacionamientos UTP',
    'VERSION': '1.0.0',
}

LANGUAGE_CODE = 'es-pe'
TIME_ZONE = 'America/Lima'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

- [ ] **Paso 7: Escribir `config/settings/development.py`**

```python
from .base import *

DEBUG = True
```

- [ ] **Paso 8: Escribir `config/urls.py`**

```python
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/', include('apps.users.urls')),
]
```

- [ ] **Paso 9: Escribir `pytest.ini`**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests/test_*.py
python_classes = Test*
python_functions = test_*
```

- [ ] **Paso 10: Levantar servicios y verificar**

```bash
docker-compose up -d db
docker-compose build web
docker-compose run --rm web python manage.py check
```

Resultado esperado: `System check identified no issues (0 silenced).`

- [ ] **Paso 11: Commit**

```bash
git add .
git commit -m "feat: scaffold Django project with Docker and PostgreSQL"
```

---

## Tarea 2: Modelo User y Vehicle

**Archivos:**
- Crear: `apps/users/__init__.py`
- Crear: `apps/users/models.py`
- Crear: `apps/users/admin.py`
- Crear: `apps/users/tests/__init__.py`
- Crear: `apps/users/tests/conftest.py`
- Crear: `apps/users/tests/test_models.py`

**Interfaces:**
- Produce: `User` con campos `codigo_institucional`, `rol`, `campus_asignado`, `estado`, `suspension_hasta`
- Produce: `Vehicle` con FK a `User`, máx 2 por usuario validado en model
- Produce: constantes `Role` y `UserState` usables en el resto de módulos

- [ ] **Paso 1: Escribir el test del modelo User**

```python
# apps/users/tests/test_models.py
import pytest
from django.core.exceptions import ValidationError
from apps.users.models import User, Vehicle, Role, UserState

@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_required_fields(self):
        user = User.objects.create_user(
            codigo_institucional='U001',
            email='u001@utp.edu.pe',
            password='testpass123',
            nombre='Juan',
            apellido='Pérez',
            rol=Role.ALUMNO,
        )
        assert user.codigo_institucional == 'U001'
        assert user.rol == Role.ALUMNO
        assert user.estado == UserState.ACTIVO
        assert user.campus_asignado is None

    def test_codigo_institucional_is_unique(self):
        User.objects.create_user(
            codigo_institucional='U002',
            email='u002@utp.edu.pe',
            password='testpass123',
            nombre='Ana',
            apellido='García',
            rol=Role.ALUMNO,
        )
        with pytest.raises(Exception):
            User.objects.create_user(
                codigo_institucional='U002',
                email='u002b@utp.edu.pe',
                password='testpass123',
                nombre='Ana',
                apellido='García',
                rol=Role.ALUMNO,
            )

    def test_rector_has_no_campus(self):
        rector = User.objects.create_user(
            codigo_institucional='R001',
            email='rector@utp.edu.pe',
            password='testpass123',
            nombre='Carlos',
            apellido='Rector',
            rol=Role.RECTOR,
        )
        assert rector.campus_asignado is None

@pytest.mark.django_db
class TestVehicleModel:
    def test_max_two_vehicles_per_user(self, user_alumno):
        Vehicle.objects.create(
            user=user_alumno, placa='ABC-123',
            tipo='auto', marca='Toyota', modelo='Corolla', color='Blanco',
        )
        Vehicle.objects.create(
            user=user_alumno, placa='XYZ-789',
            tipo='auto', marca='Honda', modelo='Civic', color='Negro',
        )
        with pytest.raises(ValidationError, match='máximo'):
            vehicle = Vehicle(
                user=user_alumno, placa='DEF-456',
                tipo='moto', marca='Yamaha', modelo='FZ', color='Rojo',
            )
            vehicle.full_clean()

    def test_placa_is_unique(self, user_alumno, user_academico):
        Vehicle.objects.create(
            user=user_alumno, placa='ABC-123',
            tipo='auto', marca='Toyota', modelo='Corolla', color='Blanco',
        )
        with pytest.raises(Exception):
            Vehicle.objects.create(
                user=user_academico, placa='ABC-123',
                tipo='auto', marca='Honda', modelo='Civic', color='Negro',
            )
```

- [ ] **Paso 2: Crear `apps/users/tests/conftest.py`**

```python
import pytest
from apps.users.models import User, Role

@pytest.fixture
def user_alumno(db):
    return User.objects.create_user(
        codigo_institucional='ALU001',
        email='alu001@utp.edu.pe',
        password='testpass123',
        nombre='Luis',
        apellido='Torres',
        rol=Role.ALUMNO,
    )

@pytest.fixture
def user_academico(db):
    return User.objects.create_user(
        codigo_institucional='ACA001',
        email='aca001@utp.edu.pe',
        password='testpass123',
        nombre='María',
        apellido='López',
        rol=Role.ACADEMICO,
    )

@pytest.fixture
def user_agente(db):
    return User.objects.create_user(
        codigo_institucional='AGT001',
        email='agt001@utp.edu.pe',
        password='testpass123',
        nombre='Pedro',
        apellido='Quispe',
        rol=Role.AGENTE_SEGURIDAD,
    )

@pytest.fixture
def user_jefe_operaciones(db):
    return User.objects.create_user(
        codigo_institucional='JOP001',
        email='jop001@utp.edu.pe',
        password='testpass123',
        nombre='Sara',
        apellido='Mamani',
        rol=Role.JEFE_OPERACIONES,
    )

@pytest.fixture
def user_rector(db):
    return User.objects.create_user(
        codigo_institucional='REC001',
        email='rector@utp.edu.pe',
        password='testpass123',
        nombre='Alberto',
        apellido='Rector',
        rol=Role.RECTOR,
    )
```

- [ ] **Paso 3: Correr el test para verificar que falla**

```bash
docker-compose run --rm web pytest apps/users/tests/test_models.py -v
```

Resultado esperado: `ImportError` o `ModuleNotFoundError` — el modelo aún no existe.

- [ ] **Paso 4: Escribir `apps/users/models.py`**

```python
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
        null=True, blank=True,
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
    marca = models.CharField(max_length=50)
    modelo = models.CharField(max_length=50)
    color = models.CharField(max_length=30)
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
```

**Nota:** `campus_asignado` referencia `spaces.Campus` que se crea en el Plan 02. Por ahora usa `'spaces.Campus'` como string para evitar import circular — Django lo resuelve en tiempo de migración.

- [ ] **Paso 5: Escribir `apps/users/admin.py`**

```python
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Vehicle


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('codigo_institucional', 'get_full_name', 'rol', 'estado', 'campus_asignado')
    list_filter = ('rol', 'estado', 'campus_asignado')
    search_fields = ('codigo_institucional', 'nombre', 'apellido', 'email')
    fieldsets = (
        (None, {'fields': ('codigo_institucional', 'email', 'password')}),
        ('Datos personales', {'fields': ('nombre', 'apellido')}),
        ('Rol y campus', {'fields': ('rol', 'campus_asignado', 'estado', 'suspension_hasta')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('codigo_institucional', 'email', 'nombre', 'apellido', 'rol', 'password1', 'password2'),
        }),
    )
    ordering = ('codigo_institucional',)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('placa', 'user', 'tipo', 'activo')
    list_filter = ('tipo', 'activo')
    search_fields = ('placa', 'user__codigo_institucional')
```

- [ ] **Paso 6: Crear migración y aplicar**

```bash
docker-compose run --rm web python manage.py makemigrations users
docker-compose run --rm web python manage.py migrate
```

Resultado esperado: migraciones aplicadas sin error.

- [ ] **Paso 7: Correr tests del modelo**

```bash
docker-compose run --rm web pytest apps/users/tests/test_models.py -v
```

Resultado esperado: todos los tests en PASS.

- [ ] **Paso 8: Commit**

```bash
git add apps/users/
git commit -m "feat: add User and Vehicle models with role system"
```

---

## Tarea 3: Autenticación JWT (login, refresh, logout)

**Archivos:**
- Crear: `apps/users/serializers.py`
- Crear: `apps/users/views.py`
- Crear: `apps/users/urls.py`
- Añadir tests en: `apps/users/tests/test_views.py`

**Interfaces:**
- Produce: `POST /api/v1/auth/login/` → `{access, refresh, user: {id, codigo, nombre, rol, campus_id}}`
- Produce: `POST /api/v1/auth/refresh/` → `{access, refresh}`
- Produce: `POST /api/v1/auth/logout/` → `204 No Content` (blacklist refresh token)

- [ ] **Paso 1: Escribir tests de autenticación**

```python
# apps/users/tests/test_views.py
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.users.models import User, Role

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def alumno_credentials(db):
    user = User.objects.create_user(
        codigo_institucional='ALU001',
        email='alu001@utp.edu.pe',
        password='testpass123',
        nombre='Luis',
        apellido='Torres',
        rol=Role.ALUMNO,
    )
    return user, 'testpass123'

@pytest.mark.django_db
class TestLogin:
    def test_login_with_valid_credentials(self, api_client, alumno_credentials):
        user, password = alumno_credentials
        response = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': user.codigo_institucional,
            'password': password,
        })
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['rol'] == Role.ALUMNO

    def test_login_with_invalid_credentials(self, api_client, alumno_credentials):
        user, _ = alumno_credentials
        response = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': user.codigo_institucional,
            'password': 'wrongpassword',
        })
        assert response.status_code == 401

    def test_login_inactive_user(self, api_client, alumno_credentials):
        user, password = alumno_credentials
        user.is_active = False
        user.save()
        response = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': user.codigo_institucional,
            'password': password,
        })
        assert response.status_code == 401

@pytest.mark.django_db
class TestLogout:
    def test_logout_blacklists_refresh_token(self, api_client, alumno_credentials):
        user, password = alumno_credentials
        login = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': user.codigo_institucional,
            'password': password,
        })
        refresh_token = login.data['refresh']
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = api_client.post('/api/v1/auth/logout/', {'refresh': refresh_token})
        assert response.status_code == 204

        # El refresh token ya no debe funcionar
        response2 = api_client.post('/api/v1/auth/refresh/', {'refresh': refresh_token})
        assert response2.status_code == 401
```

- [ ] **Paso 2: Correr tests para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/users/tests/test_views.py -v
```

Resultado esperado: `FAILED` con `ConnectionError` o `404`.

- [ ] **Paso 3: Escribir `apps/users/serializers.py`**

```python
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Vehicle, Role


class LoginSerializer(serializers.Serializer):
    codigo_institucional = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['codigo_institucional'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Credenciales incorrectas.')
        if not user.is_active:
            raise serializers.ValidationError('Usuario inactivo.')
        attrs['user'] = user
        return attrs


class UserBasicSerializer(serializers.ModelSerializer):
    campus_id = serializers.PrimaryKeyRelatedField(source='campus_asignado', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'codigo_institucional', 'nombre', 'apellido', 'email', 'rol', 'campus_id', 'estado')


class UserSerializer(serializers.ModelSerializer):
    campus_id = serializers.PrimaryKeyRelatedField(source='campus_asignado', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'codigo_institucional', 'email', 'nombre', 'apellido',
            'rol', 'campus_id', 'estado', 'suspension_hasta', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            'codigo_institucional', 'email', 'nombre', 'apellido',
            'rol', 'campus_asignado', 'password',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('id', 'placa', 'tipo', 'marca', 'modelo', 'color', 'activo', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        user = self.context['request'].user
        if not self.instance:  # solo en creación
            active_count = Vehicle.objects.filter(user=user, activo=True).count()
            if active_count >= 2:
                raise serializers.ValidationError('Máximo 2 vehículos por usuario.')
        return attrs

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
```

- [ ] **Paso 4: Escribir `apps/users/views.py` (solo auth)**

```python
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from .serializers import LoginSerializer, UserBasicSerializer


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserBasicSerializer(user).data,
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
        except TokenError:
            pass
        return Response(status=status.HTTP_204_NO_CONTENT)


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            return Response({
                'access': str(token.access_token),
                'refresh': str(token),
            })
        except TokenError:
            return Response(
                {'detail': 'Token inválido o expirado.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
```

- [ ] **Paso 5: Escribir `apps/users/urls.py`**

```python
from django.urls import path
from .views import LoginView, LogoutView, RefreshView

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/refresh/', RefreshView.as_view(), name='auth-refresh'),
]
```

- [ ] **Paso 6: Correr tests**

```bash
docker-compose run --rm web pytest apps/users/tests/test_views.py -v
```

Resultado esperado: todos los tests en PASS.

- [ ] **Paso 7: Commit**

```bash
git add apps/users/
git commit -m "feat: add JWT authentication (login, refresh, logout)"
```

---

## Tarea 4: Clases de permisos por rol

**Archivos:**
- Crear: `apps/users/permissions.py`
- Añadir tests en: `apps/users/tests/test_views.py`

**Interfaces:**
- Produce: clases `IsRector`, `IsDirectorOrAbove`, `IsJefeOperacionesOrAbove`, `IsOperativoOrAbove`, `IsSameUserOrAbove`
- Consumes: `User.rol` (Role enum de Tarea 2)

- [ ] **Paso 1: Escribir tests de permisos**

Añadir al final de `apps/users/tests/test_views.py`:

```python
@pytest.mark.django_db
class TestPermissions:
    def test_alumno_cannot_access_user_list(self, api_client, alumno_credentials):
        user, password = alumno_credentials
        login = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': user.codigo_institucional,
            'password': password,
        })
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = api_client.get('/api/v1/users/')
        assert response.status_code == 403

    def test_unauthenticated_request_is_rejected(self, api_client):
        response = api_client.get('/api/v1/users/')
        assert response.status_code == 401
```

- [ ] **Paso 2: Correr para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/users/tests/test_views.py::TestPermissions -v
```

Resultado esperado: `FAILED` con `404`.

- [ ] **Paso 3: Escribir `apps/users/permissions.py`**

```python
from rest_framework.permissions import BasePermission
from .models import Role

ROLE_HIERARCHY = [
    Role.RECTOR,
    Role.DIRECTOR,
    Role.JEFE_OPERACIONES,
    Role.JEFE_SEGURIDAD,
    Role.ASISTENTE_OPERACIONES,
    Role.AGENTE_SEGURIDAD,
    Role.ADMINISTRATIVO,
    Role.ACADEMICO,
    Role.ALUMNO,
]


def _has_role_or_above(user, min_role: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    try:
        user_index = ROLE_HIERARCHY.index(user.rol)
        min_index = ROLE_HIERARCHY.index(min_role)
        return user_index <= min_index
    except ValueError:
        return False


class IsRector(BasePermission):
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.RECTOR)


class IsDirectorOrAbove(BasePermission):
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.DIRECTOR)


class IsJefeOperacionesOrAbove(BasePermission):
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.JEFE_OPERACIONES)


class IsJefeSeguridad(BasePermission):
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.JEFE_SEGURIDAD)


class IsOperativoOrAbove(BasePermission):
    """Agente de Seguridad, Asistente de Operaciones y superiores."""
    def has_permission(self, request, view):
        return _has_role_or_above(request.user, Role.AGENTE_SEGURIDAD)


class IsUsuarioFinal(BasePermission):
    """Administrativo, Académico, Alumno."""
    FINAL_ROLES = {Role.ADMINISTRATIVO, Role.ACADEMICO, Role.ALUMNO}

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.rol in self.FINAL_ROLES
        )


class IsSameCampusOrAbove(BasePermission):
    """Verifica que el usuario solo acceda a datos de su campus, excepto Rector."""
    def has_object_permission(self, request, view, obj):
        if request.user.rol == Role.RECTOR:
            return True
        obj_campus = getattr(obj, 'campus_asignado', None) or getattr(obj, 'campus', None)
        return obj_campus == request.user.campus_asignado
```

- [ ] **Paso 4: Correr tests**

```bash
docker-compose run --rm web pytest apps/users/tests/test_views.py -v
```

Resultado esperado: todos los tests en PASS (los de permisos necesitan el endpoint de la siguiente tarea — marcarlos como `xfail` si fallan por `404`).

- [ ] **Paso 5: Commit**

```bash
git add apps/users/permissions.py
git commit -m "feat: add role-based permission classes"
```

---

## Tarea 5: CRUD de usuarios y vehículos

**Archivos:**
- Modificar: `apps/users/views.py`
- Modificar: `apps/users/urls.py`
- Añadir tests en: `apps/users/tests/test_views.py`

**Interfaces:**
- Produce: `GET /api/v1/users/` — lista usuarios del campus (Jefe Operaciones+)
- Produce: `POST /api/v1/users/` — crear usuario (Jefe Operaciones+)
- Produce: `GET /api/v1/users/{id}/` — detalle usuario
- Produce: `PATCH /api/v1/users/{id}/` — editar usuario
- Produce: `GET /api/v1/users/me/` — perfil propio (todos los roles)
- Produce: `GET /api/v1/users/{id}/vehicles/` — vehículos del usuario
- Produce: `POST /api/v1/users/{id}/vehicles/` — agregar vehículo
- Consumes: `IsJefeOperacionesOrAbove`, `IsSameCampusOrAbove` de Tarea 4

- [ ] **Paso 1: Escribir tests de CRUD**

Añadir al final de `apps/users/tests/test_views.py`:

```python
@pytest.fixture
def auth_jefe_ops(api_client, db):
    user = User.objects.create_user(
        codigo_institucional='JOP001',
        email='jop001@utp.edu.pe',
        password='testpass123',
        nombre='Sara',
        apellido='Mamani',
        rol=Role.JEFE_OPERACIONES,
    )
    login = api_client.post('/api/v1/auth/login/', {
        'codigo_institucional': 'JOP001',
        'password': 'testpass123',
    })
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
    return api_client, user

@pytest.mark.django_db
class TestUserCRUD:
    def test_jefe_ops_can_list_users(self, auth_jefe_ops):
        client, _ = auth_jefe_ops
        response = client.get('/api/v1/users/')
        assert response.status_code == 200

    def test_jefe_ops_can_create_user(self, auth_jefe_ops):
        client, _ = auth_jefe_ops
        response = client.post('/api/v1/users/', {
            'codigo_institucional': 'NEW001',
            'email': 'new001@utp.edu.pe',
            'nombre': 'Nuevo',
            'apellido': 'Usuario',
            'rol': Role.ALUMNO,
            'password': 'newpass123',
        })
        assert response.status_code == 201
        assert User.objects.filter(codigo_institucional='NEW001').exists()

    def test_me_endpoint_returns_own_profile(self, api_client, alumno_credentials):
        user, password = alumno_credentials
        login = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': user.codigo_institucional,
            'password': password,
        })
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = api_client.get('/api/v1/users/me/')
        assert response.status_code == 200
        assert response.data['codigo_institucional'] == user.codigo_institucional

@pytest.mark.django_db
class TestVehicleCRUD:
    def test_user_can_add_vehicle(self, api_client, alumno_credentials):
        user, password = alumno_credentials
        login = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': user.codigo_institucional,
            'password': password,
        })
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = api_client.post(f'/api/v1/users/{user.id}/vehicles/', {
            'placa': 'ABC-123',
            'tipo': 'auto',
            'marca': 'Toyota',
            'modelo': 'Corolla',
            'color': 'Blanco',
        })
        assert response.status_code == 201

    def test_user_cannot_add_third_vehicle(self, api_client, alumno_credentials):
        from apps.users.models import Vehicle
        user, password = alumno_credentials
        Vehicle.objects.create(user=user, placa='V01-001', tipo='auto', marca='A', modelo='B', color='C')
        Vehicle.objects.create(user=user, placa='V02-002', tipo='auto', marca='D', modelo='E', color='F')
        login = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': user.codigo_institucional,
            'password': password,
        })
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = api_client.post(f'/api/v1/users/{user.id}/vehicles/', {
            'placa': 'V03-003',
            'tipo': 'moto',
            'marca': 'X',
            'modelo': 'Y',
            'color': 'Z',
        })
        assert response.status_code == 400
```

- [ ] **Paso 2: Correr para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/users/tests/test_views.py::TestUserCRUD apps/users/tests/test_views.py::TestVehicleCRUD -v
```

Resultado esperado: `FAILED` con `404`.

- [ ] **Paso 3: Añadir vistas a `apps/users/views.py`**

Añadir al archivo existente:

```python
from rest_framework import generics, mixins
from rest_framework.decorators import action
from rest_framework.viewsets import GenericViewSet
from .models import User, Vehicle, Role
from .permissions import IsJefeOperacionesOrAbove, IsOperativoOrAbove
from .serializers import UserSerializer, UserCreateSerializer, UserBasicSerializer, VehicleSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    permission_classes = [IsJefeOperacionesOrAbove]

    def get_queryset(self):
        user = self.request.user
        qs = User.objects.select_related('campus_asignado')
        if user.rol == Role.RECTOR:
            return qs.all()
        return qs.filter(campus_asignado=user.campus_asignado)

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer


class VehicleViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = VehicleSerializer

    def get_queryset(self):
        return Vehicle.objects.filter(user_id=self.kwargs['user_pk'])

    def get_permissions(self):
        if self.action == 'create':
            # El propio usuario o un jefe ops+ puede agregar vehículos
            return [IsAuthenticated()]
        return [IsJefeOperacionesOrAbove()]

    def create(self, request, *args, **kwargs):
        target_user_id = self.kwargs['user_pk']
        if str(request.user.id) != str(target_user_id):
            if not IsJefeOperacionesOrAbove().has_permission(request, self):
                return Response(
                    {'detail': 'No tiene permiso para agregar vehículos a otro usuario.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
        return super().create(request, *args, **kwargs)
```

- [ ] **Paso 4: Actualizar `apps/users/urls.py`**

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginView, LogoutView, RefreshView, MeView, UserViewSet, VehicleViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('users/me/', MeView.as_view(), name='user-me'),
    path('', include(router.urls)),
    path('users/<int:user_pk>/vehicles/', VehicleViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-vehicles'),
    path('users/<int:user_pk>/vehicles/<int:pk>/', VehicleViewSet.as_view({'patch': 'partial_update'}), name='user-vehicle-detail'),
]
```

- [ ] **Paso 5: Correr todos los tests**

```bash
docker-compose run --rm web pytest apps/users/ -v
```

Resultado esperado: todos los tests en PASS.

- [ ] **Paso 6: Commit**

```bash
git add apps/users/
git commit -m "feat: add user and vehicle CRUD endpoints with role-based access"
```

---

## Tarea 6: Importación de usuarios desde Excel

**Archivos:**
- Añadir a: `apps/users/views.py`
- Añadir a: `apps/users/urls.py`
- Añadir tests en: `apps/users/tests/test_views.py`

**Interfaces:**
- Produce: `POST /api/v1/users/import/` — sube `.xlsx`, devuelve `{created, updated, errors: [{row, reason}]}`
- Consumes: openpyxl
- Columnas esperadas del Excel: `codigo_institucional`, `email`, `nombre`, `apellido`, `rol`, `placa_1`, `tipo_1`, `placa_2`, `tipo_2`

- [ ] **Paso 1: Escribir test de importación**

Añadir al final de `apps/users/tests/test_views.py`:

```python
import io
import openpyxl

@pytest.mark.django_db
class TestUserImport:
    def test_import_creates_users_from_excel(self, auth_jefe_ops):
        client, _ = auth_jefe_ops
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['codigo_institucional', 'email', 'nombre', 'apellido', 'rol', 'placa_1', 'tipo_1'])
        ws.append(['IMP001', 'imp001@utp.edu.pe', 'Importado', 'Uno', 'alumno', 'IMP-001', 'auto'])
        ws.append(['IMP002', 'imp002@utp.edu.pe', 'Importado', 'Dos', 'academico', '', ''])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = client.post(
            '/api/v1/users/import/',
            {'file': buffer},
            format='multipart',
        )
        assert response.status_code == 200
        assert response.data['created'] == 2
        assert User.objects.filter(codigo_institucional='IMP001').exists()

    def test_import_reports_errors_without_aborting(self, auth_jefe_ops):
        client, _ = auth_jefe_ops
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['codigo_institucional', 'email', 'nombre', 'apellido', 'rol'])
        ws.append(['GOOD001', 'good@utp.edu.pe', 'Bueno', 'Uno', 'alumno'])
        ws.append(['', 'bad@utp.edu.pe', 'Malo', '', 'rol_invalido'])  # fila con errores

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = client.post('/api/v1/users/import/', {'file': buffer}, format='multipart')
        assert response.status_code == 200
        assert response.data['created'] == 1
        assert len(response.data['errors']) == 1
```

- [ ] **Paso 2: Correr para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/users/tests/test_views.py::TestUserImport -v
```

Resultado esperado: `FAILED` con `404`.

- [ ] **Paso 3: Añadir vista de importación a `apps/users/views.py`**

```python
import openpyxl
from django.db import transaction

class UserImportView(APIView):
    permission_classes = [IsJefeOperacionesOrAbove]

    VALID_ROLES = {r.value for r in Role}
    REQUIRED_COLUMNS = {'codigo_institucional', 'email', 'nombre', 'apellido', 'rol'}

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'detail': 'Se requiere un archivo.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wb = openpyxl.load_workbook(file)
        except Exception:
            return Response({'detail': 'Archivo Excel inválido.'}, status=status.HTTP_400_BAD_REQUEST)

        ws = wb.active
        headers = [str(cell.value).strip().lower() for cell in ws[1]]

        missing = self.REQUIRED_COLUMNS - set(headers)
        if missing:
            return Response(
                {'detail': f'Columnas faltantes: {", ".join(missing)}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        created, updated, errors = 0, 0, []

        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            data = dict(zip(headers, row))
            row_errors = self._validate_row(data)

            if row_errors:
                errors.append({'row': row_idx, 'reason': '; '.join(row_errors)})
                continue

            try:
                with transaction.atomic():
                    user, was_created = User.objects.get_or_create(
                        codigo_institucional=data['codigo_institucional'],
                        defaults={
                            'email': data['email'],
                            'nombre': data['nombre'],
                            'apellido': data['apellido'],
                            'rol': data['rol'],
                            'campus_asignado': request.user.campus_asignado,
                        },
                    )
                    if was_created:
                        user.set_password(data['codigo_institucional'])  # contraseña temporal
                        user.save()
                        created += 1
                    else:
                        updated += 1

                    self._import_vehicles(user, data)
            except Exception as e:
                errors.append({'row': row_idx, 'reason': str(e)})

        return Response({'created': created, 'updated': updated, 'errors': errors})

    def _validate_row(self, data: dict) -> list[str]:
        errors = []
        if not data.get('codigo_institucional'):
            errors.append('codigo_institucional requerido')
        if not data.get('email'):
            errors.append('email requerido')
        if data.get('rol') not in self.VALID_ROLES:
            errors.append(f'rol inválido: {data.get("rol")}')
        return errors

    def _import_vehicles(self, user: User, data: dict):
        for i in ('1', '2'):
            placa = data.get(f'placa_{i}', '').strip() if data.get(f'placa_{i}') else ''
            tipo = data.get(f'tipo_{i}', '').strip() if data.get(f'tipo_{i}') else ''
            if placa and tipo:
                Vehicle.objects.get_or_create(
                    placa=placa,
                    defaults={'user': user, 'tipo': tipo, 'marca': '', 'modelo': '', 'color': ''},
                )
```

- [ ] **Paso 4: Añadir URL en `apps/users/urls.py`**

Añadir antes de `path('', include(router.urls))`:

```python
from .views import UserImportView
# ...
path('users/import/', UserImportView.as_view(), name='user-import'),
```

- [ ] **Paso 5: Correr todos los tests del módulo**

```bash
docker-compose run --rm web pytest apps/users/ -v --tb=short
```

Resultado esperado: todos los tests en PASS.

- [ ] **Paso 6: Verificar documentación Swagger**

```bash
docker-compose up -d
# Abrir http://localhost:8000/api/v1/docs/
```

Verificar que aparecen los endpoints: `auth/login`, `auth/logout`, `auth/refresh`, `users/`, `users/me/`, `users/import/`, `users/{id}/vehicles/`.

- [ ] **Paso 7: Commit final del módulo**

```bash
git add apps/users/
git commit -m "feat: add user import from Excel with validation and error reporting"
```

---

## Resumen del módulo

Al completar este plan, el sistema tiene:

- Proyecto Django dockerizado conectado a PostgreSQL
- Modelo `User` con 9 roles y `Vehicle` con límite de 2 por usuario
- Autenticación JWT con login, refresh rotativo y logout con blacklist
- 6 clases de permisos por rol reutilizables en todos los módulos siguientes
- CRUD de usuarios filtrado por campus (Rector ve todo)
- CRUD de vehículos con validación de máximo 2
- Importación masiva desde Excel con reporte de errores por fila
- Admin panel de Django configurado para gestión directa
- Swagger UI disponible en `/api/v1/docs/`

**Siguiente plan:** `2026-06-24-plan-02-spaces.md` — Módulo de campus y espacios (Campus, ParkingLot, ParkingSpace, mapa de ocupación).
