from rest_framework import mixins, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from apps.users.models import Role
from apps.users.permissions import IsDirectorOrAbove
from .models import Campus, ParkingLot, ParkingSpace, SpaceState
from .serializers import (
    CampusSerializer,
    CampusListSerializer,
    ParkingLotSerializer,
    ParkingSpaceSerializer,
)


class CampusViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    def get_queryset(self):
        user = self.request.user
        if user.rol == Role.RECTOR:
            return Campus.objects.prefetch_related('lots').all()
        if user.campus_asignado:
            return Campus.objects.prefetch_related('lots').filter(id=user.campus_asignado.id)
        return Campus.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return CampusListSerializer
        return CampusSerializer

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsDirectorOrAbove()]
        return [IsAuthenticated()]


class ParkingLotViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = ParkingLotSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ParkingLot.objects.filter(campus_id=self.kwargs['campus_pk'])


class ParkingSpaceViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    GenericViewSet,
):
    serializer_class = ParkingSpaceSerializer

    def get_queryset(self):
        return ParkingSpace.objects.filter(
            lot_id=self.kwargs['lot_pk'],
            lot__campus_id=self.kwargs['campus_pk'],
        )

    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update'):
            return [IsDirectorOrAbove()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        lot = ParkingLot.objects.get(
            id=self.kwargs['lot_pk'],
            campus_id=self.kwargs['campus_pk'],
        )
        serializer.save(lot=lot)


class CampusOccupancyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, campus_pk):
        user = request.user
        if user.rol != Role.RECTOR and (
            not user.campus_asignado or user.campus_asignado.id != int(campus_pk)
        ):
            return Response(
                {'detail': 'No tiene acceso a este campus.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        campus = Campus.objects.filter(id=campus_pk, activo=True).first()
        if not campus:
            return Response({'detail': 'Campus no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        lots_data = []
        for lot in campus.lots.prefetch_related('spaces'):
            spaces = lot.spaces.all()
            by_type = {}
            for space in spaces:
                tipo = space.tipo
                if tipo not in by_type:
                    by_type[tipo] = {'total': 0, 'libres': 0, 'ocupados': 0, 'reservados': 0}
                by_type[tipo]['total'] += 1
                estado_key = space.estado + 's'
                if estado_key in by_type[tipo]:
                    by_type[tipo][estado_key] += 1

            lots_data.append({
                'id': lot.id,
                'nombre': lot.nombre,
                'nivel': lot.nivel,
                'total': spaces.count(),
                'libres': spaces.filter(estado=SpaceState.LIBRE).count(),
                'ocupados': spaces.filter(estado=SpaceState.OCUPADO).count(),
                'reservados': spaces.filter(estado=SpaceState.RESERVADO).count(),
                'por_tipo': by_type,
            })

        return Response({
            'campus_id': campus.id,
            'campus_nombre': campus.nombre,
            'nota': 'La ocupación refleja espacios asignados por AccessRecord. No hay sensores en v1.',
            'lots': lots_data,
        })
