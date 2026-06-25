import pytest
from rest_framework.test import APIClient
from apps.users.models import User, Role, UserState
from apps.violations.models import ViolationType, Violation, ViolationLevel, ViolationState


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
        defaults={'tipo_sancion': SanctionType.SUSPENSION_TEMPORAL, 'duracion_meses': 1},
    )
    SanctionRule.objects.get_or_create(
        nivel_falta='leve', numero_reincidencia=3,
        defaults={'tipo_sancion': SanctionType.SUSPENSION_TEMPORAL, 'duracion_meses': 3},
    )


@pytest.fixture
def auth_agente(campus_arequipa, db):
    client = APIClient()
    user = User.objects.create_user(
        codigo_institucional='AGT001', email='agt001@utp.edu.pe',
        password='testpass123', nombre='Pedro', apellido='Quispe',
        rol=Role.AGENTE_SEGURIDAD, campus_asignado=campus_arequipa,
    )
    login = client.post('/api/v1/auth/login/', {
        'codigo_institucional': 'AGT001', 'password': 'testpass123',
    })
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
    return client, user


@pytest.fixture
def auth_jefe_ops(campus_arequipa, db):
    client = APIClient()
    user = User.objects.create_user(
        codigo_institucional='JOP001', email='jop001@utp.edu.pe',
        password='testpass123', nombre='Sara', apellido='Mamani',
        rol=Role.JEFE_OPERACIONES, campus_asignado=campus_arequipa,
    )
    login = client.post('/api/v1/auth/login/', {
        'codigo_institucional': 'JOP001', 'password': 'testpass123',
    })
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
    return client, user


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
        assert response.data['sancion_propuesta']['tipo_sancion'] == 'advertencia'

    def test_alumno_cannot_register_violation(self, user_alumno, violation_type_leve):
        client = APIClient()
        login = client.post('/api/v1/auth/login/', {
            'codigo_institucional': 'ALU001', 'password': 'testpass123',
        })
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = client.post('/api/v1/violations/', {
            'user_id': user_alumno.id,
            'tipo_falta_id': violation_type_leve.id,
            'descripcion': 'Test',
        })
        assert response.status_code == 403

    def test_unauthenticated_cannot_register(self, user_alumno, violation_type_leve):
        client = APIClient()
        response = client.post('/api/v1/violations/', {
            'user_id': user_alumno.id,
            'tipo_falta_id': violation_type_leve.id,
            'descripcion': 'Test',
        })
        assert response.status_code == 401


@pytest.mark.django_db
class TestConfirmViolation:
    def test_jefe_ops_confirms_violation_and_suspends_user(
        self, auth_jefe_ops, auth_agente, user_alumno,
        violation_type_leve, sanction_rules, campus_arequipa,
    ):
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve,
            descripcion='Primera falta',
            registrado_por=user_alumno,
            estado=ViolationState.CONFIRMADA,
        )
        client_agente, _ = auth_agente
        response = client_agente.post('/api/v1/violations/', {
            'user_id': user_alumno.id,
            'tipo_falta_id': violation_type_leve.id,
            'descripcion': 'Segunda falta',
        })
        assert response.status_code == 201
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

    def test_cannot_confirm_already_confirmed(
        self, auth_jefe_ops, user_alumno, violation_type_leve, campus_arequipa, sanction_rules
    ):
        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve,
            descripcion='Falta', registrado_por=user_alumno,
            estado=ViolationState.CONFIRMADA,
        )
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve,
            descripcion='Falta 2', registrado_por=user_alumno,
            estado=ViolationState.CONFIRMADA,
        )
        from apps.violations.models import Sanction, SanctionType, SanctionState
        client, jefe = auth_jefe_ops
        Sanction.objects.create(
            user=user_alumno, violation=v,
            tipo=SanctionType.ADVERTENCIA,
            aplicada_por=jefe,
            estado=SanctionState.ACTIVA,
        )
        response = client.post(f'/api/v1/violations/{v.id}/confirm/')
        assert response.status_code == 400


@pytest.mark.django_db
class TestAnnulViolation:
    def test_jefe_ops_can_annul_pending_violation(
        self, auth_jefe_ops, user_alumno, violation_type_leve, campus_arequipa
    ):
        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve,
            descripcion='Falta', registrado_por=user_alumno,
        )
        client, _ = auth_jefe_ops
        response = client.post(f'/api/v1/violations/{v.id}/annul/')
        assert response.status_code == 200
        v.refresh_from_db()
        assert v.estado == ViolationState.ANULADA


@pytest.mark.django_db
class TestMyViolations:
    def test_user_sees_own_violations(
        self, user_alumno, campus_arequipa, violation_type_leve
    ):
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve,
            descripcion='Mi falta', registrado_por=user_alumno,
        )
        client = APIClient()
        login = client.post('/api/v1/auth/login/', {
            'codigo_institucional': 'ALU001', 'password': 'testpass123',
        })
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        response = client.get('/api/v1/violations/my/')
        assert response.status_code == 200
        assert len(response.data) == 1
