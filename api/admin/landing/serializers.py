from rest_framework import serializers

from core.models import LandingBloque, SesionAsistencia


class LandingBloqueSerializer(serializers.ModelSerializer):
    imagen_principal_url = serializers.SerializerMethodField()
    imagen_2_url = serializers.SerializerMethodField()
    imagen_3_url = serializers.SerializerMethodField()
    sesion_id = serializers.PrimaryKeyRelatedField(
        source='sesion', queryset=SesionAsistencia.objects.all(),
        required=False, allow_null=True,
    )

    class Meta:
        model = LandingBloque
        fields = [
            'id', 'tipo', 'estilo', 'orden', 'activo',
            'titulo', 'subtitulo', 'descripcion', 'items_json',
            'imagen_principal', 'imagen_principal_url',
            'imagen_2', 'imagen_2_url',
            'imagen_3', 'imagen_3_url',
            'color_fondo', 'color_texto', 'color_acento',
            'boton_1_texto', 'boton_1_url', 'boton_1_icono',
            'boton_2_texto', 'boton_2_url', 'boton_2_icono',
            'sesion', 'sesion_id',
        ]
        read_only_fields = ('orden', 'sesion')
        extra_kwargs = {
            'imagen_principal': {'write_only': True, 'required': False, 'allow_null': True},
            'imagen_2': {'write_only': True, 'required': False, 'allow_null': True},
            'imagen_3': {'write_only': True, 'required': False, 'allow_null': True},
        }

    def _img_url(self, field):
        request = self.context.get('request')
        if field and hasattr(field, 'url'):
            return request.build_absolute_uri(field.url) if request else field.url
        return None

    def get_imagen_principal_url(self, obj):
        return self._img_url(obj.imagen_principal)

    def get_imagen_2_url(self, obj):
        return self._img_url(obj.imagen_2)

    def get_imagen_3_url(self, obj):
        return self._img_url(obj.imagen_3)


class ReorderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    orden = serializers.IntegerField()


class ReorderSerializer(serializers.Serializer):
    items = ReorderItemSerializer(many=True)
