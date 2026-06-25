import pytest
from apps.spaces.models import Campus, ParkingLot


@pytest.fixture
def campus_arequipa(db):
    return Campus.objects.create(
        nombre='Campus Arequipa',
        ciudad='Arequipa',
        direccion='Av. Parra 201-203',
        horario_operacion={
            'lunes_sabado': {'inicio': '06:30', 'fin': '22:30'},
            'domingo': {'inicio': '07:00', 'fin': '15:00'},
        },
    )


@pytest.fixture
def sotano2(campus_arequipa):
    return ParkingLot.objects.create(
        campus=campus_arequipa,
        nombre='Sótano 2',
        nivel=-2,
    )


@pytest.fixture
def sotano3(campus_arequipa):
    return ParkingLot.objects.create(
        campus=campus_arequipa,
        nombre='Sótano 3',
        nivel=-3,
    )
