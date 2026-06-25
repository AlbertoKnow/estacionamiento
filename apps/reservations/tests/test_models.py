import pytest
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.reservations.models import Reservation, ReservationState


@pytest.mark.django_db
class TestReservationModel:
    def test_create_reservation(self, space_libre, user_director, campus_arequipa):
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=2)
        r = Reservation.objects.create(
            space=space_libre,
            reservado_por=user_director,
            campus=campus_arequipa,
            inicio=inicio,
            fin=fin,
            motivo='Visita directorio',
        )
        assert r.estado == ReservationState.ACTIVA

    def test_str(self, space_libre, user_director, campus_arequipa):
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=2)
        r = Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio, fin=fin,
            motivo='Test',
        )
        assert str(r)  # just checks it doesn't crash

    def test_fin_before_inicio_raises(self, space_libre, user_director, campus_arequipa):
        inicio = timezone.now() + timedelta(hours=2)
        fin = timezone.now() + timedelta(hours=1)
        with pytest.raises(ValidationError):
            Reservation.objects.create(
                space=space_libre, reservado_por=user_director,
                campus=campus_arequipa, inicio=inicio, fin=fin,
                motivo='Mal horario',
            )

    def test_overlapping_reservation_raises(self, space_libre, user_director, campus_arequipa):
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=3)
        Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio, fin=fin,
            motivo='Primera',
        )
        with pytest.raises(ValidationError):
            Reservation.objects.create(
                space=space_libre, reservado_por=user_director,
                campus=campus_arequipa,
                inicio=inicio + timedelta(hours=1),
                fin=fin + timedelta(hours=1),
                motivo='Segunda solapada',
            )

    def test_non_overlapping_reservations_allowed(self, space_libre, user_director, campus_arequipa):
        inicio1 = timezone.now() + timedelta(hours=1)
        fin1 = inicio1 + timedelta(hours=2)
        inicio2 = fin1 + timedelta(minutes=1)
        fin2 = inicio2 + timedelta(hours=2)
        Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio1, fin=fin1, motivo='Primera',
        )
        r2 = Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio2, fin=fin2, motivo='Segunda',
        )
        assert r2.pk is not None
