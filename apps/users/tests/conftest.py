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
