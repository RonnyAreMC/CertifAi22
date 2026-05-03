"""Serializers del módulo "resumen" para el endpoint mobile.

No expone `transcript_raw` (puede ser MUY largo, varios MB) — el cliente
mobile no lo necesita; solo el resumen procesado y el cuestionario.
"""
from rest_framework import serializers

from core.models import IntentoCuestionario, ResumenSesion


class IntentoCuestionarioSerializer(serializers.ModelSerializer):
    porcentaje = serializers.IntegerField(read_only=True)

    class Meta:
        model = IntentoCuestionario
        fields = [
            'id', 'correctas', 'total', 'porcentaje',
            'tiempo_total_seg', 'respuestas', 'created_at',
        ]
        read_only_fields = fields


class ResumenSesionSerializer(serializers.ModelSerializer):
    is_ready = serializers.BooleanField(read_only=True)
    has_failed = serializers.BooleanField(read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)

    class Meta:
        model = ResumenSesion
        fields = [
            'id', 'estado', 'estado_display',
            'is_ready', 'has_failed',
            'resumen_md', 'puntos_clave', 'proximos_pasos', 'cuestionario',
            'duracion_minutos', 'transcript_chars',
            'ai_model', 'created_at', 'procesado_at',
        ]
        read_only_fields = fields
