from rest_framework import serializers
from apps.users.models import User, Vehicle
from .models import ViolationType, Violation, Sanction, SanctionRule
from .sanctions import calculate_sanction


class SanctionProposalSerializer(serializers.Serializer):
    tipo_sancion = serializers.CharField()
    duracion_meses = serializers.IntegerField(allow_null=True)
    numero_reincidencia = serializers.IntegerField()


class ViolationCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    vehicle_id = serializers.IntegerField(required=False, allow_null=True)
    tipo_falta_id = serializers.IntegerField()
    descripcion = serializers.CharField()
    access_record_id = serializers.IntegerField(required=False, allow_null=True)

    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError('Usuario no encontrado.')
        return value

    def validate_tipo_falta_id(self, value):
        if not ViolationType.objects.filter(id=value).exists():
            raise serializers.ValidationError('Tipo de falta no encontrado.')
        return value


class ViolationSerializer(serializers.ModelSerializer):
    tipo_falta_codigo = serializers.CharField(source='tipo_falta.codigo', read_only=True)
    tipo_falta_nivel = serializers.CharField(source='tipo_falta.nivel', read_only=True)
    registrado_por_nombre = serializers.SerializerMethodField()
    sancion_propuesta = serializers.SerializerMethodField()

    class Meta:
        model = Violation
        fields = (
            'id', 'user', 'vehicle', 'campus', 'tipo_falta_codigo', 'tipo_falta_nivel',
            'descripcion', 'fecha', 'estado', 'registrado_por_nombre', 'sancion_propuesta',
        )

    def get_registrado_por_nombre(self, obj):
        return obj.registrado_por.get_full_name()

    def get_sancion_propuesta(self, obj):
        if obj.estado == 'pendiente':
            try:
                rule = calculate_sanction(obj.user, obj.tipo_falta)
                return SanctionProposalSerializer(rule).data
            except Exception:
                return None
        return None


class SanctionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sanction
        fields = ('id', 'tipo', 'inicio', 'fin', 'estado', 'created_at')
