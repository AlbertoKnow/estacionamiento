import pytest
from apps.users.models import User, Role, Vehicle
from apps.spaces.models import Campus, ParkingLot, ParkingSpace, SpaceType


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
def space_a01(sotano2):
    return ParkingSpace.objects.create(lot=sotano2, numero='A-01', tipo=SpaceType.AUTO)


@pytest.fixture
def space_a02(sotano2):
    return ParkingSpace.objects.create(lot=sotano2, numero='A-02', tipo=SpaceType.AUTO)


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
def vehicle(db, user_alumno):
    return Vehicle.objects.create(
        user=user_alumno, placa='ABC-123',
        tipo='auto', marca='Toyota', modelo='Corolla', color='Blanco',
    )


@pytest.fixture
def mock_rsa_keys(settings):
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    settings.QR_PRIVATE_KEY = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    settings.QR_PUBLIC_KEY = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
