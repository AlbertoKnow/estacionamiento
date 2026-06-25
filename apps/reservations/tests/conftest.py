import pytest
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
