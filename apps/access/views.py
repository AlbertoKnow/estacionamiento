from django.conf import settings
from django.db import transaction
from django.utils import timezone as tz
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User, Vehicle, Role as UserRole, UserState
from apps.users.permissions import IsUsuarioFinal, IsOperativoOrAbove
from apps.spaces.models import ParkingSpace, SpaceState
from .models import AccessRecord, AccessState, UsedQRToken
from .qr import generate_entry_token, generate_session_token, verify_token, QRTokenError
from .serializers import (
    EntryQRRequestSerializer,
    EntryRequestSerializer,
    ExitRequestSerializer,
    OfflineExitSerializer,
)


class GenerateEntryQRView(APIView):
    permission_classes = [IsUsuarioFinal]

    def post(self, request):
        serializer = EntryQRRequestSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        vehicle_id = serializer.validated_data['vehicle_id']
        campus_id = request.user.campus_asignado.id if request.user.campus_asignado else None

        if not campus_id:
            return Response(
                {'detail': 'El usuario no tiene campus asignado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = generate_entry_token(
            user_id=request.user.id,
            vehicle_id=vehicle_id,
            campus_id=campus_id,
        )
        return Response({
            'token': token,
            'expires_in': settings.QR_ENTRY_TOKEN_LIFETIME_SECONDS,
        })


class EntryView(APIView):
    permission_classes = [IsOperativoOrAbove]

    def post(self, request):
        serializer = EntryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_str = serializer.validated_data['token']
        space_id = serializer.validated_data['space_id']

        try:
            payload = verify_token(token_str, expected_type='entry')
        except QRTokenError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        jti = payload['jti']
        if UsedQRToken.is_used(jti):
            return Response(
                {'detail': 'Token QR ya usado. Solicite uno nuevo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.select_related('campus_asignado').filter(
            id=payload['user_id']
        ).first()
        if not user:
            return Response({'detail': 'Usuario no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_suspended:
            return Response(
                {'detail': f'Usuario suspendido hasta {user.suspension_hasta}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if AccessRecord.objects.filter(user=user, estado=AccessState.ACTIVO).exists():
            return Response(
                {'detail': 'El usuario ya tiene una entrada activa.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        space = ParkingSpace.objects.select_related('lot__campus').filter(
            id=space_id, estado=SpaceState.LIBRE
        ).first()
        if not space:
            return Response(
                {'detail': 'El espacio no está disponible.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        vehicle = Vehicle.objects.filter(
            id=payload['vehicle_id'], user=user, activo=True
        ).first()
        if not vehicle:
            return Response(
                {'detail': 'Vehículo no registrado o inactivo.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            UsedQRToken.mark_used(jti, user.id)
            space.estado = SpaceState.OCUPADO
            space.save(update_fields=['estado'])
            record = AccessRecord.objects.create(
                user=user,
                vehicle=vehicle,
                campus=space.lot.campus,
                space=space,
                registrado_por=request.user,
            )

        session_token = generate_session_token(
            user_id=user.id,
            access_record_id=record.id,
            campus_id=space.lot.campus.id,
        )

        return Response({
            'access_record_id': record.id,
            'session_token': session_token,
            'space': space.numero,
            'user': {
                'codigo': user.codigo_institucional,
                'nombre': user.get_full_name(),
                'rol': user.rol,
            },
        })


class ExitView(APIView):
    permission_classes = [IsOperativoOrAbove]

    def post(self, request):
        serializer = ExitRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payload = verify_token(serializer.validated_data['token'], expected_type='exit')
        except QRTokenError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        record = AccessRecord.objects.select_related('space').filter(
            id=payload['access_record_id'],
            estado=AccessState.ACTIVO,
        ).first()
        if not record:
            return Response(
                {'detail': 'Registro de acceso no encontrado o ya cerrado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = tz.now()
        duracion = int((now - record.entrada_at).total_seconds() / 60)

        with transaction.atomic():
            record.salida_at = now
            record.estado = AccessState.COMPLETADO
            record.save(update_fields=['salida_at', 'estado'])
            record.space.estado = SpaceState.LIBRE
            record.space.save(update_fields=['estado'])

        return Response({
            'access_record_id': record.id,
            'space': record.space.numero,
            'duracion_minutos': duracion,
        })


class SyncOfflineExitsView(APIView):
    permission_classes = [IsOperativoOrAbove]

    def post(self, request):
        serializer = OfflineExitSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)

        synced, conflicts = 0, []

        for item in serializer.validated_data:
            record = AccessRecord.objects.select_related('space').filter(
                id=item['access_record_id'],
                estado=AccessState.ACTIVO,
            ).first()

            if not record:
                conflicts.append({
                    'access_record_id': item['access_record_id'],
                    'reason': 'Registro no encontrado o ya cerrado (posible conflicto offline).',
                })
                continue

            with transaction.atomic():
                record.salida_at = item['salida_at']
                record.estado = AccessState.COMPLETADO
                record.save(update_fields=['salida_at', 'estado'])
                record.space.estado = SpaceState.LIBRE
                record.space.save(update_fields=['estado'])
            synced += 1

        return Response({'synced': synced, 'conflicts': conflicts})


class AccessHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        requested_user_id = request.query_params.get('user_id')

        if requested_user_id and str(requested_user_id) != str(user.id):
            if user.rol in (UserRole.ALUMNO, UserRole.ACADEMICO, UserRole.ADMINISTRATIVO):
                return Response(
                    {'detail': 'No tiene permiso para ver el historial de otro usuario.'},
                    status=status.HTTP_403_FORBIDDEN,
                )
            target_id = requested_user_id
        else:
            target_id = user.id

        records = AccessRecord.objects.filter(
            user_id=target_id
        ).select_related('vehicle', 'space', 'campus').order_by('-entrada_at')[:100]

        data = [
            {
                'id': r.id,
                'placa': r.vehicle.placa,
                'campus': r.campus.nombre,
                'espacio': r.space.numero,
                'entrada_at': r.entrada_at,
                'salida_at': r.salida_at,
                'estado': r.estado,
            }
            for r in records
        ]
        return Response(data)
