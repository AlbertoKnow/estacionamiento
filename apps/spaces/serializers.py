from rest_framework import serializers
from .models import Campus, ParkingLot, ParkingSpace


class ParkingSpaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParkingSpace
        fields = ('id', 'numero', 'tipo', 'estado')
        read_only_fields = ('id', 'estado')


class ParkingLotSerializer(serializers.ModelSerializer):
    spaces_count = serializers.SerializerMethodField()
    free_count = serializers.SerializerMethodField()

    class Meta:
        model = ParkingLot
        fields = ('id', 'nombre', 'nivel', 'spaces_count', 'free_count')

    def get_spaces_count(self, obj):
        return obj.spaces.count()

    def get_free_count(self, obj):
        return obj.spaces.filter(estado='libre').count()


class CampusSerializer(serializers.ModelSerializer):
    lots = ParkingLotSerializer(many=True, read_only=True)

    class Meta:
        model = Campus
        fields = ('id', 'nombre', 'ciudad', 'direccion', 'horario_operacion', 'activo', 'lots')
        read_only_fields = ('id',)


class CampusListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campus
        fields = ('id', 'nombre', 'ciudad', 'activo')
