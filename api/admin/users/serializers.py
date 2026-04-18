from rest_framework import serializers

from core.models import Usuario


class UsuarioListSerializer(serializers.ModelSerializer):
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    facultad_display = serializers.CharField(source='get_facultad_display', read_only=True)

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'rol', 'rol_display', 'facultad', 'facultad_display',
            'telefono', 'is_staff', 'is_superuser', 'is_active', 'activo',
            'fecha_creacion', 'ultimo_acceso',
        ]
        read_only_fields = ('fecha_creacion', 'ultimo_acceso')


class UsuarioWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, min_length=4)

    class Meta:
        model = Usuario
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'rol', 'facultad', 'telefono', 'is_staff', 'is_active', 'activo', 'password',
        ]

    def create(self, validated_data):
        pwd = validated_data.pop('password', None) or '123'
        user = Usuario(**validated_data)
        user.set_password(pwd)
        user.save()
        return user

    def update(self, instance, validated_data):
        pwd = validated_data.pop('password', None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=4, write_only=True)
