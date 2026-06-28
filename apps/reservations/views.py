from django.db import transaction
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.spaces.models import ParkingSpace, SpaceState
from apps.users.models import User
from apps.users.permissions import IsJefeOperacionesOrAbove
from .models import Reservation, ReservationState
from .serializers import ReservationCreateSerializer, ReservationSerializer


class ReservationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    permission_classes = [IsJefeOperacionesOrAbove]
    serializer_class = ReservationSerializer

    def get_queryset(self):
        user = self.request.user
        return Reservation.objects.filter(
            campus=user.campus_asignado,
            estado=ReservationState.ACTIVA,
        ).select_related('space', 'reservado_por', 'beneficiario', 'campus')

    def create(self, request):
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_campus = request.user.campus_asignado
        space = ParkingSpace.objects.filter(
            id=data['space_id'], lot__campus=user_campus
        ).first()
        if not space:
            return Response(
                {'detail': 'Espacio no encontrado en su campus.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if space.estado != SpaceState.LIBRE:
            return Response(
                {'detail': 'El espacio no está disponible.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        beneficiario = None
        if data.get('beneficiario_id'):
            beneficiario = User.objects.filter(id=data['beneficiario_id']).first()

        try:
            with transaction.atomic():
                reservation = Reservation(
                    space=space,
                    reservado_por=request.user,
                    beneficiario=beneficiario,
                    campus=request.user.campus_asignado,
                    inicio=data['inicio'],
                    fin=data['fin'],
                    motivo=data['motivo'],
                )
                reservation.full_clean()
                reservation.save()
                space.estado = SpaceState.RESERVADO
                space.save(update_fields=['estado'])
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        reservation = self.get_object()
        with transaction.atomic():
            reservation.estado = ReservationState.CANCELADA
            reservation.save(update_fields=['estado'])
            from apps.access.models import AccessRecord, AccessState
            space = reservation.space
            has_active = AccessRecord.objects.filter(
                space=space, estado=AccessState.ACTIVO
            ).exists()
            if not has_active:
                space.estado = SpaceState.LIBRE
                space.save(update_fields=['estado'])
        return Response(status=status.HTTP_204_NO_CONTENT)
