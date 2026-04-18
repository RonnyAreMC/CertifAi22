from rest_framework import serializers

from core.models import Participante, Certificado


class CertificadoMiniSerializer(serializers.ModelSerializer):
    lote_nombre = serializers.CharField(source='lote.nombre_lote', read_only=True)

    class Meta:
        model = Certificado
        fields = ['id', 'hash_verificacion', 'curso', 'fecha_curso', 'horas', 'lote_nombre']


class ParticipanteListSerializer(serializers.ModelSerializer):
    certificados_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = Participante
        fields = [
            'id', 'cedula', 'nombres', 'apellidos', 'email', 'celular',
            'es_lider', 'certificados_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ('created_at', 'updated_at')


class ParticipanteDetailSerializer(ParticipanteListSerializer):
    certificados = CertificadoMiniSerializer(many=True, read_only=True)

    class Meta(ParticipanteListSerializer.Meta):
        fields = ParticipanteListSerializer.Meta.fields + ['certificados']


class ParticipanteWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participante
        fields = ['cedula', 'nombres', 'apellidos', 'email', 'celular', 'es_lider']

    def validate(self, attrs):
        cedula = attrs.get('cedula', '') or (self.instance and self.instance.cedula) or ''
        email = attrs.get('email', '') or (self.instance and self.instance.email) or ''
        if not cedula and not email:
            raise serializers.ValidationError('Debe proporcionar al menos cédula o correo.')
        return attrs
