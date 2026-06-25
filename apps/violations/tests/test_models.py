import pytest
from apps.violations.models import (
    ViolationType, ViolationLevel, ViolationState,
    SanctionRule, SanctionType, Violation, Sanction, SanctionState,
)


@pytest.mark.django_db
class TestViolationType:
    def test_create_violation_type(self, violation_type_leve_e):
        vt = violation_type_leve_e
        assert vt.codigo == 'LEVE_E'
        assert vt.nivel == ViolationLevel.LEVE

    def test_str(self, violation_type_leve_e):
        assert str(violation_type_leve_e) == '[LEVE] LEVE_E'

    def test_codigo_unique(self, db, violation_type_leve_e):
        from django.db import IntegrityError
        with pytest.raises(IntegrityError):
            ViolationType.objects.create(
                codigo='LEVE_E',
                descripcion='Duplicado',
                nivel=ViolationLevel.LEVE,
            )


@pytest.mark.django_db
class TestSanctionRule:
    def test_create_sanction_rule(self, db):
        rule = SanctionRule.objects.create(
            nivel_falta=ViolationLevel.LEVE,
            numero_reincidencia=1,
            tipo_sancion=SanctionType.ADVERTENCIA,
            duracion_meses=None,
        )
        assert rule.tipo_sancion == SanctionType.ADVERTENCIA
        assert rule.duracion_meses is None

    def test_str(self, db):
        rule = SanctionRule.objects.create(
            nivel_falta=ViolationLevel.GRAVE,
            numero_reincidencia=1,
            tipo_sancion=SanctionType.SUSPENSION_TEMPORAL,
            duracion_meses=3,
        )
        assert str(rule) == 'grave #1 → suspension_temporal'

    def test_unique_together(self, db):
        from django.db import IntegrityError
        SanctionRule.objects.create(
            nivel_falta=ViolationLevel.MUY_GRAVE,
            numero_reincidencia=1,
            tipo_sancion=SanctionType.SUSPENSION_TEMPORAL,
            duracion_meses=12,
        )
        with pytest.raises(IntegrityError):
            SanctionRule.objects.create(
                nivel_falta=ViolationLevel.MUY_GRAVE,
                numero_reincidencia=1,
                tipo_sancion=SanctionType.SUSPENSION_DEFINITIVA,
                duracion_meses=None,
            )


@pytest.mark.django_db
class TestViolation:
    def test_create_violation(
        self, user_alumno, user_agente, campus_arequipa, violation_type_leve_e
    ):
        v = Violation.objects.create(
            user=user_alumno,
            campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Estacionado fuera del espacio asignado.',
            registrado_por=user_agente,
        )
        assert v.estado == ViolationState.PENDIENTE
        assert v.vehicle is None
        assert v.access_record is None

    def test_str(
        self, user_alumno, user_agente, campus_arequipa, violation_type_leve_e
    ):
        v = Violation.objects.create(
            user=user_alumno,
            campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Test.',
            registrado_por=user_agente,
        )
        assert 'ALU001' in str(v)
        assert 'LEVE_E' in str(v)

    def test_violation_with_vehicle(
        self, user_alumno, user_agente, campus_arequipa, vehicle, violation_type_leve_e
    ):
        v = Violation.objects.create(
            user=user_alumno,
            vehicle=vehicle,
            campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Con vehículo.',
            registrado_por=user_agente,
        )
        assert v.vehicle == vehicle


@pytest.mark.django_db
class TestSanction:
    def test_create_advertencia_sanction(
        self, user_alumno, user_jefe_ops, campus_arequipa,
        violation_type_leve_e, user_agente,
    ):
        violation = Violation.objects.create(
            user=user_alumno,
            campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Primera falta leve.',
            registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        sanction = Sanction.objects.create(
            user=user_alumno,
            violation=violation,
            tipo=SanctionType.ADVERTENCIA,
            aplicada_por=user_jefe_ops,
        )
        assert sanction.estado == SanctionState.ACTIVA
        assert sanction.inicio is None
        assert sanction.fin is None

    def test_str(
        self, user_alumno, user_jefe_ops, campus_arequipa,
        violation_type_leve_e, user_agente,
    ):
        violation = Violation.objects.create(
            user=user_alumno,
            campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Falta.',
            registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        sanction = Sanction.objects.create(
            user=user_alumno,
            violation=violation,
            tipo=SanctionType.ADVERTENCIA,
            aplicada_por=user_jefe_ops,
        )
        assert 'ALU001' in str(sanction)
        assert 'advertencia' in str(sanction)

    def test_violation_onetoone(
        self, user_alumno, user_jefe_ops, campus_arequipa,
        violation_type_leve_e, user_agente,
    ):
        from django.db import IntegrityError
        violation = Violation.objects.create(
            user=user_alumno,
            campus=campus_arequipa,
            tipo_falta=violation_type_leve_e,
            descripcion='Falta.',
            registrado_por=user_agente,
            estado=ViolationState.CONFIRMADA,
        )
        Sanction.objects.create(
            user=user_alumno, violation=violation,
            tipo=SanctionType.ADVERTENCIA, aplicada_por=user_jefe_ops,
        )
        with pytest.raises(IntegrityError):
            Sanction.objects.create(
                user=user_alumno, violation=violation,
                tipo=SanctionType.SUSPENSION_TEMPORAL, aplicada_por=user_jefe_ops,
            )
