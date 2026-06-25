from rest_framework import serializers
from apps.users.models import Vehicle
from apps.spaces.models import ParkingSpace, SpaceState


class EntryQRRequestSerializer(serializers.Serializer):
    vehicle_id = serializers.IntegerField()

    def validate_vehicle_id(self, value):
        user = self.context['request'].user
        if not Vehicle.objects.filter(id=value, user=user, activo=True).exists():
            raise serializers.ValidationError(
                'Vehículo no encontrado o no pertenece al usuario.'
            )
        return value


class EntryRequestSerializer(serializers.Serializer):
    token = serializers.CharField(help_text='JWT QR de entrada (type=entry)')
    space_id = serializers.IntegerField(help_text='ID del espacio asignado por el agente')

    def validate_space_id(self, value):
        space = ParkingSpace.objects.filter(id=value, estado=SpaceState.LIBRE).first()
        if not space:
            raise serializers.ValidationError('Espacio no disponible o no existe.')
        return value


class ExitRequestSerializer(serializers.Serializer):
    token = serializers.CharField(help_text='JWT QR de sesión (type=exit)')


class OfflineExitSerializer(serializers.Serializer):
    access_record_id = serializers.IntegerField()
    salida_at = serializers.DateTimeField()
    agente_id = serializers.IntegerField()
