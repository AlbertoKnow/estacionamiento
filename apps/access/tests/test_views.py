import pytest
from rest_framework.test import APIClient
from apps.users.models import User, Role, Vehicle
from apps.spaces.models import Campus, ParkingLot, ParkingSpace, SpaceType, SpaceState


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
def sotano2(campus_arequipa):
    return ParkingLot.objects.create(campus=campus_arequipa, nombre='Sótano 2', nivel=-2)


@pytest.fixture
def free_space(sotano2):
    return ParkingSpace.objects.create(lot=sotano2, numero='A-01', tipo=SpaceType.AUTO)


@pytest.fixture
def auth_alumno(campus_arequipa, db):
    client = APIClient()
    user = User.objects.create_user(
        codigo_institucional='ALU001', email='alu001@utp.edu.pe',
        password='testpass123', nombre='Luis', apellido='Torres',
        rol=Role.ALUMNO, campus_asignado=campus_arequipa,
    )
    vehicle = Vehicle.objects.create(
        user=user, placa='ABC-123', tipo='auto',
        marca='Toyota', modelo='Corolla', color='Blanco',
    )
    login = client.post('/api/v1/auth/login/', {
        'codigo_institucional': 'ALU001', 'password': 'testpass123',
    })
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
    return client, user, vehicle


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


@pytest.mark.django_db
class TestGenerateEntryQR:
    def test_user_can_generate_entry_qr(self, auth_alumno, mock_rsa_keys):
        client, user, vehicle = auth_alumno
        response = client.post('/api/v1/access/qr/entry/', {'vehicle_id': vehicle.id})
        assert response.status_code == 200
        assert 'token' in response.data
        assert response.data['expires_in'] == 300

    def test_user_cannot_generate_qr_for_other_vehicle(self, auth_alumno, mock_rsa_keys, db):
        client, user, vehicle = auth_alumno
        other_user = User.objects.create_user(
            codigo_institucional='OTH001', email='oth@utp.edu.pe',
            password='x', nombre='Otro', apellido='Usuario', rol=Role.ALUMNO,
        )
        other_vehicle = Vehicle.objects.create(
            user=other_user, placa='OTR-999', tipo='auto',
            marca='Honda', modelo='Civic', color='Rojo',
        )
        response = client.post('/api/v1/access/qr/entry/', {'vehicle_id': other_vehicle.id})
        assert response.status_code == 400

    def test_agente_cannot_generate_entry_qr(self, auth_agente):
        client, _ = auth_agente
        response = client.post('/api/v1/access/qr/entry/', {'vehicle_id': 1})
        assert response.status_code == 403


@pytest.mark.django_db
class TestEntryRegistration:
    def test_agente_registers_entry_successfully(
        self, auth_agente, auth_alumno, free_space, mock_rsa_keys
    ):
        _, user_alumno, vehicle = auth_alumno
        from apps.access.qr import generate_entry_token
        token = generate_entry_token(
            user_id=user_alumno.id,
            vehicle_id=vehicle.id,
            campus_id=free_space.lot.campus.id,
        )
        client_agente, _ = auth_agente
        response = client_agente.post('/api/v1/access/entry/', {
            'token': token, 'space_id': free_space.id,
        })
        assert response.status_code == 200
        assert 'session_token' in response.data
        assert 'access_record_id' in response.data
        free_space.refresh_from_db()
        assert free_space.estado == 'ocupado'

    def test_suspended_user_blocked_at_entry(
        self, auth_agente, auth_alumno, free_space, mock_rsa_keys
    ):
        from django.utils import timezone
        _, user_alumno, vehicle = auth_alumno
        user_alumno.estado = 'suspendido'
        user_alumno.suspension_hasta = timezone.now().date() + timezone.timedelta(days=30)
        user_alumno.save()

        from apps.access.qr import generate_entry_token
        token = generate_entry_token(
            user_id=user_alumno.id,
            vehicle_id=vehicle.id,
            campus_id=free_space.lot.campus.id,
        )
        client_agente, _ = auth_agente
        response = client_agente.post('/api/v1/access/entry/', {
            'token': token, 'space_id': free_space.id,
        })
        assert response.status_code == 400
        assert 'suspendido' in response.data['detail'].lower()

    def test_used_qr_token_rejected(
        self, auth_agente, auth_alumno, free_space, mock_rsa_keys
    ):
        _, user_alumno, vehicle = auth_alumno
        from apps.access.qr import generate_entry_token
        token = generate_entry_token(
            user_id=user_alumno.id,
            vehicle_id=vehicle.id,
            campus_id=free_space.lot.campus.id,
        )
        client_agente, _ = auth_agente
        client_agente.post('/api/v1/access/entry/', {'token': token, 'space_id': free_space.id})
        space2 = ParkingSpace.objects.create(
            lot=free_space.lot, numero='A-02', tipo=SpaceType.AUTO
        )
        response = client_agente.post('/api/v1/access/entry/', {'token': token, 'space_id': space2.id})
        assert response.status_code == 400
        assert 'usado' in response.data['detail'].lower()


@pytest.mark.django_db
class TestExitRegistration:
    def test_agente_registers_exit_successfully(
        self, auth_agente, auth_alumno, free_space, mock_rsa_keys
    ):
        _, user_alumno, vehicle = auth_alumno
        from apps.access.models import AccessRecord
        from apps.access.qr import generate_session_token

        free_space.estado = SpaceState.OCUPADO
        free_space.save(update_fields=['estado'])
        record = AccessRecord.objects.create(
            user=user_alumno, vehicle=vehicle,
            campus=free_space.lot.campus, space=free_space,
            registrado_por=user_alumno,
        )
        session_token = generate_session_token(
            user_id=user_alumno.id,
            access_record_id=record.id,
            campus_id=free_space.lot.campus.id,
        )

        client_agente, _ = auth_agente
        response = client_agente.post('/api/v1/access/exit/', {'token': session_token})
        assert response.status_code == 200
        assert 'duracion_minutos' in response.data

        free_space.refresh_from_db()
        assert free_space.estado == SpaceState.LIBRE
        record.refresh_from_db()
        assert record.estado == 'completado'
        assert record.salida_at is not None

    def test_exit_with_invalid_token_rejected(self, auth_agente, mock_rsa_keys):
        client_agente, _ = auth_agente
        response = client_agente.post('/api/v1/access/exit/', {'token': 'token.invalido.aqui'})
        assert response.status_code == 400


@pytest.mark.django_db
class TestOfflineExitSync:
    def test_sync_offline_exits(self, auth_agente, auth_alumno, free_space):
        from apps.access.models import AccessRecord
        from django.utils import timezone

        _, user_alumno, vehicle = auth_alumno
        free_space.estado = SpaceState.OCUPADO
        free_space.save(update_fields=['estado'])
        record = AccessRecord.objects.create(
            user=user_alumno, vehicle=vehicle,
            campus=free_space.lot.campus, space=free_space,
            registrado_por=user_alumno,
        )
        salida_at = timezone.now().isoformat()
        client_agente, agente_user = auth_agente
        response = client_agente.post('/api/v1/access/exit/sync/', [
            {'access_record_id': record.id, 'salida_at': salida_at, 'agente_id': agente_user.id}
        ], format='json')
        assert response.status_code == 200
        assert response.data['synced'] == 1
        assert response.data['conflicts'] == []
        free_space.refresh_from_db()
        assert free_space.estado == SpaceState.LIBRE


@pytest.mark.django_db
class TestAccessHistory:
    def test_user_sees_own_history(self, auth_alumno, free_space):
        from apps.access.models import AccessRecord
        client, user_alumno, vehicle = auth_alumno
        AccessRecord.objects.create(
            user=user_alumno, vehicle=vehicle,
            campus=free_space.lot.campus, space=free_space,
            registrado_por=user_alumno,
        )
        response = client.get('/api/v1/access/history/')
        assert response.status_code == 200
        assert len(response.data) == 1

    def test_user_cannot_see_other_user_history(self, auth_alumno, campus_arequipa):
        other = User.objects.create_user(
            codigo_institucional='OTH002', email='oth2@utp.edu.pe',
            password='x', nombre='Otro', apellido='Dos',
            rol=Role.ALUMNO, campus_asignado=campus_arequipa,
        )
        client, user_alumno, _ = auth_alumno
        response = client.get(f'/api/v1/access/history/?user_id={other.id}')
        assert response.status_code == 403
