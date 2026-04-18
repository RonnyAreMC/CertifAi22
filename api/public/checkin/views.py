from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    SesionAsistencia, Participante, Certificado,
    ConfirmacionAsistencia, RegistroAsistencia,
)


def _get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class CheckinSessionView(APIView):
    """GET → devuelve info básica de la sesión identificada por su código QR."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, codigo_qr):
        sesion = get_object_or_404(SesionAsistencia, codigo_qr=codigo_qr, activa=True)
        return Response({
            'id': sesion.id,
            'codigo_qr': sesion.codigo_qr,
            'titulo': sesion.titulo or sesion.dia_semana,
            'descripcion': sesion.descripcion,
            'dia_semana': sesion.dia_semana,
            'fecha': sesion.fecha.strftime('%Y-%m-%d'),
            'hora_inicio': sesion.hora_inicio.strftime('%H:%M'),
            'hora_fin': sesion.hora_fin.strftime('%H:%M'),
            'lugar': sesion.lugar,
            'modalidad': sesion.modalidad,
        })


class CheckinSearchView(APIView):
    """GET ?q=X → busca participantes en el contexto del QR."""
    permission_classes = [permissions.AllowAny]

    def get(self, request, codigo_qr):
        sesion = get_object_or_404(SesionAsistencia, codigo_qr=codigo_qr, activa=True)
        query = request.query_params.get('q', '').strip()
        if len(query) < 3:
            return Response({'results': []})

        tokens = query.split()
        q_filter = Q(cedula__icontains=query) | Q(email__icontains=query)
        for t in tokens:
            q_filter |= Q(nombres__icontains=t) | Q(apellidos__icontains=t)

        participantes = Participante.objects.filter(q_filter)[:15]
        results = []
        for p in participantes:
            results.append({
                'id': p.id,
                'cedula': p.cedula,
                'nombres': p.nombres,
                'apellidos': p.apellidos,
                'email': p.email,
                'already_registered': RegistroAsistencia.objects.filter(
                    sesion=sesion, participante=p
                ).exists(),
                'is_confirmed': ConfirmacionAsistencia.objects.filter(
                    sesion=sesion, participante=p, confirmado=True
                ).exists(),
            })
        return Response({'results': results})


class CheckinRegisterView(APIView):
    """POST → registra asistencia (marca presente) si hay confirmación previa."""
    permission_classes = [permissions.AllowAny]

    def post(self, request, codigo_qr):
        sesion = get_object_or_404(SesionAsistencia, codigo_qr=codigo_qr, activa=True)

        pid = request.data.get('id') or request.data.get('cert_id')
        if not pid:
            return Response({'ok': False, 'error': 'Datos incompletos.'},
                            status=status.HTTP_400_BAD_REQUEST)

        participante = None
        try:
            participante = Participante.objects.get(id=pid)
        except Participante.DoesNotExist:
            try:
                cert = Certificado.objects.get(id=pid)
                participante = cert.participante
            except Certificado.DoesNotExist:
                pass

        if not participante:
            return Response({'ok': False, 'error': 'Participante no encontrado.'},
                            status=status.HTTP_404_NOT_FOUND)

        # Bloqueo por inasistencias previas
        blocked = ConfirmacionAsistencia.objects.filter(
            participante=participante, bloqueado=True
        ).exists()
        if blocked:
            return Response({
                'ok': False,
                'error': 'Tu cuenta está bloqueada por inasistencias previas. Contacta al administrador.',
            }, status=status.HTTP_403_FORBIDDEN)

        # Confirmación previa requerida
        is_confirmed = ConfirmacionAsistencia.objects.filter(
            participante=participante, sesion=sesion, confirmado=True
        ).exists()
        if not is_confirmed:
            return Response({
                'ok': False,
                'error': f'No tienes una confirmación de cupo registrada para la sesión de {sesion.dia_semana} {sesion.label}.',
            }, status=status.HTTP_403_FORBIDDEN)

        registro, created = RegistroAsistencia.objects.get_or_create(
            sesion=sesion, participante=participante,
            defaults={'ip_address': _get_client_ip(request)},
        )

        if not created:
            return Response({
                'ok': True, 'already': True,
                'message': '¡Ya registraste tu asistencia anteriormente!',
                'nombre': f'{participante.nombres} {participante.apellidos}',
            })

        return Response({
            'ok': True, 'already': False,
            'message': '¡Gracias por estar aquí! Tu asistencia fue registrada exitosamente.',
            'nombre': f'{participante.nombres} {participante.apellidos}',
            'hora': timezone.now().strftime('%H:%M'),
        })
