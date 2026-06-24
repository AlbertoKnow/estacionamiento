# Plan 04: Módulo de Violaciones y Sanciones

> **Para workers agénticos:** USA el skill superpowers:subagent-driven-development o superpowers:executing-plans para implementar tarea por tarea.

**Goal:** Módulo `violations` con catálogo de 19 faltas del reglamento SEG-PT002, registro de violaciones por agentes/asistentes, cálculo automático de sanciones por reincidencia, flujo de aprobación por Jefe de Operaciones, y cron job de expiración automática.

**Architecture:** App Django `apps/violations/`. Las sanciones se calculan consultando `SanctionRule` (tabla configurable). El flujo es: agente registra → sistema calcula sanción propuesta → Jefe de Operaciones confirma o anula → si confirma, `User.estado` se actualiza automáticamente.

**Tech Stack:** Django 5.x, DRF, django-auditlog, pytest-django. Depende de Plan 01 (User, permisos), Plan 02 (Campus), Plan 03 (AccessRecord).

## Global Constraints

- Todos los endpoints bajo `/api/v1/`
- Solo Agente de Seguridad y Asistente de Operaciones registran violaciones
- Solo Jefe de Operaciones y Director (y Rector) confirman o anulan sanciones
- Las sanciones quedan en estado `pendiente` hasta aprobación — no bloquean acceso hasta confirmarse
- La sanción definitiva solo puede revertirla el Rector
- Cada nivel de falta (leve/grave/muy_grave) tiene su propio contador de reincidencias independiente
- Cron job diario revisa sanciones vencidas y reactiva acceso
- Commits frecuentes, un commit por tarea
- Idioma del código: inglés; mensajes de la API: español

---

## Estructura de archivos

```
apps/
└── violations/
    ├── __init__.py
    ├── models.py          # ViolationType, Violation, SanctionRule, Sanction
    ├── serializers.py
    ├── views.py
    ├── urls.py
    ├── sanctions.py       # Lógica de cálculo de sanciones y expiración
    ├── admin.py
    ├── fixtures/
    │   ├── violation_types.json    # 19 faltas del reglamento
    │   └── sanction_rules.json    # Tabla de sanciones configurables
    └── tests/
        ├── __init__.py
        ├── conftest.py
        ├── test_models.py
        ├── test_sanctions.py
        └── test_views.py
```

---

## Tarea 1: Modelos ViolationType, Violation, SanctionRule y Sanction

**Archivos:**
- Crear: `apps/violations/__init__.py`
- Crear: `apps/violations/models.py`
- Crear: `apps/violations/admin.py`
- Crear: `apps/violations/tests/__init__.py`
- Modificar: `config/settings/base.py` (añadir `apps.violations`)

**Interfaces:**
- Produce: `ViolationLevel` enum (`leve`, `grave`, `muy_grave`)
- Produce: `ViolationState` enum (`pendiente`, `confirmada`, `anulada`, `apelada`)
- Produce: `SanctionType` enum (`advertencia`, `suspension_temporal`, `suspension_definitiva`)
- Produce: `SanctionState` enum (`activa`, `cumplida`, `anulada`, `apelada`)

- [ ] **Paso 1: Añadir `apps.violations` en `config/settings/base.py`**

```python
LOCAL_APPS = [
    'apps.users',
    'apps.spaces',
    'apps.access',
    'apps.violations',   # añadir esta línea
]
```

- [ ] **Paso 2: Escribir tests del modelo**

```python
# apps/violations/tests/test_models.py
import pytest
from apps.violations.models import ViolationType, Violation, SanctionRule, Sanction, ViolationLevel, ViolationState

@pytest.mark.django_db
class TestViolationModel:
    def test_create_violation(self, user_agente, user_alumno, campus_arequipa, violation_type_leve_e):
        v = Violation.objects.create(
            user=user_alumno,
            campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Estacionado sobre la línea',
            registrado_por=user_agente,
        )
        assert v.estado == ViolationState.PENDIENTE
        assert v.vehicle is None

    def test_violation_can_link_vehicle(self, user_agente, user_alumno, vehicle, campus_arequipa, violation_type_leve_e):
        v = Violation.objects.create(
            user=user_alumno,
            vehicle=vehicle,
            campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Estacionado sobre la línea',
            registrado_por=user_agente,
        )
        assert v.vehicle == vehicle

@pytest.mark.django_db
class TestSanctionRuleModel:
    def test_rule_exists_for_all_levels(self):
        from apps.violations.models import SanctionRule, ViolationLevel
        for level in ViolationLevel.values:
            for occurrence in range(1, 4):
                rule = SanctionRule.objects.filter(
                    nivel_falta=level,
                    numero_reincidencia=occurrence,
                ).first()
                assert rule is not None, f'Falta regla para {level} ocurrencia {occurrence}'
```

- [ ] **Paso 3: Crear `apps/violations/tests/conftest.py`**

```python
import pytest
from apps.users.models import User, Role
from apps.spaces.models import Campus
from apps.violations.models import ViolationType, ViolationLevel


@pytest.fixture
def campus_arequipa(db):
    return Campus.objects.create(
        nombre='Campus Arequipa', ciudad='Arequipa',
        direccion='Av. Parra 201', horario_operacion={},
    )

@pytest.fixture
def user_alumno(db, campus_arequipa):
    return User.objects.create_user(
        codigo_institucional='ALU001', email='alu001@utp.edu.pe',
        password='testpass123', nombre='Luis', apellido='Torres',
        rol=Role.ALUMNO, campus_asignado=campus_arequipa,
    )

@pytest.fixture
def user_agente(db, campus_arequipa):
    return User.objects.create_user(
        codigo_institucional='AGT001', email='agt001@utp.edu.pe',
        password='testpass123', nombre='Pedro', apellido='Quispe',
        rol=Role.AGENTE_SEGURIDAD, campus_asignado=campus_arequipa,
    )

@pytest.fixture
def user_jefe_ops(db, campus_arequipa):
    return User.objects.create_user(
        codigo_institucional='JOP001', email='jop001@utp.edu.pe',
        password='testpass123', nombre='Sara', apellido='Mamani',
        rol=Role.JEFE_OPERACIONES, campus_asignado=campus_arequipa,
    )

@pytest.fixture
def vehicle(db, user_alumno):
    from apps.users.models import Vehicle
    return Vehicle.objects.create(
        user=user_alumno, placa='ABC-123',
        tipo='auto', marca='Toyota', modelo='Corolla', color='Blanco',
    )

@pytest.fixture
def violation_type_leve_e(db):
    return ViolationType.objects.get_or_create(
        codigo='LEVE_E',
        defaults={
            'descripcion': 'Estacionarse incorrectamente o invadir otro espacio',
            'nivel': ViolationLevel.LEVE,
        },
    )[0]

@pytest.fixture
def violation_type_grave_a(db):
    return ViolationType.objects.get_or_create(
        codigo='GRAVE_A',
        defaults={
            'descripcion': 'No respetar zonas para personas con discapacidad',
            'nivel': ViolationLevel.GRAVE,
        },
    )[0]

@pytest.fixture
def violation_type_muy_grave_g(db):
    return ViolationType.objects.get_or_create(
        codigo='MUY_GRAVE_G',
        defaults={
            'descripcion': 'Prestar o usar Fotocheck ajeno',
            'nivel': ViolationLevel.MUY_GRAVE,
        },
    )[0]
```

- [ ] **Paso 4: Correr para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/violations/tests/test_models.py -v
```

Resultado esperado: `ImportError` — los modelos aún no existen.

- [ ] **Paso 5: Escribir `apps/violations/models.py`**

```python
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
    evidencia_foto = models.ImageField(
        upload_to='violations/', null=True, blank=True
    )
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
```

- [ ] **Paso 6: Escribir `apps/violations/admin.py`**

```python
from django.contrib import admin
from .models import ViolationType, SanctionRule, Violation, Sanction


@admin.register(ViolationType)
class ViolationTypeAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nivel', 'descripcion')
    list_filter = ('nivel',)


@admin.register(SanctionRule)
class SanctionRuleAdmin(admin.ModelAdmin):
    list_display = ('nivel_falta', 'numero_reincidencia', 'tipo_sancion', 'duracion_meses')
    list_filter = ('nivel_falta',)


@admin.register(Violation)
class ViolationAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo_falta', 'campus', 'fecha', 'estado')
    list_filter = ('estado', 'tipo_falta__nivel', 'campus')
    search_fields = ('user__codigo_institucional', 'vehicle__placa')
    readonly_fields = ('fecha', 'registrado_por')


@admin.register(Sanction)
class SanctionAdmin(admin.ModelAdmin):
    list_display = ('user', 'tipo', 'inicio', 'fin', 'estado')
    list_filter = ('tipo', 'estado')
    search_fields = ('user__codigo_institucional',)
```

- [ ] **Paso 7: Crear migración y aplicar**

```bash
docker-compose run --rm web python manage.py makemigrations violations
docker-compose run --rm web python manage.py migrate
```

- [ ] **Paso 8: Correr tests**

```bash
docker-compose run --rm web pytest apps/violations/tests/test_models.py -v
```

Resultado esperado: `test_create_violation` y `test_violation_can_link_vehicle` en PASS. `test_rule_exists_for_all_levels` fallará hasta cargar fixtures en Tarea 2.

- [ ] **Paso 9: Commit**

```bash
git add apps/violations/
git commit -m "feat: add ViolationType, Violation, SanctionRule and Sanction models"
```

---

## Tarea 2: Fixtures del catálogo de faltas y reglas de sanción

**Archivos:**
- Crear: `apps/violations/fixtures/violation_types.json`
- Crear: `apps/violations/fixtures/sanction_rules.json`

**Interfaces:**
- Produce: 19 `ViolationType` cargables con `loaddata`
- Produce: 9 `SanctionRule` (3 niveles × 3 reincidencias) cargables con `loaddata`

- [ ] **Paso 1: Crear `apps/violations/fixtures/violation_types.json`**

```json
[
  {"model": "violations.violationtype", "pk": 1,  "fields": {"codigo": "LEVE_A", "descripcion": "No acatar indicaciones del personal de Seguridad", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 2,  "fields": {"codigo": "LEVE_B", "descripcion": "No respetar turno solicitado o sede asignada", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 3,  "fields": {"codigo": "LEVE_C", "descripcion": "No permitir la revisión del vehículo", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 4,  "fields": {"codigo": "LEVE_D", "descripcion": "Tocar bocina sin motivo urgente", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 5,  "fields": {"codigo": "LEVE_E", "descripcion": "Estacionarse incorrectamente o invadir otro espacio", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 6,  "fields": {"codigo": "LEVE_F", "descripcion": "No respetar espacios reservados para directivos", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 7,  "fields": {"codigo": "LEVE_G", "descripcion": "Mantener ocupante en el vehículo una vez estacionado (reportado por agente en ronda)", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 8,  "fields": {"codigo": "LEVE_H", "descripcion": "No usar luces dentro del estacionamiento o no usar luces direccionales", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 9,  "fields": {"codigo": "LEVE_I", "descripcion": "Bloquear entrada esperando espacio disponible o impedir libre tránsito", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 10, "fields": {"codigo": "LEVE_J", "descripcion": "No respetar señales de tránsito internas", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 11, "fields": {"codigo": "LEVE_K", "descripcion": "Estacionar moto o bicicleta en espacio incorrecto", "nivel": "leve"}},
  {"model": "violations.violationtype", "pk": 12, "fields": {"codigo": "GRAVE_A", "descripcion": "No respetar zonas para personas con discapacidad", "nivel": "grave"}},
  {"model": "violations.violationtype", "pk": 13, "fields": {"codigo": "GRAVE_B", "descripcion": "No estacionar según tipo de vehículo", "nivel": "grave"}},
  {"model": "violations.violationtype", "pk": 14, "fields": {"codigo": "GRAVE_C", "descripcion": "Exceder velocidad de 10 km/h dentro del estacionamiento", "nivel": "grave"}},
  {"model": "violations.violationtype", "pk": 15, "fields": {"codigo": "GRAVE_D", "descripcion": "Realizar maniobras temerarias", "nivel": "grave"}},
  {"model": "violations.violationtype", "pk": 16, "fields": {"codigo": "GRAVE_E", "descripcion": "Vehículo pernoctando sin autorización", "nivel": "grave"}},
  {"model": "violations.violationtype", "pk": 17, "fields": {"codigo": "GRAVE_F", "descripcion": "Agredir física o verbalmente al personal de Seguridad o colaboradores", "nivel": "grave"}},
  {"model": "violations.violationtype", "pk": 18, "fields": {"codigo": "MUY_GRAVE_G", "descripcion": "Prestar o usar Fotocheck ajeno", "nivel": "muy_grave"}},
  {"model": "violations.violationtype", "pk": 19, "fields": {"codigo": "MUY_GRAVE_H", "descripcion": "Modificar o adulterar el Fotocheck usando mecanismos digitales", "nivel": "muy_grave"}}
]
```

- [ ] **Paso 2: Crear `apps/violations/fixtures/sanction_rules.json`**

```json
[
  {"model": "violations.sanctionrule", "pk": 1, "fields": {"nivel_falta": "leve",      "numero_reincidencia": 1, "tipo_sancion": "advertencia",           "duracion_meses": null}},
  {"model": "violations.sanctionrule", "pk": 2, "fields": {"nivel_falta": "leve",      "numero_reincidencia": 2, "tipo_sancion": "suspension_temporal",   "duracion_meses": 1}},
  {"model": "violations.sanctionrule", "pk": 3, "fields": {"nivel_falta": "leve",      "numero_reincidencia": 3, "tipo_sancion": "suspension_temporal",   "duracion_meses": 3}},
  {"model": "violations.sanctionrule", "pk": 4, "fields": {"nivel_falta": "grave",     "numero_reincidencia": 1, "tipo_sancion": "suspension_temporal",   "duracion_meses": 3}},
  {"model": "violations.sanctionrule", "pk": 5, "fields": {"nivel_falta": "grave",     "numero_reincidencia": 2, "tipo_sancion": "suspension_temporal",   "duracion_meses": 6}},
  {"model": "violations.sanctionrule", "pk": 6, "fields": {"nivel_falta": "grave",     "numero_reincidencia": 3, "tipo_sancion": "suspension_temporal",   "duracion_meses": 12}},
  {"model": "violations.sanctionrule", "pk": 7, "fields": {"nivel_falta": "muy_grave", "numero_reincidencia": 1, "tipo_sancion": "suspension_temporal",   "duracion_meses": 12}},
  {"model": "violations.sanctionrule", "pk": 8, "fields": {"nivel_falta": "muy_grave", "numero_reincidencia": 2, "tipo_sancion": "suspension_temporal",   "duracion_meses": 24}},
  {"model": "violations.sanctionrule", "pk": 9, "fields": {"nivel_falta": "muy_grave", "numero_reincidencia": 3, "tipo_sancion": "suspension_definitiva", "duracion_meses": null}}
]
```

- [ ] **Paso 3: Cargar fixtures**

```bash
docker-compose run --rm web python manage.py loaddata apps/violations/fixtures/violation_types.json
docker-compose run --rm web python manage.py loaddata apps/violations/fixtures/sanction_rules.json
```

- [ ] **Paso 4: Correr todos los tests del modelo**

```bash
docker-compose run --rm web pytest apps/violations/tests/test_models.py -v
```

Resultado esperado: todos en PASS incluyendo `test_rule_exists_for_all_levels`.

- [ ] **Paso 5: Commit**

```bash
git add apps/violations/fixtures/
git commit -m "feat: add violation types and sanction rules fixtures from SEG-PT002"
```

---

## Tarea 3: Lógica de cálculo de sanciones

**Archivos:**
- Crear: `apps/violations/sanctions.py`
- Crear: `apps/violations/tests/test_sanctions.py`

**Interfaces:**
- Produce: `calculate_sanction(user, violation_type) → SanctionRule` — determina la regla a aplicar según historial de reincidencias del usuario para ese nivel de falta
- Produce: `apply_sanction(violation, applied_by) → Sanction` — crea la `Sanction`, actualiza `User.estado` y `suspension_hasta`
- Produce: `expire_sanctions()` — revisa sanciones vencidas y reactiva acceso; llamado por cron job

- [ ] **Paso 1: Escribir tests de lógica de sanciones**

```python
# apps/violations/tests/test_sanctions.py
import pytest
from django.utils import timezone
from datetime import timedelta
from apps.violations.models import (
    ViolationType, Violation, SanctionRule, Sanction,
    ViolationLevel, ViolationState, SanctionType, SanctionState,
)
from apps.violations.sanctions import calculate_sanction, apply_sanction, expire_sanctions
from apps.users.models import UserState


@pytest.mark.django_db
class TestCalculateSanction:
    def test_first_leve_gives_advertencia(
        self, user_alumno, user_agente, campus_arequipa, violation_type_leve_e
    ):
        rule = calculate_sanction(user_alumno, violation_type_leve_e)
        assert rule.tipo_sancion == SanctionType.ADVERTENCIA
        assert rule.numero_reincidencia == 1

    def test_second_leve_gives_one_month(
        self, user_alumno, user_agente, campus_arequipa, violation_type_leve_e
    ):
        # primera falta confirmada
        v1 = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Primera', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        rule = calculate_sanction(user_alumno, violation_type_leve_e)
        assert rule.numero_reincidencia == 2
        assert rule.duracion_meses == 1

    def test_counters_are_independent_per_level(
        self, user_alumno, user_agente, campus_arequipa,
        violation_type_leve_e, violation_type_grave_a,
    ):
        # una falta leve confirmada no afecta el contador grave
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Leve 1', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        rule = calculate_sanction(user_alumno, violation_type_grave_a)
        assert rule.numero_reincidencia == 1
        assert rule.tipo_sancion == SanctionType.SUSPENSION_TEMPORAL
        assert rule.duracion_meses == 3

    def test_capped_at_third_occurrence(
        self, user_alumno, user_agente, campus_arequipa, violation_type_leve_e
    ):
        for i in range(5):
            Violation.objects.create(
                user=user_alumno, campus=campus_arequipa,
                tipo_falta=violation_type_leve_e,
                descripcion=f'Falta {i}', registrado_por=user_agente,
                estado=ViolationState.CONFIRMADA,
            )
        rule = calculate_sanction(user_alumno, violation_type_leve_e)
        assert rule.numero_reincidencia == 3


@pytest.mark.django_db
class TestApplySanction:
    def test_advertencia_does_not_suspend_user(
        self, user_alumno, user_agente, user_jefe_ops, campus_arequipa, violation_type_leve_e
    ):
        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Primera leve', registrado_por=user_agente,
        )
        sanction = apply_sanction(v, applied_by=user_jefe_ops)
        assert sanction.tipo == SanctionType.ADVERTENCIA
        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.ACTIVO

    def test_suspension_temporal_suspends_user(
        self, user_alumno, user_agente, user_jefe_ops, campus_arequipa, violation_type_leve_e
    ):
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Primera', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        v2 = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Segunda', registrado_por=user_agente,
        )
        sanction = apply_sanction(v2, applied_by=user_jefe_ops)
        assert sanction.tipo == SanctionType.SUSPENSION_TEMPORAL
        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.SUSPENDIDO
        assert user_alumno.suspension_hasta is not None


@pytest.mark.django_db
class TestExpireSanctions:
    def test_expired_sanction_reactivates_user(
        self, user_alumno, user_agente, user_jefe_ops, campus_arequipa, violation_type_leve_e
    ):
        from django.utils import timezone
        yesterday = timezone.now().date() - timedelta(days=1)
        user_alumno.estado = UserState.SUSPENDIDO
        user_alumno.suspension_hasta = yesterday
        user_alumno.save()

        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Falta', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        Sanction.objects.create(
            user=user_alumno, violation=v,
            tipo=SanctionType.SUSPENSION_TEMPORAL,
            inicio=yesterday - timedelta(days=30),
            fin=yesterday,
            aplicada_por=user_jefe_ops,
            estado=SanctionState.ACTIVA,
        )

        expire_sanctions()

        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.ACTIVO
        assert user_alumno.suspension_hasta is None
```

- [ ] **Paso 2: Correr para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/violations/tests/test_sanctions.py -v
```

Resultado esperado: `ImportError` — `sanctions.py` aún no existe.

- [ ] **Paso 3: Escribir `apps/violations/sanctions.py`**

```python
from datetime import date
from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

from apps.users.models import UserState
from .models import (
    ViolationType, Violation, SanctionRule, Sanction,
    ViolationLevel, ViolationState, SanctionType, SanctionState,
)


def calculate_sanction(user, violation_type: ViolationType) -> SanctionRule:
    """Determina la regla a aplicar según historial confirmado del usuario para ese nivel."""
    nivel = violation_type.nivel
    prior_count = Violation.objects.filter(
        user=user,
        tipo_falta__nivel=nivel,
        estado=ViolationState.CONFIRMADA,
    ).count()
    occurrence = min(prior_count + 1, 3)
    return SanctionRule.objects.get(nivel_falta=nivel, numero_reincidencia=occurrence)


def apply_sanction(violation: Violation, applied_by) -> Sanction:
    """Crea la Sanction y actualiza el estado del usuario si corresponde."""
    rule = calculate_sanction(violation.user, violation.tipo_falta)
    today = timezone.now().date()

    fin = None
    if rule.tipo_sancion == SanctionType.SUSPENSION_TEMPORAL and rule.duracion_meses:
        fin = today + relativedelta(months=rule.duracion_meses)

    with transaction.atomic():
        violation.estado = ViolationState.CONFIRMADA
        violation.save(update_fields=['estado'])

        sanction = Sanction.objects.create(
            user=violation.user,
            violation=violation,
            tipo=rule.tipo_sancion,
            inicio=today if rule.tipo_sancion != SanctionType.ADVERTENCIA else None,
            fin=fin,
            aplicada_por=applied_by,
            estado=SanctionState.ACTIVA,
        )

        if rule.tipo_sancion in (SanctionType.SUSPENSION_TEMPORAL, SanctionType.SUSPENSION_DEFINITIVA):
            violation.user.estado = UserState.SUSPENDIDO
            violation.user.suspension_hasta = fin  # None = definitiva
            violation.user.save(update_fields=['estado', 'suspension_hasta'])

    return sanction


def expire_sanctions():
    """Reactiva usuarios cuya suspensión temporal ya venció. Llamado por cron job diario."""
    today = timezone.now().date()
    expired = Sanction.objects.filter(
        estado=SanctionState.ACTIVA,
        tipo=SanctionType.SUSPENSION_TEMPORAL,
        fin__lt=today,
    ).select_related('user')

    for sanction in expired:
        with transaction.atomic():
            sanction.estado = SanctionState.CUMPLIDA
            sanction.save(update_fields=['estado'])
            user = sanction.user
            user.estado = UserState.ACTIVO
            user.suspension_hasta = None
            user.save(update_fields=['estado', 'suspension_hasta'])
```

Añadir `python-dateutil` a `requirements.txt`:

```
python-dateutil==2.9.*
```

Reconstruir:

```bash
docker-compose build web
```

- [ ] **Paso 4: Correr tests de sanciones**

```bash
docker-compose run --rm web pytest apps/violations/tests/test_sanctions.py -v
```

Resultado esperado: todos en PASS.

- [ ] **Paso 5: Commit**

```bash
git add apps/violations/sanctions.py apps/violations/tests/test_sanctions.py requirements.txt
git commit -m "feat: add sanction calculation and expiration logic"
```

---

## Tarea 4: Endpoints de violaciones y flujo de aprobación

**Archivos:**
- Crear: `apps/violations/serializers.py`
- Crear: `apps/violations/views.py`
- Crear: `apps/violations/urls.py`
- Añadir a: `config/urls.py`
- Crear: `apps/violations/tests/test_views.py`

**Interfaces:**
- Produce: `POST /api/v1/violations/` — registrar violación (agente/asistente)
  - Body: `{user_id, vehicle_id?, tipo_falta_id, descripcion, access_record_id?}`
  - Response 201: violación creada con sanción propuesta incluida
- Produce: `GET /api/v1/violations/` — listar (Jefe Ops+ ve todas; agente ve las propias)
- Produce: `POST /api/v1/violations/{id}/confirm/` — confirmar sanción (Jefe Ops+)
- Produce: `POST /api/v1/violations/{id}/annul/` — anular violación (Jefe Ops+)
- Produce: `GET /api/v1/violations/my/` — propias faltas (usuarios finales)

- [ ] **Paso 1: Escribir tests de endpoints**

```python
# apps/violations/tests/test_views.py
import pytest
from rest_framework.test import APIClient
from apps.users.models import User, Role, UserState
from apps.spaces.models import Campus
from apps.violations.models import ViolationType, Violation, ViolationLevel, ViolationState


@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def campus_arequipa(db):
    return Campus.objects.create(
        nombre='Campus Arequipa', ciudad='Arequipa',
        direccion='Av. Parra 201', horario_operacion={},
    )

@pytest.fixture
def violation_type_leve(db):
    return ViolationType.objects.get_or_create(
        codigo='LEVE_E',
        defaults={'descripcion': 'Estacionado mal', 'nivel': ViolationLevel.LEVE},
    )[0]

@pytest.fixture
def sanction_rules(db):
    from apps.violations.models import SanctionRule, SanctionType
    SanctionRule.objects.get_or_create(
        nivel_falta='leve', numero_reincidencia=1,
        defaults={'tipo_sancion': SanctionType.ADVERTENCIA, 'duracion_meses': None},
    )
    SanctionRule.objects.get_or_create(
        nivel_falta='leve', numero_reincidencia=2,
        defaults={'tipo_sancion': 'suspension_temporal', 'duracion_meses': 1},
    )
    SanctionRule.objects.get_or_create(
        nivel_falta='leve', numero_reincidencia=3,
        defaults={'tipo_sancion': 'suspension_temporal', 'duracion_meses': 3},
    )

@pytest.fixture
def auth_agente(api_client, campus_arequipa, db):
    user = User.objects.create_user(
        codigo_institucional='AGT001', email='agt001@utp.edu.pe',
        password='testpass123', nombre='Pedro', apellido='Quispe',
        rol=Role.AGENTE_SEGURIDAD, campus_asignado=campus_arequipa,
    )
    login = api_client.post('/api/v1/auth/login/', {'codigo_institucional': 'AGT001', 'password': 'testpass123'})
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
    return api_client, user

@pytest.fixture
def auth_jefe_ops(api_client, campus_arequipa, db):
    user = User.objects.create_user(
        codigo_institucional='JOP001', email='jop001@utp.edu.pe',
        password='testpass123', nombre='Sara', apellido='Mamani',
        rol=Role.JEFE_OPERACIONES, campus_asignado=campus_arequipa,
    )
    login = api_client.post('/api/v1/auth/login/', {'codigo_institucional': 'JOP001', 'password': 'testpass123'})
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
    return api_client, user

@pytest.fixture
def user_alumno(campus_arequipa, db):
    return User.objects.create_user(
        codigo_institucional='ALU001', email='alu001@utp.edu.pe',
        password='testpass123', nombre='Luis', apellido='Torres',
        rol=Role.ALUMNO, campus_asignado=campus_arequipa,
    )

@pytest.mark.django_db
class TestCreateViolation:
    def test_agente_can_register_violation(
        self, auth_agente, user_alumno, violation_type_leve, sanction_rules
    ):
        client, _ = auth_agente
        response = client.post('/api/v1/violations/', {
            'user_id': user_alumno.id,
            'tipo_falta_id': violation_type_leve.id,
            'descripcion': 'Estacionado sobre la línea amarilla',
        })
        assert response.status_code == 201
        assert response.data['estado'] == ViolationState.PENDIENTE
        assert 'sancion_propuesta' in response.data

    def test_alumno_cannot_register_violation(self, api_client, user_alumno, violation_type_leve):
        login = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': 'ALU001', 'password': 'testpass123',
        })
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = api_client.post('/api/v1/violations/', {
            'user_id': user_alumno.id,
            'tipo_falta_id': violation_type_leve.id,
            'descripcion': 'Test',
        })
        assert response.status_code == 403

@pytest.mark.django_db
class TestConfirmViolation:
    def test_jefe_ops_confirms_violation_and_suspends_user(
        self, auth_jefe_ops, auth_agente, user_alumno,
        violation_type_leve, sanction_rules, campus_arequipa, db,
    ):
        # segunda falta: debe suspender
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve,
            descripcion='Primera falta',
            registrado_por=user_alumno,
            estado=ViolationState.CONFIRMADA,
        )
        client_agente, agente = auth_agente
        response = client_agente.post('/api/v1/violations/', {
            'user_id': user_alumno.id,
            'tipo_falta_id': violation_type_leve.id,
            'descripcion': 'Segunda falta',
        })
        violation_id = response.data['id']

        client_jefe, _ = auth_jefe_ops
        confirm = client_jefe.post(f'/api/v1/violations/{violation_id}/confirm/')
        assert confirm.status_code == 200

        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.SUSPENDIDO

    def test_agente_cannot_confirm_violation(
        self, auth_agente, user_alumno, violation_type_leve, campus_arequipa, sanction_rules
    ):
        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve,
            descripcion='Falta', registrado_por=user_alumno,
        )
        client, _ = auth_agente
        response = client.post(f'/api/v1/violations/{v.id}/confirm/')
        assert response.status_code == 403

@pytest.mark.django_db
class TestMyViolations:
    def test_user_sees_own_violations(self, api_client, user_alumno, campus_arequipa, violation_type_leve, db):
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve,
            descripcion='Mi falta', registrado_por=user_alumno,
        )
        login = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': 'ALU001', 'password': 'testpass123',
        })
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = api_client.get('/api/v1/violations/my/')
        assert response.status_code == 200
        assert len(response.data) == 1
```

- [ ] **Paso 2: Correr para verificar que fallan**

```bash
docker-compose run --rm web pytest apps/violations/tests/test_views.py -v
```

Resultado esperado: `FAILED` con `404`.

- [ ] **Paso 3: Escribir `apps/violations/serializers.py`**

```python
from rest_framework import serializers
from apps.users.models import User, Vehicle
from .models import ViolationType, Violation, Sanction, SanctionRule
from .sanctions import calculate_sanction


class SanctionProposalSerializer(serializers.Serializer):
    tipo_sancion = serializers.CharField()
    duracion_meses = serializers.IntegerField(allow_null=True)
    numero_reincidencia = serializers.IntegerField()


class ViolationCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    vehicle_id = serializers.IntegerField(required=False, allow_null=True)
    tipo_falta_id = serializers.IntegerField()
    descripcion = serializers.CharField()
    access_record_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('Usuario no encontrado.')
        return value

    def validate_tipo_falta_id(self, value):
        if not ViolationType.objects.filter(id=value).exists():
            raise serializers.ValidationError('Tipo de falta no encontrado.')
        return value


class ViolationSerializer(serializers.ModelSerializer):
    tipo_falta_codigo = serializers.CharField(source='tipo_falta.codigo', read_only=True)
    tipo_falta_nivel = serializers.CharField(source='tipo_falta.nivel', read_only=True)
    registrado_por_nombre = serializers.CharField(source='registrado_por.get_full_name', read_only=True)
    sancion_propuesta = serializers.SerializerMethodField()

    class Meta:
        model = Violation
        fields = (
            'id', 'user', 'vehicle', 'campus', 'tipo_falta_codigo', 'tipo_falta_nivel',
            'descripcion', 'fecha', 'estado', 'registrado_por_nombre', 'sancion_propuesta',
        )

    def get_sancion_propuesta(self, obj):
        if obj.estado == 'pendiente':
            try:
                rule = calculate_sanction(obj.user, obj.tipo_falta)
                return SanctionProposalSerializer(rule).data
            except Exception:
                return None
        return None


class SanctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sanction
        fields = ('id', 'tipo', 'inicio', 'fin', 'estado', 'created_at')
```

- [ ] **Paso 4: Escribir `apps/violations/views.py`**

```python
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from apps.users.models import Role
from apps.users.permissions import IsOperativoOrAbove, IsJefeOperacionesOrAbove
from .models import Violation, ViolationType, ViolationState
from .sanctions import apply_sanction
from .serializers import ViolationCreateSerializer, ViolationSerializer


class ViolationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = ViolationSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsOperativoOrAbove()]
        if self.action in ('confirm', 'annul'):
            return [IsJefeOperacionesOrAbove()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.rol in (Role.RECTOR,):
            return Violation.objects.select_related(
                'user', 'vehicle', 'campus', 'tipo_falta', 'registrado_por'
            ).all()
        if user.rol in (Role.DIRECTOR, Role.JEFE_OPERACIONES, Role.JEFE_SEGURIDAD,
                        Role.ASISTENTE_OPERACIONES):
            return Violation.objects.select_related(
                'user', 'vehicle', 'campus', 'tipo_falta', 'registrado_por'
            ).filter(campus=user.campus_asignado)
        # agente: solo las que él registró
        return Violation.objects.filter(registrado_por=user)

    def create(self, request):
        serializer = ViolationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from apps.users.models import User, Vehicle
        from apps.spaces.models import Campus
        user = User.objects.get(id=data['user_id'])
        tipo_falta = ViolationType.objects.get(id=data['tipo_falta_id'])
        campus = request.user.campus_asignado

        vehicle = None
        if data.get('vehicle_id'):
            vehicle = Vehicle.objects.filter(id=data['vehicle_id']).first()

        access_record = None
        if data.get('access_record_id'):
            from apps.access.models import AccessRecord
            access_record = AccessRecord.objects.filter(id=data['access_record_id']).first()

        violation = Violation.objects.create(
            user=user,
            vehicle=vehicle,
            campus=campus,
            tipo_falta=tipo_falta,
            descripcion=data['descripcion'],
            registrado_por=request.user,
            access_record=access_record,
        )
        return Response(ViolationSerializer(violation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        violation = self.get_object()
        if violation.estado != ViolationState.PENDIENTE:
            return Response(
                {'detail': 'Solo se pueden confirmar violaciones pendientes.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sanction = apply_sanction(violation, applied_by=request.user)
        return Response({
            'detail': 'Sanción confirmada.',
            'sancion_id': sanction.id,
            'tipo': sanction.tipo,
            'fin': sanction.fin,
        })

    @action(detail=True, methods=['post'])
    def annul(self, request, pk=None):
        violation = self.get_object()
        if violation.estado not in (ViolationState.PENDIENTE, ViolationState.CONFIRMADA):
            return Response(
                {'detail': 'No se puede anular esta violación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        violation.estado = ViolationState.ANULADA
        violation.save(update_fields=['estado'])
        return Response({'detail': 'Violación anulada.'})


class MyViolationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        violations = Violation.objects.filter(
            user=request.user
        ).select_related('tipo_falta', 'campus').order_by('-fecha')
        return Response(ViolationSerializer(violations, many=True).data)
```

- [ ] **Paso 5: Escribir `apps/violations/urls.py`**

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ViolationViewSet, MyViolationsView

router = DefaultRouter()
router.register(r'violations', ViolationViewSet, basename='violation')

urlpatterns = [
    path('violations/my/', MyViolationsView.as_view(), name='my-violations'),
    path('', include(router.urls)),
]
```

- [ ] **Paso 6: Añadir a `config/urls.py`**

```python
path('api/v1/', include('apps.violations.urls')),
```

- [ ] **Paso 7: Correr todos los tests**

```bash
docker-compose run --rm web pytest apps/violations/ -v --tb=short
```

Resultado esperado: todos en PASS.

- [ ] **Paso 8: Commit**

```bash
git add apps/violations/
git commit -m "feat: add violation registration and approval endpoints"
```

---

## Tarea 5: Cron job de expiración de sanciones

**Archivos:**
- Crear: `apps/violations/management/__init__.py`
- Crear: `apps/violations/management/commands/__init__.py`
- Crear: `apps/violations/management/commands/expire_sanctions.py`

**Interfaces:**
- Produce: `python manage.py expire_sanctions` — reactiva usuarios con sanción vencida
- La misma función `expire_sanctions()` de `sanctions.py` es llamada por el comando
- En producción se ejecuta diariamente vía cron del sistema operativo o tarea programada

- [ ] **Paso 1: Escribir test del comando**

```python
# añadir a apps/violations/tests/test_sanctions.py

@pytest.mark.django_db
class TestExpireSanctionsCommand:
    def test_management_command_expires_sanctions(
        self, user_alumno, user_agente, user_jefe_ops,
        campus_arequipa, violation_type_leve_e, db
    ):
        from django.utils import timezone
        from datetime import timedelta
        from apps.violations.models import Sanction, SanctionType, SanctionState, Violation, ViolationState
        from apps.users.models import UserState

        yesterday = timezone.now().date() - timedelta(days=1)
        user_alumno.estado = UserState.SUSPENDIDO
        user_alumno.suspension_hasta = yesterday
        user_alumno.save()

        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Falta', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        Sanction.objects.create(
            user=user_alumno, violation=v,
            tipo=SanctionType.SUSPENSION_TEMPORAL,
            inicio=yesterday - timedelta(days=30),
            fin=yesterday,
            aplicada_por=user_jefe_ops,
            estado=SanctionState.ACTIVA,
        )

        from django.core.management import call_command
        call_command('expire_sanctions')

        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.ACTIVO
```

- [ ] **Paso 2: Correr para verificar que falla**

```bash
docker-compose run --rm web pytest apps/violations/tests/test_sanctions.py::TestExpireSanctionsCommand -v
```

Resultado esperado: `FAILED` — comando no existe.

- [ ] **Paso 3: Crear el comando de management**

```python
# apps/violations/management/commands/expire_sanctions.py
from django.core.management.base import BaseCommand
from apps.violations.sanctions import expire_sanctions


class Command(BaseCommand):
    help = 'Reactiva acceso de usuarios cuya suspensión temporal ha vencido'

    def handle(self, *args, **options):
        expire_sanctions()
        self.stdout.write(self.style.SUCCESS('Sanciones expiradas procesadas correctamente.'))
```

Crear archivos `__init__.py` vacíos:

```bash
mkdir -p apps/violations/management/commands
touch apps/violations/management/__init__.py apps/violations/management/commands/__init__.py
```

- [ ] **Paso 4: Correr todos los tests del módulo**

```bash
docker-compose run --rm web pytest apps/violations/ -v --tb=short
```

Resultado esperado: todos en PASS.

- [ ] **Paso 5: Verificar el comando manualmente**

```bash
docker-compose run --rm web python manage.py expire_sanctions
```

Resultado esperado: `Sanciones expiradas procesadas correctamente.`

- [ ] **Paso 6: Añadir al crontab del servidor (instrucción para producción)**

En el servidor de producción, añadir al crontab del sistema:

```
0 1 * * * cd /app && python manage.py expire_sanctions >> /var/log/expire_sanctions.log 2>&1
```

Esto ejecuta el comando cada día a la 1:00 AM hora local.

- [ ] **Paso 7: Commit final del módulo**

```bash
git add apps/violations/
git commit -m "feat: add expire_sanctions management command for daily cron"
```

---

## Resumen del módulo

Al completar este plan, el sistema tiene:

- 19 tipos de falta precargados del reglamento SEG-PT002
- 9 reglas de sanción configurables (3 niveles × 3 reincidencias)
- Registro de violaciones por agente/asistente con sanción propuesta automática
- Contadores de reincidencia independientes por nivel de falta
- Flujo: agente registra → estado `pendiente` → Jefe Ops confirma o anula → si confirma, usuario suspendido automáticamente
- Usuarios finales ven sus propias faltas y sanciones
- Cron job diario que reactiva usuarios con suspensión vencida
- Todo auditado con django-auditlog

**Siguiente plan:** `2026-06-24-plan-05-reservations-reports.md` — Módulo de reservas (Reservation) y reportes/exportaciones (Excel, PDF).