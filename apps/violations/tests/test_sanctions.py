import pytest
from datetime import timedelta
from django.utils import timezone
from apps.violations.models import (
    Violation, SanctionRule, Sanction,
    ViolationLevel, ViolationState, SanctionType, SanctionState,
)
from apps.violations.sanctions import calculate_sanction, apply_sanction, expire_sanctions
from apps.users.models import UserState


@pytest.mark.django_db
class TestCalculateSanction:
    def test_first_leve_gives_advertencia(
        self, user_alumno, violation_type_leve_e, sanction_rules
    ):
        rule = calculate_sanction(user_alumno, violation_type_leve_e)
        assert rule.tipo_sancion == SanctionType.ADVERTENCIA
        assert rule.numero_reincidencia == 1

    def test_second_leve_gives_one_month(
        self, user_alumno, user_agente, campus_arequipa,
        violation_type_leve_e, sanction_rules,
    ):
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Primera', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        rule = calculate_sanction(user_alumno, violation_type_leve_e)
        assert rule.numero_reincidencia == 2
        assert rule.duracion_meses == 1

    def test_counters_are_independent_per_level(
        self, user_alumno, user_agente, campus_arequipa,
        violation_type_leve_e, violation_type_grave_a, sanction_rules,
    ):
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Leve 1', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        rule = calculate_sanction(user_alumno, violation_type_grave_a)
        assert rule.numero_reincidencia == 1
        assert rule.tipo_sancion == SanctionType.SUSPENSION_TEMPORAL
        assert rule.duracion_meses == 3

    def test_capped_at_third_occurrence(
        self, user_alumno, user_agente, campus_arequipa,
        violation_type_leve_e, sanction_rules,
    ):
        for i in range(5):
            Violation.objects.create(
                user=user_alumno, campus=campus_arequipa,
                tipo_falta=violation_type_leve_e,
                descripcion=f'Falta {i}', registrado_por=user_agente,
                estado=ViolationState.CONFIRMADA,
            )
        rule = calculate_sanction(user_alumno, violation_type_leve_e)
        assert rule.numero_reincidencia == 3


@pytest.mark.django_db
class TestApplySanction:
    def test_advertencia_does_not_suspend_user(
        self, user_alumno, user_agente, user_jefe_ops,
        campus_arequipa, violation_type_leve_e, sanction_rules,
    ):
        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Primera leve', registrado_por=user_agente,
        )
        sanction = apply_sanction(v, applied_by=user_jefe_ops)
        assert sanction.tipo == SanctionType.ADVERTENCIA
        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.ACTIVO

    def test_suspension_temporal_suspends_user(
        self, user_alumno, user_agente, user_jefe_ops,
        campus_arequipa, violation_type_leve_e, sanction_rules,
    ):
        Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Primera', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        v2 = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Segunda', registrado_por=user_agente,
        )
        sanction = apply_sanction(v2, applied_by=user_jefe_ops)
        assert sanction.tipo == SanctionType.SUSPENSION_TEMPORAL
        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.SUSPENDIDO
        assert user_alumno.suspension_hasta is not None

    def test_violation_marked_confirmada_after_apply(
        self, user_alumno, user_agente, user_jefe_ops,
        campus_arequipa, violation_type_leve_e, sanction_rules,
    ):
        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Falta', registrado_por=user_agente,
        )
        apply_sanction(v, applied_by=user_jefe_ops)
        v.refresh_from_db()
        assert v.estado == ViolationState.CONFIRMADA


@pytest.mark.django_db
class TestExpireSanctions:
    def test_expired_sanction_reactivates_user(
        self, user_alumno, user_agente, user_jefe_ops,
        campus_arequipa, violation_type_leve_e,
    ):
        yesterday = timezone.now().date() - timedelta(days=1)
        user_alumno.estado = UserState.SUSPENDIDO
        user_alumno.suspension_hasta = yesterday
        user_alumno.save()

        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Falta', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        Sanction.objects.create(
            user=user_alumno, violation=v,
            tipo=SanctionType.SUSPENSION_TEMPORAL,
            inicio=yesterday - timedelta(days=30),
            fin=yesterday,
            aplicada_por=user_jefe_ops,
            estado=SanctionState.ACTIVA,
        )

        expire_sanctions()

        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.ACTIVO
        assert user_alumno.suspension_hasta is None

    def test_active_sanction_not_expired(
        self, user_alumno, user_agente, user_jefe_ops,
        campus_arequipa, violation_type_leve_e,
    ):
        tomorrow = timezone.now().date() + timedelta(days=1)
        user_alumno.estado = UserState.SUSPENDIDO
        user_alumno.suspension_hasta = tomorrow
        user_alumno.save()

        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Falta activa', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        Sanction.objects.create(
            user=user_alumno, violation=v,
            tipo=SanctionType.SUSPENSION_TEMPORAL,
            inicio=timezone.now().date(),
            fin=tomorrow,
            aplicada_por=user_jefe_ops,
            estado=SanctionState.ACTIVA,
        )

        expire_sanctions()

        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.SUSPENDIDO


@pytest.mark.django_db
class TestExpireSanctionsCommand:
    def test_management_command_expires_sanctions(
        self, user_alumno, user_agente, user_jefe_ops,
        campus_arequipa, violation_type_leve_e,
    ):
        yesterday = timezone.now().date() - timedelta(days=1)
        user_alumno.estado = UserState.SUSPENDIDO
        user_alumno.suspension_hasta = yesterday
        user_alumno.save()

        v = Violation.objects.create(
            user=user_alumno, campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Falta', registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        Sanction.objects.create(
            user=user_alumno, violation=v,
            tipo=SanctionType.SUSPENSION_TEMPORAL,
            inicio=yesterday - timedelta(days=30),
            fin=yesterday,
            aplicada_por=user_jefe_ops,
            estado=SanctionState.ACTIVA,
        )

        from django.core.management import call_command
        call_command('expire_sanctions')

        user_alumno.refresh_from_db()
        assert user_alumno.estado == UserState.ACTIVO
