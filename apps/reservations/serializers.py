from rest_framework import serializers
from apps.spaces.models import ParkingSpace
from apps.users.models import User
from .models import Reservation


class ReservationCreateSerializer(serializers.Serializer):
    space_id = serializers.IntegerField()
    inicio = serializers.DateTimeField()
    fin = serializers.DateTimeField()
    motivo = serializers.CharField(max_length=255)
    beneficiario_id = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, data):
        if data['fin'] <= data['inicio']:
            raise serializers.ValidationError('La fecha de fin debe ser posterior al inicio.')
        if not ParkingSpace.objects.filter(id=data['space_id']).exists():
            raise serializers.ValidationError({'space_id': 'Espacio no encontrado.'})
        return data


class ReservationSerializer(serializers.ModelSerializer):
    space_numero = serializers.CharField(source='space.numero', read_only=True)
    reservado_por_nombre = serializers.SerializerMethodField()
    beneficiario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = (
            'id', 'space', 'space_numero', 'reservado_por', 'reservado_por_nombre',
            'beneficiario', 'beneficiario_nombre', 'campus',
            'inicio', 'fin', 'motivo', 'estado', 'created_at',
        )
        read_only_fields = ('reservado_por', 'campus', 'estado', 'created_at')

    def get_reservado_por_nombre(self, obj):
        return obj.reservado_por.get_full_name()

    def get_beneficiario_nombre(self, obj):
        return obj.beneficiario.get_full_name() if obj.beneficiario else None
