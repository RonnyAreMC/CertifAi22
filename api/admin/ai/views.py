from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.base.mixins import log_audit
from core.services.ai import copilot, excel_mapper, insights, recommender, voice

from .serializers import (
    CopilotBodyInputSerializer,
    ExcelMapInputSerializer,
    VoiceExtractInputSerializer,
)


class BaseAIView(APIView):
    """Base para endpoints de IA. Auditan uso."""
    permission_classes = [permissions.IsAdminUser]
    ai_action = ''

    def _respond(self, result: dict):
        """Si la feature no está implementada → 501 Not Implemented."""
        if not result.get('implemented', False):
            return Response(result, status=status.HTTP_501_NOT_IMPLEMENTED)
        return Response(result)

    def _audit(self, detail: str):
        log_audit(self.request.user, f'IA_{self.ai_action}', detail)


class CopilotBodyView(BaseAIView):
    """POST: genera cuerpo de certificado con IA."""
    ai_action = 'COPILOT_BODY'

    def post(self, request):
        ser = CopilotBodyInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = copilot.generate_body_text(**ser.validated_data)
        self._audit(f'tipo={ser.validated_data["tipo_evento"]} tono={ser.validated_data["tono"]}')
        return self._respond(result)


class ExcelMapColumnsView(BaseAIView):
    """POST: clasifica columnas de Excel con IA."""
    ai_action = 'EXCEL_MAP'

    def post(self, request):
        ser = ExcelMapInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = excel_mapper.map_excel_columns(ser.validated_data['sample_data'])
        cols = list(ser.validated_data['sample_data'].keys())
        self._audit(f'mapping {len(cols)} cols: {cols[:5]}')
        return self._respond(result)


class VoiceExtractView(BaseAIView):
    """POST: extrae entidades de sesión desde voz transcrita."""
    ai_action = 'VOICE_EXTRACT'

    def post(self, request):
        ser = VoiceExtractInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        result = voice.extract_entities_from_voice(ser.validated_data['transcripcion'])
        self._audit(f'len={len(ser.validated_data["transcripcion"])}')
        return self._respond(result)


class InsightsDashboardView(BaseAIView):
    """GET: insights narrativos del dashboard."""
    ai_action = 'INSIGHTS'

    def get(self, request):
        result = insights.generate_insights()
        self._audit('dashboard insights')
        return self._respond(result)


class RecommendationsView(APIView):
    """GET: recomendaciones para un email. Público (post-inscripción)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, email):
        result = recommender.recommend_for_email(email)
        if not result.get('implemented', False):
            return Response(result, status=status.HTTP_501_NOT_IMPLEMENTED)
        return Response(result)
