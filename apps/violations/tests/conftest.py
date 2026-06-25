import pytest
from apps.users.models import User, Role, Vehicle
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


@pytest.fixture
def sanction_rules(db):
    from apps.violations.models import SanctionRule, SanctionType
    rules = [
        ('leve',      1, SanctionType.ADVERTENCIA,           None),
        ('leve',      2, SanctionType.SUSPENSION_TEMPORAL,   1),
        ('leve',      3, SanctionType.SUSPENSION_TEMPORAL,   3),
        ('grave',     1, SanctionType.SUSPENSION_TEMPORAL,   3),
        ('grave',     2, SanctionType.SUSPENSION_TEMPORAL,   6),
        ('grave',     3, SanctionType.SUSPENSION_TEMPORAL,   12),
        ('muy_grave', 1, SanctionType.SUSPENSION_TEMPORAL,   12),
        ('muy_grave', 2, SanctionType.SUSPENSION_TEMPORAL,   24),
        ('muy_grave', 3, SanctionType.SUSPENSION_DEFINITIVA, None),
    ]
    for nivel, reincidencia, tipo, meses in rules:
        SanctionRule.objects.get_or_create(
            nivel_falta=nivel, numero_reincidencia=reincidencia,
            defaults={'tipo_sancion': tipo, 'duracion_meses': meses},
        )
