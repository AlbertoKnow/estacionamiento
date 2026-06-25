import pytest
from apps.spaces.models import Campus, ParkingLot, ParkingSpace, SpaceType, SpaceState


@pytest.mark.django_db
class TestCampusModel:
    def test_create_campus(self):
        campus = Campus.objects.create(
            nombre='Campus Arequipa',
            ciudad='Arequipa',
            direccion='Av. Parra 201-203',
            horario_operacion={
                'lunes_sabado': {'inicio': '06:30', 'fin': '22:30'},
                'domingo': {'inicio': '07:00', 'fin': '15:00'},
            },
        )
        assert campus.activo is True
        assert campus.nombre == 'Campus Arequipa'


@pytest.mark.django_db
class TestParkingLotModel:
    def test_create_parking_lot(self, campus_arequipa):
        lot = ParkingLot.objects.create(
            campus=campus_arequipa,
            nombre='Sótano 2',
            nivel=-2,
        )
        assert lot.campus == campus_arequipa
        assert str(lot) == 'Campus Arequipa — Sótano 2'


@pytest.mark.django_db
class TestParkingSpaceModel:
    def test_create_space(self, sotano2):
        space = ParkingSpace.objects.create(
            lot=sotano2,
            numero='A-01',
            tipo=SpaceType.AUTO,
        )
        assert space.estado == SpaceState.LIBRE
        assert str(space) == 'A-01 (Sótano 2)'

    def test_space_numero_unique_within_lot(self, sotano2):
        ParkingSpace.objects.create(lot=sotano2, numero='A-01', tipo=SpaceType.AUTO)
        with pytest.raises(Exception):
            ParkingSpace.objects.create(lot=sotano2, numero='A-01', tipo=SpaceType.MOTO)
