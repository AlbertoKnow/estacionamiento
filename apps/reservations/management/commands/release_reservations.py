from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.access.models import AccessRecord, AccessState
from apps.reservations.models import Reservation, ReservationState
from apps.spaces.models import SpaceState


class Command(BaseCommand):
    help = 'Vence reservas cuyo horario fin ya pasó y libera el espacio si está desocupado'

    def handle(self, *args, **options):
        now = timezone.now()
        expired = Reservation.objects.filter(
            estado=ReservationState.ACTIVA,
            fin__lt=now,
        ).select_related('space')

        count = 0
        for reservation in expired:
            with transaction.atomic():
                reservation.estado = ReservationState.VENCIDA
                reservation.save(update_fields=['estado'])
                space = reservation.space
                has_active = AccessRecord.objects.filter(
                    space=space, estado=AccessState.ACTIVO
                ).exists()
                if not has_active and space.estado == SpaceState.RESERVADO:
                    space.estado = SpaceState.LIBRE
                    space.save(update_fields=['estado'])
            count += 1

        self.stdout.write(self.style.SUCCESS(f'{count} reserva(s) vencida(s) procesada(s).'))
