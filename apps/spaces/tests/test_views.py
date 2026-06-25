import pytest
from rest_framework.test import APIClient
from apps.users.models import User, Role
from apps.spaces.models import Campus, ParkingLot, ParkingSpace, SpaceType, SpaceState


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def campus_arequipa(db):
    return Campus.objects.create(
        nombre='Campus Arequipa',
        ciudad='Arequipa',
        direccion='Av. Parra 201',
        horario_operacion={},
    )


@pytest.fixture
def sotano2(campus_arequipa):
    return ParkingLot.objects.create(campus=campus_arequipa, nombre='Sótano 2', nivel=-2)


@pytest.fixture
def auth_director(api_client, campus_arequipa, db):
    user = User.objects.create_user(
        codigo_institucional='DIR001',
        email='dir001@utp.edu.pe',
        password='testpass123',
        nombre='Diana',
        apellido='Directora',
        rol=Role.DIRECTOR,
        campus_asignado=campus_arequipa,
    )
    login = api_client.post('/api/v1/auth/login/', {
        'codigo_institucional': 'DIR001', 'password': 'testpass123',
    })
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
    return api_client, user


@pytest.fixture
def auth_alumno(api_client, campus_arequipa, db):
    user = User.objects.create_user(
        codigo_institucional='ALU001',
        email='alu001@utp.edu.pe',
        password='testpass123',
        nombre='Luis',
        apellido='Torres',
        rol=Role.ALUMNO,
        campus_asignado=campus_arequipa,
    )
    login = api_client.post('/api/v1/auth/login/', {
        'codigo_institucional': 'ALU001', 'password': 'testpass123',
    })
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
    return api_client, user


@pytest.mark.django_db
class TestCampusEndpoints:
    def test_any_authenticated_user_can_list_campus(self, auth_alumno):
        client, _ = auth_alumno
        response = client.get('/api/v1/campus/')
        assert response.status_code == 200

    def test_alumno_cannot_create_campus(self, auth_alumno):
        client, _ = auth_alumno
        response = client.post('/api/v1/campus/', {
            'nombre': 'Nuevo', 'ciudad': 'Lima', 'direccion': 'Calle X',
            'horario_operacion': {},
        }, format='json')
        assert response.status_code == 403

    def test_director_can_create_campus(self, auth_director):
        client, _ = auth_director
        response = client.post('/api/v1/campus/', {
            'nombre': 'Campus Lima', 'ciudad': 'Lima',
            'direccion': 'Av. Arequipa 660',
            'horario_operacion': {'lunes_sabado': {'inicio': '07:00', 'fin': '22:00'}},
        }, format='json')
        assert response.status_code == 201
        assert Campus.objects.filter(nombre='Campus Lima').exists()


@pytest.mark.django_db
class TestParkingSpaceEndpoints:
    def test_director_can_create_space(self, auth_director, sotano2):
        client, _ = auth_director
        response = client.post(
            f'/api/v1/campus/{sotano2.campus.id}/lots/{sotano2.id}/spaces/',
            {'numero': 'A-01', 'tipo': SpaceType.AUTO},
        )
        assert response.status_code == 201
        assert ParkingSpace.objects.filter(numero='A-01', lot=sotano2).exists()

    def test_alumno_cannot_create_space(self, auth_alumno, sotano2):
        client, _ = auth_alumno
        response = client.post(
            f'/api/v1/campus/{sotano2.campus.id}/lots/{sotano2.id}/spaces/',
            {'numero': 'B-01', 'tipo': SpaceType.AUTO},
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestOccupancy:
    def test_occupancy_returns_counts_by_lot(self, auth_alumno, campus_arequipa, sotano2):
        ParkingSpace.objects.create(lot=sotano2, numero='A-01', tipo=SpaceType.AUTO, estado=SpaceState.LIBRE)
        ParkingSpace.objects.create(lot=sotano2, numero='A-02', tipo=SpaceType.AUTO, estado=SpaceState.OCUPADO)
        ParkingSpace.objects.create(lot=sotano2, numero='A-03', tipo=SpaceType.MOTO, estado=SpaceState.LIBRE)

        client, _ = auth_alumno
        response = client.get(f'/api/v1/campus/{campus_arequipa.id}/occupancy/')
        assert response.status_code == 200
        assert len(response.data['lots']) == 1
        lot_data = response.data['lots'][0]
        assert lot_data['nombre'] == 'Sótano 2'
        assert lot_data['total'] == 3
        assert lot_data['libres'] == 2
        assert lot_data['ocupados'] == 1
        assert lot_data['reservados'] == 0

    def test_occupancy_includes_breakdown_by_type(self, auth_alumno, campus_arequipa, sotano2):
        ParkingSpace.objects.create(lot=sotano2, numero='M-01', tipo=SpaceType.MOTO, estado=SpaceState.LIBRE)
        ParkingSpace.objects.create(lot=sotano2, numero='D-01', tipo=SpaceType.DISCAPACITADO, estado=SpaceState.LIBRE)

        client, _ = auth_alumno
        response = client.get(f'/api/v1/campus/{campus_arequipa.id}/occupancy/')
        assert response.status_code == 200
        by_type = response.data['lots'][0]['por_tipo']
        assert 'moto' in by_type
        assert 'discapacitado' in by_type
