from django.db import transaction
from rest_framework import status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import GenericViewSet

from apps.users.models import Role, UserState
from apps.users.permissions import IsOperativoOrAbove, IsJefeSeguridad
from .models import Violation, ViolationType, ViolationState, Sanction, SanctionState
from .sanctions import apply_sanction
from .serializers import ViolationCreateSerializer, ViolationSerializer, ViolationTypeNestedSerializer


class ViolationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    serializer_class = ViolationSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsOperativoOrAbove()]
        if self.action in ('confirm', 'annul'):
            return [IsJefeSeguridad()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Violation.objects.select_related(
            'user', 'vehicle', 'campus', 'tipo_falta', 'registrado_por'
        )
        if user.rol == Role.RECTOR:
            return qs.all()
        if user.rol in (
            Role.DIRECTOR, Role.JEFE_OPERACIONES, Role.JEFE_SEGURIDAD,
            Role.ASISTENTE_OPERACIONES,
        ):
            return qs.filter(campus=user.campus_asignado)
        return qs.filter(registrado_por=user)

    def create(self, request):
        serializer = ViolationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        from apps.users.models import User, Vehicle
        user = User.objects.get(id=data['user_id'])
        tipo_falta = ViolationType.objects.get(id=data['tipo_falta_id'])
        campus = request.user.campus_asignado

        vehicle = None
        if data.get('vehicle_id'):
            vehicle = Vehicle.objects.filter(id=data['vehicle_id']).first()

        access_record = None
        if data.get('access_record_id'):
            from apps.access.models import AccessRecord
            access_record = AccessRecord.objects.filter(id=data['access_record_id']).first()

        violation = Violation.objects.create(
            user=user,
            vehicle=vehicle,
            campus=campus,
            tipo_falta=tipo_falta,
            descripcion=data['descripcion'],
            registrado_por=request.user,
            access_record=access_record,
        )
        return Response(ViolationSerializer(violation).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='types', permission_classes=[IsOperativoOrAbove])
    def types(self, request):
        qs = ViolationType.objects.all().order_by('nivel', 'codigo')
        return Response(ViolationTypeNestedSerializer(qs, many=True).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        violation = self.get_object()
        if violation.estado != ViolationState.PENDIENTE:
            return Response(
                {'detail': 'Solo se pueden confirmar violaciones pendientes.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        sanction = apply_sanction(violation, applied_by=request.user)
        return Response({
            'detail': 'Sanción confirmada.',
            'sancion_id': sanction.id,
            'tipo': sanction.tipo,
            'fin': sanction.fin,
        })

    @action(detail=True, methods=['post'])
    def annul(self, request, pk=None):
        violation = self.get_object()
        if violation.estado not in (ViolationState.PENDIENTE, ViolationState.CONFIRMADA):
            return Response(
                {'detail': 'No se puede anular esta violación.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            violation.estado = ViolationState.ANULADA
            violation.save(update_fields=['estado'])
            try:
                sanction = violation.sanction
                sanction.estado = SanctionState.ANULADA
                sanction.save(update_fields=['estado'])
                user = violation.user
                if user.estado == UserState.SUSPENDIDO:
                    user.estado = UserState.ACTIVO
                    user.suspension_hasta = None
                    user.save(update_fields=['estado', 'suspension_hasta'])
            except Sanction.DoesNotExist:
                pass
        return Response({'detail': 'Violación anulada.'})


class MyViolationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        violations = Violation.objects.filter(
            user=request.user
        ).select_related('tipo_falta', 'campus', 'registrado_por').order_by('-fecha')
        return Response(ViolationSerializer(violations, many=True).data)
