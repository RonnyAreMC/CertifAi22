from rest_framework import serializers

from core.models import Certificado


class CertificadoListSerializer(serializers.ModelSerializer):
    lote_nombre = serializers.CharField(source='lote.nombre_lote', read_only=True)
    lote_facultad = serializers.CharField(source='lote.facultad', read_only=True)
    lote_facultad_display = serializers.CharField(source='lote.get_facultad_display', read_only=True)
    participante_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Certificado
        fields = [
            'id', 'hash_verificacion', 'cedula', 'nombres', 'apellidos',
            'email', 'curso', 'fecha_curso', 'horas',
            'lote', 'lote_nombre', 'lote_facultad', 'lote_facultad_display',
            'participante', 'participante_nombre',
            'descargas_count', 'veces_buscado', 'fecha_ultima_descarga',
            'created_at',
        ]
        read_only_fields = ('hash_verificacion', 'descargas_count', 'veces_buscado',
                            'fecha_ultima_descarga', 'created_at')

    def get_participante_nombre(self, obj):
        p = obj.participante
        return f'{p.nombres} {p.apellidos}' if p else ''


class CertificadoDetailSerializer(CertificadoListSerializer):
    class Meta(CertificadoListSerializer.Meta):
        pass


class CertificadoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificado
        fields = [
            'lote', 'participante', 'cedula', 'nombres', 'apellidos',
            'email', 'celular', 'curso', 'fecha_curso', 'horas',
        ]
