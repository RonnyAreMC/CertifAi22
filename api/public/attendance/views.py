from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    Participante, Certificado, SesionAsistencia, ConfirmacionAsistencia,
)

from .serializers import (
    AttendanceConfirmInputSerializer, UpdatePhoneInputSerializer,
)


def _participant_data(p):
    return {
        'id': p.id,
        'cedula': p.cedula,
        'nombres': p.nombres,
        'apellidos': p.apellidos,
        'email': p.email,
        'celular': p.celular or '',
        'cursos': list(p.certificados.values_list('curso', flat=True).distinct()),
        'cursos_count': p.certificados.count(),
    }


class AttendanceSearchView(APIView):
    """GET ?q=X → lista participantes para confirmar asistencia."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if len(query) < 3:
            return Response({'results': []})

        tokens = query.split()
        q_filter = Q(cedula__icontains=query) | Q(email__icontains=query)
        for t in tokens:
            q_filter |= Q(nombres__icontains=t) | Q(apellidos__icontains=t)

        participantes = Participante.objects.filter(q_filter)[:20]
        return Response({'results': [_participant_data(p) for p in participantes]})


class AttendanceVerifyView(APIView):
    """GET ?q=X → búsqueda enriquecida con sesiones disponibles y estado de confirmación."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response({
                'personas': [], 'total': 0,
                'dias_disponibles': self._sessions_by_day(),
                'confirmacion_existente': None,
            })

        tokens = query.split()
        q_filter = Q(cedula__icontains=query) | Q(email__icontains=query)
        for t in tokens:
            q_filter |= Q(nombres__icontains=t) | Q(apellidos__icontains=t)

        participantes = list(Participante.objects.filter(q_filter)[:50])
        personas = []
        for p in participantes:
            personas.append({
                **_participant_data(p),
                'participante_id': p.id,
                'cert_id': p.certificados.values_list('id', flat=True).first(),
            })

        conf_existente = None
        if len(personas) == 1:
            p = participantes[0]
            conf = (
                ConfirmacionAsistencia.objects
                .filter(participante=p, confirmado=True)
                .select_related('sesion').first()
            )
            if conf:
                conf_existente = {
                    'dia': conf.sesion.dia_semana,
                    'fecha': conf.sesion.fecha.strftime('%d/%m/%Y'),
                    'horario': conf.sesion.label,
                }

        return Response({
            'personas': personas,
            'total': len(personas),
            'persona': personas[0] if len(personas) == 1 else None,
            'dias_disponibles': self._sessions_by_day(),
            'confirmacion_existente': conf_existente,
        })

    @staticmethod
    def _sessions_by_day():
        sesiones = SesionAsistencia.objects.filter(activa=True).order_by('fecha', 'hora_inicio')
        dias = {}
        for s in sesiones:
            key = f"{s.dia_semana} - {s.fecha.strftime('%d/%m/%Y')}"
            dias.setdefault(key, []).append({
                'id': s.id,
                'label': s.label,
                'titulo': s.titulo,
                'cupos': s.cupos_disponibles if s.cupos_disponibles is not None else 9999,
                'llena': s.esta_llena,
            })
        return dias


class AttendanceSessionsView(APIView):
    """GET → sesiones activas agrupadas por día (para select dependiente)."""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({'dias': AttendanceVerifyView._sessions_by_day()})


class AttendanceConfirmView(APIView):
    """POST → crea ConfirmacionAsistencia para un participante + sesión."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = AttendanceConfirmInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        try:
            sesion = SesionAsistencia.objects.get(id=data['sesion_id'], activa=True)
        except SesionAsistencia.DoesNotExist:
            return Response({'ok': False, 'error': 'Sesión no encontrada.'},
                            status=status.HTTP_404_NOT_FOUND)

        participante = None
        if data.get('participante_id'):
            try:
                participante = Participante.objects.get(id=data['participante_id'])
            except Participante.DoesNotExist:
                return Response({'ok': False, 'error': 'Participante no encontrado.'},
                                status=status.HTTP_404_NOT_FOUND)
        elif data.get('cert_id'):
            try:
                cert = Certificado.objects.get(id=data['cert_id'])
                participante = cert.participante
                if not participante:
                    return Response({'ok': False, 'error': 'Participante no vinculado.'},
                                    status=status.HTTP_404_NOT_FOUND)
            except Certificado.DoesNotExist:
                return Response({'ok': False, 'error': 'Certificado no encontrado.'},
                                status=status.HTTP_404_NOT_FOUND)

        if sesion.esta_llena:
            return Response({
                'ok': False,
                'error': f'Esta sesión ya alcanzó el cupo máximo de {sesion.capacidad} personas.',
            }, status=status.HTTP_409_CONFLICT)

        conf, created = ConfirmacionAsistencia.objects.get_or_create(
            participante=participante, sesion=sesion, defaults={'confirmado': True},
        )

        if not created:
            return Response({'ok': True, 'already': True,
                             'message': 'Ya estás confirmado para esta sesión.'})

        cupos = sesion.cupos_disponibles
        cupos_msg = f'Quedan {cupos} cupos.' if cupos is not None else ''
        return Response({
            'ok': True, 'already': False,
            'message': f'Asistencia confirmada para {sesion.dia_semana} {sesion.label}. {cupos_msg} ¡Recuerda asistir!',
        })


class AttendanceUpdatePhoneView(APIView):
    """POST → actualiza celular del participante (y sincroniza certificados)."""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = UpdatePhoneInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        celular = (ser.validated_data.get('celular') or '').strip()

        pid = ser.validated_data.get('participante_id')
        cid = ser.validated_data.get('cert_id')

        if pid:
            try:
                p = Participante.objects.get(id=pid)
                p.celular = celular
                p.save(update_fields=['celular'])
                Certificado.objects.filter(participante=p).update(celular=celular)
                return Response({'ok': True, 'celular': celular})
            except Participante.DoesNotExist:
                return Response({'ok': False, 'error': 'Participante no encontrado.'},
                                status=status.HTTP_404_NOT_FOUND)

        if cid:
            try:
                cert = Certificado.objects.get(id=cid)
                Certificado.objects.filter(cedula=cert.cedula).update(celular=celular)
                if cert.participante:
                    cert.participante.celular = celular
                    cert.participante.save(update_fields=['celular'])
                return Response({'ok': True, 'celular': celular})
            except Certificado.DoesNotExist:
                return Response({'ok': False, 'error': 'Certificado no encontrado.'},
                                status=status.HTTP_404_NOT_FOUND)

        return Response({'ok': False, 'error': 'Faltan datos.'},
                        status=status.HTTP_400_BAD_REQUEST)
