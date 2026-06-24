# Plan 05: Módulo de Reservas y Reportes

> **Para workers agénticos:** USA el skill superpowers:subagent-driven-development o superpowers:executing-plans para implementar tarea por tarea.

**Goal:** Módulo de reservas (`apps/reservations/`) para que Director y Jefe de Operaciones puedan bloquear espacios, y módulo de reportes (`apps/reports/`) con exportación a Excel y PDF de los tres reportes principales.

**Architecture:** Dos mini-apps Django. Las reservas bloquean `ParkingSpace.estado = 'reservado'` durante una ventana de tiempo; un cron/command libera los vencidos. Los reportes consultan AccessRecord, Violation y Sanction para generar Excel (openpyxl) y PDF (ReportLab), con un formato de columnas compatible con Oracle Cloud HCM para el reporte de usuarios.

**Tech Stack:** Django 5.x, DRF, openpyxl==3.1.*, reportlab==4.*, pytest-django. Depende de Plan 01 (User, permisos), Plan 02 (Campus, ParkingSpace), Plan 03 (AccessRecord), Plan 04 (Violation, Sanction).

## Global Constraints

- Solo Director y Jefe de Operaciones (y Rector) pueden crear, modificar o cancelar reservas
- Ningún otro rol puede reservar espacios
- Una reserva bloquea el espacio (`ParkingSpace.estado = RESERVADO`) durante su ventana
- Al vencer, el espacio vuelve automáticamente a LIBRE (si no hay `AccessRecord` activo)
- Los reportes se generan bajo demanda (sin caché de archivos en disco)
- Exportación compatible con Oracle Cloud HCM: columnas fijas, sin macros, UTF-8 con BOM para Excel
- Commits frecuentes, un commit por tarea
- Idioma del código: inglés; mensajes de la API: español

---

## Estructura de archivos

```
apps/
├── reservations/
│   ├── __init__.py
│   ├── models.py          # Reservation
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   ├── management/
│   │   └── commands/
│   │       └── release_reservations.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       └── test_views.py
└── reports/
    ├── __init__.py
    ├── generators/
    │   ├── __init__.py
    │   ├── occupancy.py    # Reporte de ocupación
    │   ├── violations.py   # Reporte de infracciones
    │   └── users.py        # Reporte de usuarios (compatible HCM)
    ├── views.py
    ├── urls.py
    └── tests/
        ├── __init__.py
        └── test_reports.py
```

---

## PARTE A: Módulo de Reservas

---

## Tarea A1: Modelo Reservation

**Archivos:**
- Crear: `apps/reservations/__init__.py`
- Crear: `apps/reservations/models.py`
- Crear: `apps/reservations/admin.py`
- Crear: `apps/reservations/tests/__init__.py`
- Modificar: `config/settings/base.py` (añadir `apps.reservations`)

**Interfaces:**
- Produce: `ReservationState` enum (`activa`, `vencida`, `cancelada`)
- Produce: `Reservation` model vinculado a `ParkingSpace` y `User`

- [ ] **Paso 1: Añadir `apps.reservations` en `config/settings/base.py`**

```python
LOCAL_APPS = [
    'apps.users',
    'apps.spaces',
    'apps.access',
    'apps.violations',
    'apps.reservations',   # añadir
]
```

- [ ] **Paso 2: Escribir tests del modelo**

```python
# apps/reservations/tests/test_models.py
import pytest
from django.utils import timezone
from datetime import timedelta
from apps.reservations.models import Reservation, ReservationState


@pytest.mark.django_db
class TestReservationModel:
    def test_create_reservation(self, space_libre, user_director, campus_arequipa):
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=2)
        r = Reservation.objects.create(
            space=space_libre,
            reservado_por=user_director,
            campus=campus_arequipa,
            inicio=inicio,
            fin=fin,
            motivo='Visita directorio',
        )
        assert r.estado == ReservationState.ACTIVA

    def test_overlapping_reservation_raises(self, space_libre, user_director, campus_arequipa):
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=3)
        Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio, fin=fin,
            motivo='Primera',
        )
        with pytest.raises(Exception):
            Reservation.objects.create(
                space=space_libre, reservado_por=user_director,
                campus=campus_arequipa,
                inicio=inicio + timedelta(hours=1),
                fin=fin + timedelta(hours=1),
                motivo='Segunda (solapada)',
            )
```

- [ ] **Paso 3: Crear `apps/reservations/tests/conftest.py`**

```python
import pytest
from django.utils import timezone
from apps.users.models import User, Role
from apps.spaces.models import Campus, ParkingLot, ParkingSpace, SpaceType, SpaceState


@pytest.fixture
def campus_arequipa(db):
    return Campus.objects.create(
        nombre='Campus Arequipa', ciudad='Arequipa',
        direccion='Av. Parra 201', horario_operacion={},
    )

@pytest.fixture
def parking_lot(campus_arequipa):
    return ParkingLot.objects.create(campus=campus_arequipa, nombre='Sótano 2', nivel=-2)

@pytest.fixture
def space_libre(parking_lot):
    return ParkingSpace.objects.create(
        lot=parking_lot, numero='A-01', tipo=SpaceType.AUTO, estado=SpaceState.LIBRE,
    )

@pytest.fixture
def user_director(campus_arequipa, db):
    return User.objects.create_user(
        codigo_institucional='DIR001', email='dir001@utp.edu.pe',
        password='testpass123', nombre='Ana', apellido='Flores',
        rol=Role.DIRECTOR, campus_asignado=campus_arequipa,
    )

@pytest.fixture
def user_jefe_ops(campus_arequipa, db):
    return User.objects.create_user(
        codigo_institucional='JOP001', email='jop001@utp.edu.pe',
        password='testpass123', nombre='Carlos', apellido='Soto',
        rol=Role.JEFE_OPERACIONES, campus_asignado=campus_arequipa,
    )

@pytest.fixture
def user_alumno(campus_arequipa, db):
    return User.objects.create_user(
        codigo_institucional='ALU001', email='alu001@utp.edu.pe',
        password='testpass123', nombre='Luis', apellido='Torres',
        rol=Role.ALUMNO, campus_asignado=campus_arequipa,
    )
```

- [ ] **Paso 4: Correr tests para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/reservations/tests/ -v
```

Resultado esperado: `ImportError` — los modelos aún no existen.

- [ ] **Paso 5: Escribir `apps/reservations/models.py`**

```python
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
        help_text='Vacío = reserva para uno mismo. Directivo puede reservar para visita.',
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
            raise ValidationError(
                'El espacio ya tiene una reserva activa en ese horario.'
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.space} — {self.inicio:%Y-%m-%d %H:%M} → {self.fin:%H:%M}'


auditlog.register(Reservation)
```

- [ ] **Paso 6: Escribir `apps/reservations/admin.py`**

```python
from django.contrib import admin
from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('space', 'reservado_por', 'beneficiario', 'inicio', 'fin', 'estado')
    list_filter = ('estado', 'campus')
    search_fields = ('reservado_por__codigo_institucional', 'space__numero')
    readonly_fields = ('created_at',)
```

- [ ] **Paso 7: Crear migración y aplicar**

```bash
docker-compose run --rm web python manage.py makemigrations reservations
docker-compose run --rm web python manage.py migrate
```

- [ ] **Paso 8: Correr tests del modelo**

```bash
docker-compose run --rm web pytest apps/reservations/tests/ -v
```

Resultado esperado: todos en PASS.

- [ ] **Paso 9: Commit**

```bash
git add apps/reservations/
git commit -m "feat: add Reservation model with overlap validation"
```

---

## Tarea A2: Endpoints de reservas

**Archivos:**
- Crear: `apps/reservations/serializers.py`
- Crear: `apps/reservations/views.py`
- Crear: `apps/reservations/urls.py`
- Crear: `apps/reservations/tests/test_views.py`
- Añadir a: `config/urls.py`

**Interfaces:**
- Produce: `POST /api/v1/reservations/` — crear reserva (Director/Jefe Ops/Rector)
  - Body: `{space_id, inicio, fin, motivo, beneficiario_id?}`
  - Response 201: reserva creada; `ParkingSpace.estado` → `RESERVADO`
- Produce: `GET /api/v1/reservations/` — listar reservas activas del campus
- Produce: `DELETE /api/v1/reservations/{id}/` — cancelar reserva; `ParkingSpace.estado` → `LIBRE`
- Produce: `GET /api/v1/reservations/spaces/` — espacios disponibles en ventana de tiempo

- [ ] **Paso 1: Escribir tests de endpoints**

```python
# apps/reservations/tests/test_views.py
import pytest
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from apps.spaces.models import SpaceState


@pytest.fixture
def api_client():
    return APIClient()

def login(api_client, codigo, password='testpass123'):
    r = api_client.post('/api/v1/auth/login/', {
        'codigo_institucional': codigo, 'password': password,
    })
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
    return api_client


@pytest.mark.django_db
class TestCreateReservation:
    def test_director_can_create_reservation(
        self, api_client, user_director, space_libre
    ):
        client = login(api_client, 'DIR001')
        inicio = (timezone.now() + timedelta(hours=1)).isoformat()
        fin = (timezone.now() + timedelta(hours=3)).isoformat()
        response = client.post('/api/v1/reservations/', {
            'space_id': space_libre.id,
            'inicio': inicio,
            'fin': fin,
            'motivo': 'Visita directorio',
        })
        assert response.status_code == 201
        space_libre.refresh_from_db()
        assert space_libre.estado == SpaceState.RESERVADO

    def test_alumno_cannot_create_reservation(
        self, api_client, user_alumno, space_libre
    ):
        client = login(api_client, 'ALU001')
        inicio = (timezone.now() + timedelta(hours=1)).isoformat()
        fin = (timezone.now() + timedelta(hours=2)).isoformat()
        response = client.post('/api/v1/reservations/', {
            'space_id': space_libre.id,
            'inicio': inicio,
            'fin': fin,
            'motivo': 'Test',
        })
        assert response.status_code == 403

    def test_overlapping_reservation_returns_400(
        self, api_client, user_director, space_libre, campus_arequipa
    ):
        from apps.reservations.models import Reservation, ReservationState
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=3)
        Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio, fin=fin,
            motivo='Primera', estado=ReservationState.ACTIVA,
        )
        client = login(api_client, 'DIR001')
        response = client.post('/api/v1/reservations/', {
            'space_id': space_libre.id,
            'inicio': (inicio + timedelta(hours=1)).isoformat(),
            'fin': (fin + timedelta(hours=1)).isoformat(),
            'motivo': 'Segunda solapada',
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestCancelReservation:
    def test_cancel_releases_space(
        self, api_client, user_director, space_libre, campus_arequipa
    ):
        from apps.reservations.models import Reservation
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=2)
        r = Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio, fin=fin,
            motivo='Test',
        )
        space_libre.estado = SpaceState.RESERVADO
        space_libre.save()

        client = login(api_client, 'DIR001')
        response = client.delete(f'/api/v1/reservations/{r.id}/')
        assert response.status_code == 204
        space_libre.refresh_from_db()
        assert space_libre.estado == SpaceState.LIBRE
```

- [ ] **Paso 2: Correr para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/reservations/tests/test_views.py -v
```

Resultado esperado: `FAILED` con `404`.

- [ ] **Paso 3: Escribir `apps/reservations/serializers.py`**

```python
from rest_framework import serializers
from apps.spaces.models import ParkingSpace
from apps.users.models import User
from .models import Reservation


class ReservationCreateSerializer(serializers.Serializer):
    space_id = serializers.IntegerField()
    inicio = serializers.DateTimeField()
    fin = serializers.DateTimeField()
    motivo = serializers.CharField(max_length=255)
    beneficiario_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        if data['fin'] <= data['inicio']:
            raise serializers.ValidationError('La fecha de fin debe ser posterior al inicio.')
        if not ParkingSpace.objects.filter(id=data['space_id']).exists():
            raise serializers.ValidationError({'space_id': 'Espacio no encontrado.'})
        return data


class ReservationSerializer(serializers.ModelSerializer):
    space_numero = serializers.CharField(source='space.numero', read_only=True)
    reservado_por_nombre = serializers.CharField(
        source='reservado_por.get_full_name', read_only=True
    )
    beneficiario_nombre = serializers.CharField(
        source='beneficiario.get_full_name', read_only=True, allow_null=True
    )

    class Meta:
        model = Reservation
        fields = (
            'id', 'space', 'space_numero', 'reservado_por', 'reservado_por_nombre',
            'beneficiario', 'beneficiario_nombre', 'campus',
            'inicio', 'fin', 'motivo', 'estado', 'created_at',
        )
        read_only_fields = ('reservado_por', 'campus', 'estado', 'created_at')
```

- [ ] **Paso 4: Escribir `apps/reservations/views.py`**

```python
from django.db import transaction
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.spaces.models import ParkingSpace, SpaceState
from apps.users.models import User
from apps.users.permissions import IsDirectorOrAbove
from .models import Reservation, ReservationState
from .serializers import ReservationCreateSerializer, ReservationSerializer


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    permission_classes = [IsDirectorOrAbove]
    serializer_class = ReservationSerializer

    def get_queryset(self):
        user = self.request.user
        return Reservation.objects.filter(
            campus=user.campus_asignado,
            estado=ReservationState.ACTIVA,
        ).select_related('space', 'reservado_por', 'beneficiario', 'campus')

    def create(self, request):
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        space = ParkingSpace.objects.get(id=data['space_id'])
        beneficiario = None
        if data.get('beneficiario_id'):
            beneficiario = User.objects.filter(id=data['beneficiario_id']).first()

        try:
            with transaction.atomic():
                reservation = Reservation(
                    space=space,
                    reservado_por=request.user,
                    beneficiario=beneficiario,
                    campus=request.user.campus_asignado,
                    inicio=data['inicio'],
                    fin=data['fin'],
                    motivo=data['motivo'],
                )
                reservation.full_clean()
                reservation.save()
                space.estado = SpaceState.RESERVADO
                space.save(update_fields=['estado'])
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ReservationSerializer(reservation).data,
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        with transaction.atomic():
            reservation.estado = ReservationState.CANCELADA
            reservation.save(update_fields=['estado'])
            from apps.access.models import AccessRecord, AccessState
            space = reservation.space
            has_active = AccessRecord.objects.filter(
                space=space, estado=AccessState.ACTIVO
            ).exists()
            if not has_active:
                space.estado = SpaceState.LIBRE
                space.save(update_fields=['estado'])
        return Response(status=status.HTTP_204_NO_CONTENT)
```

- [ ] **Paso 5: Escribir `apps/reservations/urls.py`**

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReservationViewSet

router = DefaultRouter()
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),
]
```

Registrar el `create` manualmente porque el `ViewSet` no hereda de `CreateModelMixin`. Añadir en `urls.py`:

```python
from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ReservationViewSet

router = DefaultRouter()
router.register(r'reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('reservations/', ReservationViewSet.as_view({'get': 'list', 'post': 'create'})),
    path('reservations/<int:pk>/', ReservationViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
]
```

- [ ] **Paso 6: Añadir a `config/urls.py`**

```python
path('api/v1/', include('apps.reservations.urls')),
```

- [ ] **Paso 7: Correr todos los tests**

```bash
docker-compose run --rm web pytest apps/reservations/ -v --tb=short
```

Resultado esperado: todos en PASS.

- [ ] **Paso 8: Commit**

```bash
git add apps/reservations/
git commit -m "feat: add reservation endpoints for Director and Jefe de Operaciones"
```

---

## Tarea A3: Cron job de liberación de reservas vencidas

**Archivos:**
- Crear: `apps/reservations/management/__init__.py`
- Crear: `apps/reservations/management/commands/__init__.py`
- Crear: `apps/reservations/management/commands/release_reservations.py`

**Interfaces:**
- Produce: `python manage.py release_reservations` — vence reservas cuyo `fin < now()` y libera el espacio si no tiene `AccessRecord` activo
- Ejecutar en producción cada 15 minutos vía cron

- [ ] **Paso 1: Crear el comando**

```python
# apps/reservations/management/commands/release_reservations.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from apps.reservations.models import Reservation, ReservationState
from apps.spaces.models import SpaceState
from apps.access.models import AccessRecord, AccessState


class Command(BaseCommand):
    help = 'Vence reservas cuyo horario fin ya pasó y libera el espacio si está desocupado'

    def handle(self, *args, **options):
        now = timezone.now()
        expired = Reservation.objects.filter(
            estado=ReservationState.ACTIVA,
            fin__lt=now,
        ).select_related('space')

        count = 0
        for reservation in expired:
            with transaction.atomic():
                reservation.estado = ReservationState.VENCIDA
                reservation.save(update_fields=['estado'])
                space = reservation.space
                has_active = AccessRecord.objects.filter(
                    space=space, estado=AccessState.ACTIVO
                ).exists()
                if not has_active and space.estado == SpaceState.RESERVADO:
                    space.estado = SpaceState.LIBRE
                    space.save(update_fields=['estado'])
            count += 1

        self.stdout.write(
            self.style.SUCCESS(f'{count} reserva(s) vencida(s) procesada(s).')
        )
```

Crear archivos `__init__.py` vacíos:

```bash
mkdir -p apps/reservations/management/commands
touch apps/reservations/management/__init__.py apps/reservations/management/commands/__init__.py
```

- [ ] **Paso 2: Verificar el comando**

```bash
docker-compose run --rm web python manage.py release_reservations
```

Resultado esperado: `0 reserva(s) vencida(s) procesada(s).`

- [ ] **Paso 3: Instrucción para producción**

Añadir al crontab del servidor (cada 15 min):

```
*/15 * * * * cd /app && python manage.py release_reservations >> /var/log/release_reservations.log 2>&1
```

- [ ] **Paso 4: Commit**

```bash
git add apps/reservations/management/
git commit -m "feat: add release_reservations management command for cron"
```

---

## PARTE B: Módulo de Reportes

---

## Tarea B1: Generadores de reportes

**Archivos:**
- Crear: `apps/reports/__init__.py`
- Crear: `apps/reports/generators/__init__.py`
- Crear: `apps/reports/generators/occupancy.py`
- Crear: `apps/reports/generators/violations.py`
- Crear: `apps/reports/generators/users.py`
- Crear: `apps/reports/tests/__init__.py`
- Crear: `apps/reports/tests/test_reports.py`
- Modificar: `config/settings/base.py` (añadir `apps.reports`)

**Interfaces:**
- Produce: `generate_occupancy_report(campus_id, date_from, date_to, format) → HttpResponse`
  - Columnas: fecha, hora_entrada, hora_salida, usuario, placa, espacio, sotano, duración_min
- Produce: `generate_violations_report(campus_id, date_from, date_to, format) → HttpResponse`
  - Columnas: fecha, usuario, placa, codigo_falta, nivel, descripcion, estado, sancion_aplicada
- Produce: `generate_users_report(campus_id, format) → HttpResponse`
  - Columnas (compatibles HCM): codigo_institucional, nombre, apellido, email, rol, campus, estado, sanciones_activas, vehiculos
- `format`: `'xlsx'` o `'pdf'`

- [ ] **Paso 1: Añadir `apps.reports` en `config/settings/base.py`**

```python
LOCAL_APPS = [
    'apps.users',
    'apps.spaces',
    'apps.access',
    'apps.violations',
    'apps.reservations',
    'apps.reports',     # añadir
]
```

Añadir a `requirements.txt`:

```
openpyxl==3.1.*
reportlab==4.*
```

Reconstruir:

```bash
docker-compose build web
```

- [ ] **Paso 2: Escribir tests de los generadores**

```python
# apps/reports/tests/test_reports.py
import pytest
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from apps.users.models import User, Role
from apps.spaces.models import Campus, ParkingLot, ParkingSpace, SpaceType, SpaceState


@pytest.fixture
def campus_arequipa(db):
    return Campus.objects.create(
        nombre='Campus Arequipa', ciudad='Arequipa',
        direccion='Av. Parra 201', horario_operacion={},
    )

@pytest.fixture
def user_alumno(campus_arequipa):
    return User.objects.create_user(
        codigo_institucional='ALU001', email='alu001@utp.edu.pe',
        password='testpass123', nombre='Luis', apellido='Torres',
        rol=Role.ALUMNO, campus_asignado=campus_arequipa,
    )

@pytest.fixture
def access_record(campus_arequipa, user_alumno, db):
    from apps.access.models import AccessRecord, AccessState
    lot = ParkingLot.objects.create(campus=campus_arequipa, nombre='Sótano 2', nivel=-2)
    space = ParkingSpace.objects.create(lot=lot, numero='A-01', tipo=SpaceType.AUTO, estado=SpaceState.LIBRE)
    from apps.users.models import Vehicle
    vehicle = Vehicle.objects.create(
        user=user_alumno, placa='ABC-123', tipo='auto',
        marca='Toyota', modelo='Corolla', color='Blanco',
    )
    return AccessRecord.objects.create(
        user=user_alumno, vehicle=vehicle, campus=campus_arequipa, space=space,
        registrado_por=user_alumno,
        entrada_at=timezone.now() - timedelta(hours=2),
        salida_at=timezone.now() - timedelta(hours=1),
        estado=AccessState.COMPLETADO,
    )


@pytest.mark.django_db
class TestOccupancyReport:
    def test_xlsx_returns_valid_response(self, campus_arequipa, access_record):
        from apps.reports.generators.occupancy import generate_occupancy_report
        date_from = (timezone.now() - timedelta(days=1)).date()
        date_to = timezone.now().date()
        response = generate_occupancy_report(campus_arequipa.id, date_from, date_to, 'xlsx')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        assert len(response.content) > 0

    def test_pdf_returns_valid_response(self, campus_arequipa, access_record):
        from apps.reports.generators.occupancy import generate_occupancy_report
        date_from = (timezone.now() - timedelta(days=1)).date()
        date_to = timezone.now().date()
        response = generate_occupancy_report(campus_arequipa.id, date_from, date_to, 'pdf')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/pdf'
        assert len(response.content) > 0


@pytest.mark.django_db
class TestViolationsReport:
    def test_xlsx_returns_valid_response(self, campus_arequipa, user_alumno, db):
        from apps.reports.generators.violations import generate_violations_report
        date_from = (timezone.now() - timedelta(days=1)).date()
        date_to = timezone.now().date()
        response = generate_violations_report(campus_arequipa.id, date_from, date_to, 'xlsx')
        assert isinstance(response, HttpResponse)
        assert response['Content-Type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


@pytest.mark.django_db
class TestUsersReport:
    def test_xlsx_hcm_columns_present(self, campus_arequipa, user_alumno):
        from apps.reports.generators.users import generate_users_report
        import openpyxl
        import io
        response = generate_users_report(campus_arequipa.id, 'xlsx')
        wb = openpyxl.load_workbook(io.BytesIO(response.content))
        ws = wb.active
        headers = [cell.value for cell in ws[1]]
        assert 'codigo_institucional' in headers
        assert 'nombre' in headers
        assert 'email' in headers
        assert 'rol' in headers
        assert 'estado' in headers
```

- [ ] **Paso 3: Correr para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/reports/tests/test_reports.py -v
```

Resultado esperado: `ImportError` — los generadores aún no existen.

- [ ] **Paso 4: Escribir `apps/reports/generators/occupancy.py`**

```python
import io
from datetime import date
from django.http import HttpResponse
from django.utils import timezone

from apps.access.models import AccessRecord, AccessState


def _queryset(campus_id: int, date_from: date, date_to: date):
    return AccessRecord.objects.filter(
        campus_id=campus_id,
        entrada_at__date__gte=date_from,
        entrada_at__date__lte=date_to,
    ).select_related('user', 'vehicle', 'space', 'space__lot').order_by('entrada_at')


def _headers():
    return [
        'fecha', 'hora_entrada', 'hora_salida',
        'codigo_usuario', 'nombre_usuario',
        'placa', 'espacio', 'sotano', 'duracion_min',
    ]


def _rows(records):
    rows = []
    for r in records:
        duracion = None
        if r.salida_at:
            duracion = int((r.salida_at - r.entrada_at).total_seconds() / 60)
        rows.append([
            r.entrada_at.date().isoformat(),
            r.entrada_at.strftime('%H:%M'),
            r.salida_at.strftime('%H:%M') if r.salida_at else '',
            r.user.codigo_institucional,
            f'{r.user.nombre} {r.user.apellido}',
            r.vehicle.placa if r.vehicle else '',
            r.space.numero if r.space else '',
            r.space.lot.nombre if r.space else '',
            duracion,
        ])
    return rows


def generate_occupancy_report(campus_id: int, date_from: date, date_to: date, fmt: str) -> HttpResponse:
    records = _queryset(campus_id, date_from, date_to)
    headers = _headers()
    rows = _rows(records)

    if fmt == 'xlsx':
        return _to_xlsx(headers, rows, f'ocupacion_{date_from}_{date_to}')
    return _to_pdf(headers, rows, f'Reporte de Ocupación\n{date_from} → {date_to}')


def _to_xlsx(headers, rows, filename):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Ocupación'

    header_font = Font(bold=True, color='FFFFFF')
    header_fill = PatternFill('solid', fgColor='1F3864')
    ws.append(headers)
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

    for row in rows:
        ws.append(row)

    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    response = HttpResponse(
        buf.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    return response


def _to_pdf(headers, rows, title):
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=20)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles['Title']), Spacer(1, 12)]

    data = [headers] + rows
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F3864')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#EBF3FF')]),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    response = HttpResponse(buf.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="reporte.pdf"'
    return response
```

- [ ] **Paso 5: Escribir `apps/reports/generators/violations.py`**

```python
import io
from datetime import date
from django.http import HttpResponse

from apps.violations.models import Violation


def _queryset(campus_id: int, date_from: date, date_to: date):
    return Violation.objects.filter(
        campus_id=campus_id,
        fecha__date__gte=date_from,
        fecha__date__lte=date_to,
    ).select_related('user', 'vehicle', 'tipo_falta', 'sanction').order_by('fecha')


def _headers():
    return [
        'fecha', 'codigo_usuario', 'nombre_usuario', 'placa',
        'codigo_falta', 'nivel', 'descripcion', 'estado', 'sancion_aplicada',
    ]


def _rows(records):
    rows = []
    for v in records:
        sancion = ''
        if hasattr(v, 'sanction') and v.sanction:
            sancion = v.sanction.tipo
        rows.append([
            v.fecha.strftime('%Y-%m-%d %H:%M'),
            v.user.codigo_institucional,
            f'{v.user.nombre} {v.user.apellido}',
            v.vehicle.placa if v.vehicle else '',
            v.tipo_falta.codigo,
            v.tipo_falta.nivel,
            v.descripcion,
            v.estado,
            sancion,
        ])
    return rows


def generate_violations_report(campus_id: int, date_from: date, date_to: date, fmt: str) -> HttpResponse:
    from apps.reports.generators.occupancy import _to_xlsx, _to_pdf
    records = _queryset(campus_id, date_from, date_to)
    headers = _headers()
    rows = _rows(records)
    if fmt == 'xlsx':
        return _to_xlsx(headers, rows, f'infracciones_{date_from}_{date_to}')
    return _to_pdf(headers, rows, f'Reporte de Infracciones\n{date_from} → {date_to}')
```

- [ ] **Paso 6: Escribir `apps/reports/generators/users.py`**

```python
import io
from django.http import HttpResponse

from apps.users.models import User
from apps.violations.models import Sanction, SanctionState


def _queryset(campus_id: int):
    return User.objects.filter(campus_asignado_id=campus_id).prefetch_related('vehicles', 'sanctions')


def _headers():
    # Columnas compatibles con Oracle Cloud HCM para importación de datos de empleados/estudiantes
    return [
        'codigo_institucional', 'nombre', 'apellido', 'email',
        'rol', 'campus', 'estado', 'sanciones_activas', 'vehiculos',
    ]


def _rows(users):
    rows = []
    for u in users:
        sanciones_activas = sum(
            1 for s in u.sanctions.all() if s.estado == SanctionState.ACTIVA
        )
        placas = ', '.join(v.placa for v in u.vehicles.filter(activo=True))
        rows.append([
            u.codigo_institucional,
            u.nombre,
            u.apellido,
            u.email,
            u.rol,
            u.campus_asignado.nombre if u.campus_asignado else '',
            u.estado,
            sanciones_activas,
            placas,
        ])
    return rows


def generate_users_report(campus_id: int, fmt: str) -> HttpResponse:
    from apps.reports.generators.occupancy import _to_xlsx, _to_pdf
    users = _queryset(campus_id)
    headers = _headers()
    rows = _rows(users)
    if fmt == 'xlsx':
        return _to_xlsx(headers, rows, f'usuarios_campus_{campus_id}')
    return _to_pdf(headers, rows, f'Reporte de Usuarios — Campus {campus_id}')
```

- [ ] **Paso 7: Correr tests de reportes**

```bash
docker-compose run --rm web pytest apps/reports/tests/test_reports.py -v --tb=short
```

Resultado esperado: todos en PASS.

- [ ] **Paso 8: Commit**

```bash
git add apps/reports/
git commit -m "feat: add Excel and PDF report generators for occupancy, violations and users"
```

---

## Tarea B2: Endpoints de reportes

**Archivos:**
- Crear: `apps/reports/views.py`
- Crear: `apps/reports/urls.py`
- Añadir a: `config/urls.py`

**Interfaces:**
- Produce: `GET /api/v1/reports/occupancy/?campus_id=&date_from=&date_to=&format=xlsx`
  - Permisos: Jefe de Operaciones, Jefe de Seguridad, Director, Rector
- Produce: `GET /api/v1/reports/violations/?campus_id=&date_from=&date_to=&format=xlsx`
  - Permisos: mismos que occupancy
- Produce: `GET /api/v1/reports/users/?campus_id=&format=xlsx`
  - Permisos: Director, Rector

- [ ] **Paso 1: Escribir `apps/reports/views.py`**

```python
from datetime import date
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from apps.users.permissions import IsJefeSeguridad, IsJefeOperacionesOrAbove, IsDirectorOrAbove
from .generators.occupancy import generate_occupancy_report
from .generators.violations import generate_violations_report
from .generators.users import generate_users_report


def _parse_date(value: str):
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None


class OccupancyReportView(APIView):
    permission_classes = [IsJefeSeguridad | IsJefeOperacionesOrAbove]

    def get(self, request):
        campus_id = request.query_params.get('campus_id') or getattr(request.user.campus_asignado, 'id', None)
        date_from = _parse_date(request.query_params.get('date_from'))
        date_to = _parse_date(request.query_params.get('date_to'))
        fmt = request.query_params.get('format', 'xlsx')

        if not campus_id or not date_from or not date_to:
            return Response(
                {'detail': 'Parámetros requeridos: campus_id, date_from, date_to.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return generate_occupancy_report(int(campus_id), date_from, date_to, fmt)


class ViolationsReportView(APIView):
    permission_classes = [IsJefeSeguridad | IsJefeOperacionesOrAbove]

    def get(self, request):
        campus_id = request.query_params.get('campus_id') or getattr(request.user.campus_asignado, 'id', None)
        date_from = _parse_date(request.query_params.get('date_from'))
        date_to = _parse_date(request.query_params.get('date_to'))
        fmt = request.query_params.get('format', 'xlsx')

        if not campus_id or not date_from or not date_to:
            return Response(
                {'detail': 'Parámetros requeridos: campus_id, date_from, date_to.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return generate_violations_report(int(campus_id), date_from, date_to, fmt)


class UsersReportView(APIView):
    permission_classes = [IsDirectorOrAbove]

    def get(self, request):
        campus_id = request.query_params.get('campus_id') or getattr(request.user.campus_asignado, 'id', None)
        fmt = request.query_params.get('format', 'xlsx')

        if not campus_id:
            return Response(
                {'detail': 'Parámetro requerido: campus_id.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return generate_users_report(int(campus_id), fmt)
```

- [ ] **Paso 2: Escribir `apps/reports/urls.py`**

```python
from django.urls import path
from .views import OccupancyReportView, ViolationsReportView, UsersReportView

urlpatterns = [
    path('reports/occupancy/', OccupancyReportView.as_view(), name='report-occupancy'),
    path('reports/violations/', ViolationsReportView.as_view(), name='report-violations'),
    path('reports/users/', UsersReportView.as_view(), name='report-users'),
]
```

- [ ] **Paso 3: Añadir a `config/urls.py`**

```python
path('api/v1/', include('apps.reports.urls')),
```

- [ ] **Paso 4: Test de endpoint rápido**

```bash
docker-compose run --rm web pytest apps/reports/ -v --tb=short
```

- [ ] **Paso 5: Commit**

```bash
git add apps/reports/
git commit -m "feat: add report endpoints for occupancy, violations and users"
```

---

## Tarea B3: Integración drf-spectacular (OpenAPI)

**Objetivo:** Exponer Swagger UI y ReDoc con todos los endpoints documentados automáticamente.

**Archivos:**
- Modificar: `config/urls.py`

- [ ] **Paso 1: Verificar `drf-spectacular` instalado**

En `requirements.txt` debe existir:

```
drf-spectacular==0.27.*
```

En `config/settings/base.py`:

```python
INSTALLED_APPS = [
    ...
    'drf_spectacular',
    ...
]

REST_FRAMEWORK = {
    ...
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Estacionamiento UTP API',
    'DESCRIPTION': 'Sistema de gestión de estacionamiento universitario.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}
```

- [ ] **Paso 2: Añadir rutas de documentación en `config/urls.py`**

```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

- [ ] **Paso 3: Verificar que los docs levantan**

```bash
docker-compose run --rm web python manage.py spectacular --validate --fail-on-warn
```

Resultado esperado: schema válido sin warnings.

- [ ] **Paso 4: Commit**

```bash
git add config/urls.py
git commit -m "feat: expose Swagger UI and ReDoc via drf-spectacular"
```

---

## Resumen del plan completo

Con los planes 01–05 implementados, el sistema tiene:

| Módulo | App | Estado |
|--------|-----|--------|
| Setup + Auth + JWT | `users` | Plan 01 |
| Espacios y campus | `spaces` | Plan 02 |
| Acceso con QR | `access` | Plan 03 |
| Violaciones y sanciones | `violations` | Plan 04 |
| Reservas y reportes | `reservations`, `reports` | **Plan 05** |

**Endpoints totales:**

```
POST   /api/v1/auth/login/
POST   /api/v1/auth/logout/
POST   /api/v1/auth/refresh/

CRUD   /api/v1/users/
POST   /api/v1/users/import/
CRUD   /api/v1/vehicles/

CRUD   /api/v1/campus/
GET    /api/v1/campus/{id}/occupancy/
CRUD   /api/v1/parking-lots/
CRUD   /api/v1/parking-spaces/

POST   /api/v1/access/qr/entry/
POST   /api/v1/access/entry/
POST   /api/v1/access/exit/
POST   /api/v1/access/exit/sync/
GET    /api/v1/access/history/

POST   /api/v1/violations/
GET    /api/v1/violations/
POST   /api/v1/violations/{id}/confirm/
POST   /api/v1/violations/{id}/annul/
GET    /api/v1/violations/my/

POST   /api/v1/reservations/
GET    /api/v1/reservations/
DELETE /api/v1/reservations/{id}/

GET    /api/v1/reports/occupancy/
GET    /api/v1/reports/violations/
GET    /api/v1/reports/users/

GET    /api/schema/
GET    /api/docs/
GET    /api/redoc/
```

**Management commands:**

```
manage.py expire_sanctions        # cron diario 01:00
manage.py release_reservations    # cron cada 15 min
```

**Próximos pasos recomendados para v2:**
- Notificaciones por email (Django send_mail) al confirmar sanción
- Panel de administración personalizado para Rector
- App móvil PWA para agentes (offline sync ya preparado)
- Integración de cámaras OCR para placa (v3)
