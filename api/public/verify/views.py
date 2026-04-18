from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Certificado


class VerifyCertificateView(APIView):
    """GET /<hash>/ → datos completos de un certificado para la página de verificación."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, hash):
        cert = (
            Certificado.objects
            .filter(hash_verificacion=hash)
            .select_related('lote')
            .first()
        )
        if not cert:
            return Response({'found': False, 'hash': hash}, status=404)

        Certificado.objects.filter(pk=cert.pk).update(veces_buscado=cert.veces_buscado + 1)

        lote = cert.lote
        return Response({
            'found': True,
            'hash': cert.hash_verificacion,
            'certificado': {
                'nombres': cert.nombres,
                'apellidos': cert.apellidos,
                'cedula': cert.cedula,
                'email': cert.email,
                'curso': cert.curso,
                'fecha_curso': cert.fecha_curso.isoformat() if cert.fecha_curso else None,
                'fecha_emision': cert.created_at.isoformat() if cert.created_at else None,
                'horas': cert.horas,
                'descargas_count': cert.descargas_count,
                'veces_buscado': cert.veces_buscado + 1,
            },
            'lote': {
                'nombre': lote.nombre_lote if lote else None,
                'facultad_code': lote.facultad if lote else None,
                'facultad_display': lote.get_facultad_display() if lote else None,
                'plantilla': lote.plantilla if lote else None,
            } if lote else None,
        })
