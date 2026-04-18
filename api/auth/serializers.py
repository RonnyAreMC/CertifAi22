from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.models import Usuario


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Devuelve info del usuario junto con los tokens."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['rol'] = getattr(user, 'rol', '')
        token['is_staff'] = user.is_staff
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'rol': getattr(user, 'rol', ''),
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
        }
        return data


class UsuarioMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'rol', 'facultad', 'telefono', 'is_staff', 'is_superuser',
        ]
        read_only_fields = fields
