import json

from rest_framework import serializers

from core.models import SesionAsistencia, ConfirmacionAsistencia, RegistroAsistencia, Ponente


class PonenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ponente
        fields = ['id', 'nombre', 'titulo', 'afiliacion', 'bio', 'orden']


class SesionListSerializer(serializers.ModelSerializer):
    plataforma_display = serializers.CharField(source='plataforma_display_safe', read_only=True)
    es_virtual = serializers.BooleanField(read_only=True)
    confirmados_count = serializers.IntegerField(read_only=True)
    cupos_disponibles = serializers.IntegerField(read_only=True, allow_null=True)
    esta_llena = serializers.BooleanField(read_only=True)
    imagen_banner_url = serializers.SerializerMethodField()
    lote_nombre = serializers.CharField(source='lote.nombre_lote', read_only=True, allow_null=True)
    ponentes = PonenteSerializer(many=True, read_only=True)

    class Meta:
        model = SesionAsistencia
        fields = [
            'id', 'titulo', 'descripcion', 'imagen_banner_url',
            'modalidad', 'plataforma_virtual', 'plataforma_display', 'enlace_virtual',
            'lugar', 'fecha', 'dia_semana', 'hora_inicio', 'hora_fin',
            'capacidad', 'solo_lideres', 'activa', 'codigo_qr',
            'confirmados_count', 'cupos_disponibles', 'esta_llena',
            'es_virtual', 'lote', 'lote_nombre', 'ponentes', 'created_at',
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
    """Serializer de escritura para sesiones. Soporta ponentes anidados.

    El form HTML envía los ponentes como JSON serializado en el campo
    `ponentes_json` (FormData no soporta listas anidadas). Internamente lo
    parseamos y reemplazamos completamente la lista en cada save.
    """
    ponentes_json = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = SesionAsistencia
        fields = [
            'titulo', 'descripcion', 'imagen_banner',
            'modalidad', 'plataforma_virtual', 'enlace_virtual',
            'lugar', 'fecha', 'dia_semana', 'hora_inicio', 'hora_fin',
            'capacidad', 'solo_lideres', 'activa', 'lote',
            'ponentes_json',
        ]

    def validate_ponentes_json(self, value: str):
        """Parsea el JSON y valida que sea lista de dicts con `nombre`."""
        if not value:
            return []
        try:
            data = json.loads(value)
        except json.JSONDecodeError:
            raise serializers.ValidationError('Formato JSON inválido en ponentes.')
        if not isinstance(data, list):
            raise serializers.ValidationError('Ponentes debe ser una lista.')
        cleaned = []
        for i, p in enumerate(data):
            if not isinstance(p, dict):
                continue
            nombre = (p.get('nombre') or '').strip()
            if not nombre:
                continue  # silenciosamente saltamos los vacíos
            cleaned.append({
                'nombre': nombre,
                'titulo': (p.get('titulo') or '').strip(),
                'afiliacion': (p.get('afiliacion') or '').strip(),
                'bio': (p.get('bio') or '').strip(),
                'orden': i,
            })
        return cleaned

    def validate(self, attrs):
        """Sesiones virtuales = siempre Google Meet (auto-generado por Calendar API).

        El admin no escoge plataforma ni enlace: ambos se llenan en el hook
        `perform_create` del viewset. Para presenciales, limpiamos los dos.
        """
        modalidad = attrs.get('modalidad') or (self.instance and self.instance.modalidad)
        if modalidad == 'virtual':
            attrs['plataforma_virtual'] = 'meet'
            # enlace lo rellena Calendar API (queda vacío hasta entonces)
        elif modalidad == 'presencial':
            attrs['enlace_virtual'] = ''
            attrs['plataforma_virtual'] = ''
        return attrs

    def _save_ponentes(self, sesion, ponentes_data):
        """Reemplaza la lista de ponentes de la sesión."""
        sesion.ponentes.all().delete()
        Ponente.objects.bulk_create([
            Ponente(sesion=sesion, **p) for p in ponentes_data
        ])

    def create(self, validated_data):
        ponentes_data = validated_data.pop('ponentes_json', None)
        sesion = super().create(validated_data)
        if ponentes_data is not None:
            self._save_ponentes(sesion, ponentes_data)
        return sesion

    def update(self, instance, validated_data):
        ponentes_data = validated_data.pop('ponentes_json', None)
        sesion = super().update(instance, validated_data)
        # Solo actualizamos ponentes si vinieron en el payload (PATCH parcial)
        if ponentes_data is not None:
            self._save_ponentes(sesion, ponentes_data)
        return sesion


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
