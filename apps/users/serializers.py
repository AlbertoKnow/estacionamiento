from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Vehicle, Role


class LoginSerializer(serializers.Serializer):
    codigo_institucional = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            username=attrs['codigo_institucional'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('Credenciales incorrectas.')
        if not user.is_active:
            raise serializers.ValidationError('Usuario inactivo.')
        attrs['user'] = user
        return attrs


class UserBasicSerializer(serializers.ModelSerializer):
    campus_id = serializers.PrimaryKeyRelatedField(source='campus_asignado', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'codigo_institucional', 'nombre', 'apellido', 'email', 'rol', 'campus_id', 'estado')


class UserSerializer(serializers.ModelSerializer):
    campus_id = serializers.PrimaryKeyRelatedField(source='campus_asignado', read_only=True)
    campus_nombre = serializers.CharField(source='campus_asignado.nombre', read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'codigo_institucional', 'email', 'nombre', 'apellido',
            'rol', 'campus_id', 'campus_nombre', 'estado', 'suspension_hasta', 'created_at',
        )
        read_only_fields = ('id', 'created_at')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            'codigo_institucional', 'email', 'nombre', 'apellido',
            'rol', 'campus_asignado', 'password',
        )

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'nombre', 'apellido', 'rol', 'campus_asignado', 'estado', 'suspension_hasta')


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ('id', 'placa', 'tipo', 'marca', 'modelo', 'color', 'activo', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        request = self.context.get('request')
        user_pk = self.context.get('user_pk')
        if not self.instance and request and user_pk:
            active_count = Vehicle.objects.filter(user_id=user_pk, activo=True).count()
            if active_count >= 2:
                raise serializers.ValidationError('Máximo 2 vehículos activos por usuario.')
        return attrs

    def create(self, validated_data):
        validated_data['user_id'] = self.context['user_pk']
        return super().create(validated_data)
