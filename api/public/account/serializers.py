"""Serializers del API de cuenta pública (mobile)."""
from rest_framework import serializers

from core.models import Certificado, Participante, SesionAsistencia


class LoginInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)


class RegisterInputSerializer(serializers.Serializer):
    nombres   = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    email     = serializers.EmailField()
    cedula    = serializers.CharField(required=False, allow_blank=True, default='')
    celular   = serializers.CharField(required=False, allow_blank=True, default='')
    password  = serializers.CharField(write_only=True, min_length=6)


class ParticipanteSerializer(serializers.ModelSerializer):
    nombre_completo = serializers.CharField(read_only=True)
    initials        = serializers.CharField(read_only=True)
    avatar_url      = serializers.SerializerMethodField()

    class Meta:
        model = Participante
        fields = [
            'id', 'nombres', 'apellidos', 'email', 'cedula', 'celular',
            'es_lider', 'nombre_completo', 'initials', 'avatar_url',
            'last_login', 'created_at',
        ]
        read_only_fields = fields

    def get_avatar_url(self, obj):
        return obj.avatar.url if obj.avatar else None


class CertificadoSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    verify_url   = serializers.SerializerMethodField()
    lote_nombre  = serializers.CharField(source='lote.nombre_lote', read_only=True)

    class Meta:
        model = Certificado
        fields = [
            'id', 'curso', 'fecha_curso', 'horas',
            'hash_verificacion', 'lote_nombre',
            'download_url', 'verify_url',
            'created_at',
        ]
        read_only_fields = fields

    def get_download_url(self, obj):
        return f'/api/v1/public/certificates/{obj.hash_verificacion}/download/'

    def get_verify_url(self, obj):
        return f'/verificar/{obj.hash_verificacion}/'


class SesionMobileSerializer(serializers.ModelSerializer):
    es_virtual    = serializers.BooleanField(read_only=True)
    titulo_display = serializers.SerializerMethodField()
    banner_url    = serializers.SerializerMethodField()

    class Meta:
        model = SesionAsistencia
        fields = [
            'id', 'titulo', 'titulo_display', 'descripcion',
            'fecha', 'dia_semana', 'hora_inicio', 'hora_fin',
            'modalidad', 'es_virtual', 'enlace_virtual', 'lugar',
            'banner_url', 'activa',
        ]
        read_only_fields = fields

    def get_titulo_display(self, obj):
        return obj.titulo or obj.dia_semana

    def get_banner_url(self, obj):
        return obj.imagen_banner.url if obj.imagen_banner else None
