from rest_framework import serializers

from core.models import LoteCertificados


class LoteListSerializer(serializers.ModelSerializer):
    administrador_username = serializers.CharField(source='administrador.username', read_only=True, allow_null=True)
    total_certificados = serializers.IntegerField(read_only=True, required=False)
    facultad_display = serializers.CharField(source='get_facultad_display', read_only=True)
    plantilla_display = serializers.CharField(source='get_plantilla_display', read_only=True)

    class Meta:
        model = LoteCertificados
        fields = [
            'id', 'nombre_lote', 'facultad', 'facultad_display',
            'plantilla', 'plantilla_display', 'personalizar_diseno',
            'color_primario', 'color_secundario', 'color_terciario', 'color_texto',
            'administrador', 'administrador_username',
            'activo', 'fecha_creacion', 'total_certificados',
        ]
        read_only_fields = ('fecha_creacion',)


class LoteDetailSerializer(LoteListSerializer):
    class Meta(LoteListSerializer.Meta):
        fields = LoteListSerializer.Meta.fields + [
            'cuerpo_certificado', 'archivo_excel',
            'nombre_firma_1', 'cargo_firma_1',
            'nombre_firma_2', 'cargo_firma_2',
            'nombre_firma_3', 'cargo_firma_3',
            'nombre_firma_4', 'cargo_firma_4',
            'firma_inst_1', 'firma_inst_2', 'firma_inst_3', 'firma_inst_4',
            'logo_header_1', 'logo_header_2', 'logo_header_3',
            'posicion_firmas',
        ]


class LoteWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoteCertificados
        fields = [
            'nombre_lote', 'facultad', 'plantilla', 'personalizar_diseno',
            'color_primario', 'color_secundario', 'color_terciario', 'color_texto',
            'cuerpo_certificado', 'archivo_excel', 'activo',
            'firma_inst_1', 'firma_inst_2', 'firma_inst_3', 'firma_inst_4',
            'nombre_firma_1', 'cargo_firma_1',
            'nombre_firma_2', 'cargo_firma_2',
            'nombre_firma_3', 'cargo_firma_3',
            'nombre_firma_4', 'cargo_firma_4',
            'logo_header_1', 'logo_header_2', 'logo_header_3',
            'posicion_firmas',
        ]
