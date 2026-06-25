import pytest
from apps.access.models import AccessRecord, AccessState


@pytest.mark.django_db
class TestAccessRecord:
    def test_create_active_record(self, user_alumno, vehicle, campus_arequipa, space_a01, user_agente):
        record = AccessRecord.objects.create(
            user=user_alumno,
            vehicle=vehicle,
            campus=campus_arequipa,
            space=space_a01,
            registrado_por=user_agente,
        )
        assert record.estado == AccessState.ACTIVO
        assert record.entrada_at is not None
        assert record.salida_at is None

    def test_user_cannot_have_two_active_records(
        self, user_alumno, vehicle, campus_arequipa, space_a01, space_a02, user_agente
    ):
        AccessRecord.objects.create(
            user=user_alumno, vehicle=vehicle, campus=campus_arequipa,
            space=space_a01, registrado_por=user_agente,
        )
        with pytest.raises(Exception, match='activo'):
            record = AccessRecord(
                user=user_alumno, vehicle=vehicle, campus=campus_arequipa,
                space=space_a02, registrado_por=user_agente,
            )
            record.full_clean()
