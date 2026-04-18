from rest_framework import serializers

from core.models import SesionAsistencia, ConfirmacionAsistencia, RegistroAsistencia


class SesionListSerializer(serializers.ModelSerializer):
    plataforma_display = serializers.CharField(source='plataforma_display_safe', read_only=True)
    es_virtual = serializers.BooleanField(read_only=True)
    confirmados_count = serializers.IntegerField(read_only=True)
    cupos_disponibles = serializers.IntegerField(read_only=True, allow_null=True)
    esta_llena = serializers.BooleanField(read_only=True)
    imagen_banner_url = serializers.SerializerMethodField()
    lote_nombre = serializers.CharField(source='lote.nombre_lote', read_only=True, allow_null=True)

    class Meta:
        model = SesionAsistencia
        fields = [
            'id', 'titulo', 'descripcion', 'imagen_banner_url',
            'modalidad', 'plataforma_virtual', 'plataforma_display', 'enlace_virtual',
            'lugar', 'fecha', 'dia_semana', 'hora_inicio', 'hora_fin',
            'capacidad', 'solo_lideres', 'activa', 'codigo_qr',
            'confirmados_count', 'cupos_disponibles', 'esta_llena',
            'es_virtual', 'lote', 'lote_nombre', 'created_at',
        ]
        read_only_fields = ('codigo_qr', 'created_at')

    def get_imagen_banner_url(self, obj):
        request = self.context.get('request')
        if obj.imagen_banner and hasattr(obj.imagen_banner, 'url'):
            url = obj.imagen_banner.url
            return request.build_absolute_uri(url) if request else url
        return None


class SesionDetailSerializer(SesionListSerializer):
    class Meta(SesionListSerializer.Meta):
        pass


class SesionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SesionAsistencia
        fields = [
            'titulo', 'descripcion', 'imagen_banner',
            'modalidad', 'plataforma_virtual', 'enlace_virtual',
            'lugar', 'fecha', 'dia_semana', 'hora_inicio', 'hora_fin',
            'capacidad', 'solo_lideres', 'activa', 'lote',
        ]

    def validate(self, attrs):
        modalidad = attrs.get('modalidad') or (self.instance and self.instance.modalidad)
        enlace = attrs.get('enlace_virtual', '')
        if modalidad == 'virtual' and not enlace and not (self.instance and self.instance.enlace_virtual):
            raise serializers.ValidationError({
                'enlace_virtual': 'Debes proporcionar un enlace para eventos virtuales.'
            })
        if modalidad == 'presencial':
            attrs['enlace_virtual'] = ''
            attrs['plataforma_virtual'] = ''
        return attrs


class ConfirmacionSerializer(serializers.ModelSerializer):
    participante_nombre = serializers.SerializerMethodField()
    participante_email = serializers.CharField(source='participante.email', read_only=True)
    participante_cedula = serializers.CharField(source='participante.cedula', read_only=True)
    ya_asistio = serializers.SerializerMethodField()

    class Meta:
        model = ConfirmacionAsistencia
        fields = [
            'id', 'participante', 'participante_nombre',
            'participante_email', 'participante_cedula',
            'confirmado', 'fecha_confirmacion', 'ya_asistio',
        ]
        read_only_fields = fields

    def get_participante_nombre(self, obj):
        p = obj.participante
        return f'{p.nombres} {p.apellidos}' if p else ''

    def get_ya_asistio(self, obj):
        return RegistroAsistencia.objects.filter(
            sesion=obj.sesion, participante=obj.participante
        ).exists()
