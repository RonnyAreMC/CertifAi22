from rest_framework import serializers, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import DisenoGlobal
from core.base.mixins import log_audit


class DisenoGlobalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisenoGlobal
        fields = [
            'id', 'plantilla', 'color_primario', 'color_secundario',
            'color_terciario', 'color_texto', 'cuerpo_certificado',
            'firma_inst_1', 'firma_inst_2', 'firma_inst_3',
            'nombre_firma_4', 'cargo_firma_4', 'imagen_firma_4',
            'logo_header_1', 'logo_header_2', 'logo_header_3',
            'posicion_firmas',
            'firma_1_offset_y', 'firma_1_escala',
            'firma_2_offset_y', 'firma_2_escala',
            'firma_3_offset_y', 'firma_3_escala',
            'firma_4_offset_y', 'firma_4_escala',
            'updated_at',
        ]
        read_only_fields = ('id', 'updated_at')


class DisenoGlobalView(APIView):
    """Singleton: GET devuelve el diseño actual, PATCH lo actualiza."""
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        diseno = DisenoGlobal.get_solo()
        return Response(DisenoGlobalSerializer(diseno).data)

    def patch(self, request):
        diseno = DisenoGlobal.get_solo()
        ser = DisenoGlobalSerializer(diseno, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        log_audit(request.user, 'EDITAR_DISENO_GLOBAL', 'Diseño global actualizado')
        return Response(ser.data)
