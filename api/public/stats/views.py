from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Certificado, LoteCertificados, Participante, SesionAsistencia


class PublicStatsView(APIView):
    """Conteos agregados para la landing pública."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'total_certificados': Certificado.objects.count(),
            'total_seminarios': LoteCertificados.objects.count(),
            'total_participantes': Participante.objects.count(),
            'total_sesiones_activas': SesionAsistencia.objects.filter(activa=True).count(),
        })
