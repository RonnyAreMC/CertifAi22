from rest_framework import serializers


class CopilotBodyInputSerializer(serializers.Serializer):
    tipo_evento = serializers.ChoiceField(
        choices=['seminario', 'taller', 'curso', 'conferencia', 'capacitacion'],
        default='seminario',
    )
    contexto = serializers.CharField(required=False, allow_blank=True, default='')
    tono = serializers.ChoiceField(
        choices=['formal', 'amigable', 'inspirador', 'corto', 'expandido'],
        default='formal',
    )
    accion = serializers.ChoiceField(
        choices=['create', 'rewrite', 'shorten', 'expand'],
        default='create',
    )


class ExcelMapInputSerializer(serializers.Serializer):
    sample_data = serializers.DictField(
        child=serializers.ListField(child=serializers.CharField(allow_blank=True)),
        help_text='Dict: {columna: [valores de muestra]}',
    )


class VoiceExtractInputSerializer(serializers.Serializer):
    transcripcion = serializers.CharField(
        help_text='Texto transcrito del audio del admin',
        min_length=5,
    )
