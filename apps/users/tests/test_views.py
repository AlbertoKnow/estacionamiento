import io
import pytest
import openpyxl
from rest_framework.test import APIClient

from apps.users.models import User, Vehicle, Role


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
        assert response.status_code == 400

    def test_login_inactive_user(self, api_client, alumno_credentials):
        user, password = alumno_credentials
        user.is_active = False
        user.save()
        response = api_client.post('/api/v1/auth/login/', {
            'codigo_institucional': user.codigo_institucional,
            'password': password,
        })
        assert response.status_code == 400


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

        response2 = api_client.post('/api/v1/auth/refresh/', {'refresh': refresh_token})
        assert response2.status_code == 401


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

        response = client.post('/api/v1/users/import/', {'file': buffer}, format='multipart')
        assert response.status_code == 200
        assert response.data['created'] == 2
        assert User.objects.filter(codigo_institucional='IMP001').exists()

    def test_import_reports_errors_without_aborting(self, auth_jefe_ops):
        client, _ = auth_jefe_ops
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(['codigo_institucional', 'email', 'nombre', 'apellido', 'rol'])
        ws.append(['GOOD001', 'good@utp.edu.pe', 'Bueno', 'Uno', 'alumno'])
        ws.append(['', 'bad@utp.edu.pe', 'Malo', '', 'rol_invalido'])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)

        response = client.post('/api/v1/users/import/', {'file': buffer}, format='multipart')
        assert response.status_code == 200
        assert response.data['created'] == 1
        assert len(response.data['errors']) == 1
