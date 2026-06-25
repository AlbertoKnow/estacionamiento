import pytest
from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APIClient
from apps.spaces.models import SpaceState


def _login(codigo, password='testpass123'):
    client = APIClient()
    r = client.post('/api/v1/auth/login/', {
        'codigo_institucional': codigo, 'password': password,
    })
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
    return client


@pytest.mark.django_db
class TestCreateReservation:
    def test_director_can_create_reservation(self, user_director, space_libre):
        client = _login('DIR001')
        inicio = (timezone.now() + timedelta(hours=1)).isoformat()
        fin = (timezone.now() + timedelta(hours=3)).isoformat()
        response = client.post('/api/v1/reservations/', {
            'space_id': space_libre.id,
            'inicio': inicio,
            'fin': fin,
            'motivo': 'Visita directorio',
        })
        assert response.status_code == 201
        space_libre.refresh_from_db()
        assert space_libre.estado == SpaceState.RESERVADO

    def test_jefe_ops_can_create_reservation(self, user_jefe_ops, space_libre):
        client = _login('JOP001')
        inicio = (timezone.now() + timedelta(hours=1)).isoformat()
        fin = (timezone.now() + timedelta(hours=2)).isoformat()
        response = client.post('/api/v1/reservations/', {
            'space_id': space_libre.id,
            'inicio': inicio,
            'fin': fin,
            'motivo': 'Reunión operativa',
        })
        assert response.status_code == 201

    def test_alumno_cannot_create_reservation(self, user_alumno, space_libre):
        client = _login('ALU001')
        inicio = (timezone.now() + timedelta(hours=1)).isoformat()
        fin = (timezone.now() + timedelta(hours=2)).isoformat()
        response = client.post('/api/v1/reservations/', {
            'space_id': space_libre.id,
            'inicio': inicio,
            'fin': fin,
            'motivo': 'Test',
        })
        assert response.status_code == 403

    def test_overlapping_reservation_returns_400(
        self, user_director, space_libre, campus_arequipa
    ):
        from apps.reservations.models import Reservation
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=3)
        Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio, fin=fin, motivo='Primera',
        )
        client = _login('DIR001')
        response = client.post('/api/v1/reservations/', {
            'space_id': space_libre.id,
            'inicio': (inicio + timedelta(hours=1)).isoformat(),
            'fin': (fin + timedelta(hours=1)).isoformat(),
            'motivo': 'Segunda solapada',
        })
        assert response.status_code == 400

    def test_fin_before_inicio_returns_400(self, user_director, space_libre):
        client = _login('DIR001')
        inicio = (timezone.now() + timedelta(hours=3)).isoformat()
        fin = (timezone.now() + timedelta(hours=1)).isoformat()
        response = client.post('/api/v1/reservations/', {
            'space_id': space_libre.id,
            'inicio': inicio,
            'fin': fin,
            'motivo': 'Mal horario',
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestCancelReservation:
    def test_cancel_releases_space(self, user_director, space_libre, campus_arequipa):
        from apps.reservations.models import Reservation
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=2)
        r = Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio, fin=fin, motivo='Test',
        )
        space_libre.estado = SpaceState.RESERVADO
        space_libre.save()

        client = _login('DIR001')
        response = client.delete(f'/api/v1/reservations/{r.id}/')
        assert response.status_code == 204
        space_libre.refresh_from_db()
        assert space_libre.estado == SpaceState.LIBRE

    def test_alumno_cannot_cancel_reservation(self, user_director, user_alumno, space_libre, campus_arequipa):
        from apps.reservations.models import Reservation
        inicio = timezone.now() + timedelta(hours=1)
        fin = inicio + timedelta(hours=2)
        r = Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa, inicio=inicio, fin=fin, motivo='Test',
        )
        client = _login('ALU001')
        response = client.delete(f'/api/v1/reservations/{r.id}/')
        assert response.status_code == 403


@pytest.mark.django_db
class TestListReservations:
    def test_director_can_list_reservations(self, user_director, space_libre, campus_arequipa):
        from apps.reservations.models import Reservation
        Reservation.objects.create(
            space=space_libre, reservado_por=user_director,
            campus=campus_arequipa,
            inicio=timezone.now() + timedelta(hours=1),
            fin=timezone.now() + timedelta(hours=3),
            motivo='Para listar',
        )
        client = _login('DIR001')
        response = client.get('/api/v1/reservations/')
        assert response.status_code == 200
        assert len(response.data) == 1
