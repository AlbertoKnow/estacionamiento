from dateutil.relativedelta import relativedelta
from django.db import transaction
from django.utils import timezone

from apps.users.models import UserState
from .models import (
    ViolationType, Violation, SanctionRule, Sanction,
    ViolationState, SanctionType, SanctionState,
)


def calculate_sanction(user, violation_type: ViolationType) -> SanctionRule:
    """Determines the applicable rule based on confirmed violations for that level."""
    nivel = violation_type.nivel
    prior_count = Violation.objects.filter(
        user=user,
        tipo_falta__nivel=nivel,
        estado=ViolationState.CONFIRMADA,
    ).count()
    occurrence = min(prior_count + 1, 3)
    return SanctionRule.objects.get(nivel_falta=nivel, numero_reincidencia=occurrence)


def apply_sanction(violation: Violation, applied_by) -> Sanction:
    """Creates the Sanction and updates User.estado if applicable."""
    rule = calculate_sanction(violation.user, violation.tipo_falta)
    today = timezone.now().date()

    fin = None
    if rule.tipo_sancion == SanctionType.SUSPENSION_TEMPORAL and rule.duracion_meses:
        fin = today + relativedelta(months=rule.duracion_meses)

    with transaction.atomic():
        violation.estado = ViolationState.CONFIRMADA
        violation.save(update_fields=['estado'])

        sanction = Sanction.objects.create(
            user=violation.user,
            violation=violation,
            tipo=rule.tipo_sancion,
            inicio=today if rule.tipo_sancion != SanctionType.ADVERTENCIA else None,
            fin=fin,
            aplicada_por=applied_by,
            estado=SanctionState.ACTIVA,
        )

        if rule.tipo_sancion in (SanctionType.SUSPENSION_TEMPORAL, SanctionType.SUSPENSION_DEFINITIVA):
            violation.user.estado = UserState.SUSPENDIDO
            violation.user.suspension_hasta = fin  # None = permanent ban
            violation.user.save(update_fields=['estado', 'suspension_hasta'])

    return sanction


def expire_sanctions():
    """Reactivates users whose temporary suspension has expired. Called daily by cron."""
    today = timezone.now().date()
    expired = Sanction.objects.filter(
        estado=SanctionState.ACTIVA,
        tipo=SanctionType.SUSPENSION_TEMPORAL,
        fin__lt=today,
    ).select_related('user')

    for sanction in expired:
        with transaction.atomic():
            sanction.estado = SanctionState.CUMPLIDA
            sanction.save(update_fields=['estado'])
            user = sanction.user
            user.estado = UserState.ACTIVO
            user.suspension_hasta = None
            user.save(update_fields=['estado', 'suspension_hasta'])
