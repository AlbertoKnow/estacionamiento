import pytest
from django.core.exceptions import ValidationError

from apps.users.models import User, Vehicle, Role, UserState


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_with_required_fields(self):
        user = User.objects.create_user(
            codigo_institucional='U001',
            email='u001@utp.edu.pe',
            password='testpass123',
            nombre='Juan',
            apellido='Pérez',
            rol=Role.ALUMNO,
        )
        assert user.codigo_institucional == 'U001'
        assert user.rol == Role.ALUMNO
        assert user.estado == UserState.ACTIVO
        assert user.campus_asignado is None

    def test_codigo_institucional_is_unique(self):
        User.objects.create_user(
            codigo_institucional='U002',
            email='u002@utp.edu.pe',
            password='testpass123',
            nombre='Ana',
            apellido='García',
            rol=Role.ALUMNO,
        )
        with pytest.raises(Exception):
            User.objects.create_user(
                codigo_institucional='U002',
                email='u002b@utp.edu.pe',
                password='testpass123',
                nombre='Ana',
                apellido='García',
                rol=Role.ALUMNO,
            )

    def test_rector_has_no_campus(self):
        rector = User.objects.create_user(
            codigo_institucional='R001',
            email='rector@utp.edu.pe',
            password='testpass123',
            nombre='Carlos',
            apellido='Rector',
            rol=Role.RECTOR,
        )
        assert rector.campus_asignado is None

    def test_get_full_name(self):
        user = User.objects.create_user(
            codigo_institucional='U003',
            email='u003@utp.edu.pe',
            password='testpass123',
            nombre='Ana',
            apellido='Torres',
            rol=Role.ALUMNO,
        )
        assert user.get_full_name() == 'Ana Torres'


@pytest.mark.django_db
class TestVehicleModel:
    def test_max_two_vehicles_per_user(self, user_alumno):
        Vehicle.objects.create(
            user=user_alumno, placa='ABC-123',
            tipo='auto', marca='Toyota', modelo='Corolla', color='Blanco',
        )
        Vehicle.objects.create(
            user=user_alumno, placa='XYZ-789',
            tipo='auto', marca='Honda', modelo='Civic', color='Negro',
        )
        with pytest.raises(ValidationError, match='máximo'):
            vehicle = Vehicle(
                user=user_alumno, placa='DEF-456',
                tipo='moto', marca='Yamaha', modelo='FZ', color='Rojo',
            )
            vehicle.full_clean()

    def test_placa_is_unique(self, user_alumno, user_academico):
        Vehicle.objects.create(
            user=user_alumno, placa='ABC-123',
            tipo='auto', marca='Toyota', modelo='Corolla', color='Blanco',
        )
        with pytest.raises(Exception):
            Vehicle.objects.create(
                user=user_academico, placa='ABC-123',
                tipo='auto', marca='Honda', modelo='Civic', color='Negro',
            )
