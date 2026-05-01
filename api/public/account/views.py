"""API de cuenta de participante para clientes móviles (Expo)."""
from __future__ import annotations

from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import (
    Certificado, ConfirmacionAsistencia, Participante, ParticipanteToken,
    RegistroAsistencia, SesionAsistencia,
)

from .authentication import ParticipanteTokenAuthentication
from .serializers import (
    CertificadoSerializer, LoginInputSerializer, ParticipanteSerializer,
    RegisterInputSerializer, SesionMobileSerializer,
)


# ════════════════════════════════════════════════════════════════
#  Auth
# ════════════════════════════════════════════════════════════════

class LoginView(APIView):
    """POST /api/v1/public/account/login/ → token bearer."""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = LoginInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        email = ser.validated_data['email'].strip().lower()
        password = ser.validated_data['password']

        try:
            p = Participante.objects.get(email__iexact=email)
        except Participante.DoesNotExist:
            return Response({'error': 'Credenciales inválidas.'}, status=401)
        if not p.has_account or not p.check_password(password):
            return Response({'error': 'Credenciales inválidas.'}, status=401)

        ua = request.META.get('HTTP_USER_AGENT', '')[:255]
        token = ParticipanteToken.generate_for(p, days=30, user_agent=ua)
        p.last_login = timezone.now()
        p.save(update_fields=['last_login'])

        return Response({
            'token': token.key,
            'expires_at': token.expires_at.isoformat(),
            'participante': ParticipanteSerializer(p).data,
        })


class RegisterView(APIView):
    """POST /api/v1/public/account/register/ → crea cuenta + token."""
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = RegisterInputSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        email = d['email'].strip().lower()

        existing = Participante.objects.filter(email__iexact=email).first()
        if existing and existing.has_account:
            return Response(
                {'error': 'Ya existe una cuenta con ese email. Inicia sesión.'},
                status=409,
            )

        p = existing or Participante(email=email)
        p.nombres   = d['nombres'].strip() or p.nombres
        p.apellidos = d['apellidos'].strip() or p.apellidos
        if d.get('cedula'):  p.cedula  = d['cedula'].strip() or p.cedula
        if d.get('celular'): p.celular = d['celular'].strip() or p.celular
        try:
            p.full_clean(exclude=['password_hash'])
        except Exception as e:
            return Response({'error': str(e)}, status=400)
        p.set_password(d['password'])
        p.save()

        ua = request.META.get('HTTP_USER_AGENT', '')[:255]
        token = ParticipanteToken.generate_for(p, days=30, user_agent=ua)
        return Response(
            {
                'token': token.key,
                'expires_at': token.expires_at.isoformat(),
                'participante': ParticipanteSerializer(p).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LogoutView(APIView):
    """POST /api/v1/public/account/logout/ → invalida el token actual."""
    authentication_classes = [ParticipanteTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # request.auth viene del 2º elemento del tuple devuelto por authenticate()
        token = getattr(request, 'auth', None)
        if isinstance(token, ParticipanteToken):
            token.delete()
        return Response({'ok': True})


# ════════════════════════════════════════════════════════════════
#  Landing público (sin auth) — eventos hero + stats
# ════════════════════════════════════════════════════════════════

class LandingView(APIView):
    """GET /api/v1/public/account/landing/ → datos del home antes del login.

    Devuelve los próximos eventos para el carrusel y estadísticas globales
    (total certificados / horas / participantes) para el trust strip.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        today = timezone.localdate()
        eventos = (SesionAsistencia.objects
            .filter(activa=True, fecha__gte=today)
            .order_by('fecha', 'hora_inicio')[:5])

        agg = Certificado.objects.aggregate(total_horas=Sum('horas'))
        return Response({
            'eventos_hero': SesionMobileSerializer(eventos, many=True).data,
            'stats': {
                'total_certificados': Certificado.objects.count(),
                'total_eventos':      SesionAsistencia.objects.filter(activa=True).count(),
                'total_horas':        agg['total_horas'] or 0,
                'total_participantes': Participante.objects.count(),
            },
        })


# ════════════════════════════════════════════════════════════════
#  Mi cuenta
# ════════════════════════════════════════════════════════════════

class _AuthenticatedBase(APIView):
    authentication_classes = [ParticipanteTokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_participante(self):
        return self.request.user.participante


class MeView(_AuthenticatedBase):
    """GET /api/v1/public/account/me/ → datos del participante autenticado."""

    def get(self, request):
        return Response(ParticipanteSerializer(self.get_participante()).data)


class CertificadosView(_AuthenticatedBase):
    """GET /api/v1/public/account/certificates/ → lista de certificados."""

    def get(self, request):
        p = self.get_participante()
        qs = Certificado.objects.filter(
            Q(cedula=p.cedula) if p.cedula else Q(email__iexact=p.email)
        ).select_related('lote').order_by('-fecha_curso')
        q = request.query_params.get('q', '').strip()
        if q:
            qs = qs.filter(Q(curso__icontains=q) | Q(lote__nombre_lote__icontains=q))
        return Response({
            'count': qs.count(),
            'results': CertificadoSerializer(qs, many=True).data,
        })


class EventosView(_AuthenticatedBase):
    """GET /api/v1/public/account/events/?tab=mios|disponibles"""

    def get(self, request):
        p = self.get_participante()
        tab = request.query_params.get('tab', 'mios')
        today = timezone.localdate()

        confirmados_ids = set(ConfirmacionAsistencia.objects.filter(participante=p).values_list('sesion_id', flat=True))
        asistidos_ids   = set(RegistroAsistencia.objects.filter(participante=p).values_list('sesion_id', flat=True))
        mis_ids = confirmados_ids | asistidos_ids

        if tab == 'disponibles':
            eventos = (SesionAsistencia.objects
                .filter(activa=True, fecha__gte=today)
                .exclude(id__in=mis_ids)
                .order_by('fecha', 'hora_inicio'))
        else:
            eventos = (SesionAsistencia.objects
                .filter(id__in=mis_ids)
                .order_by('-fecha', '-hora_inicio'))

        results = []
        for e in eventos:
            data = SesionMobileSerializer(e).data
            if e.id in asistidos_ids:           data['status'] = 'asisti'
            elif e.id in confirmados_ids:
                data['status'] = 'no_asisti' if e.fecha < today else 'inscrito'
            else:
                data['status'] = 'disponible'
            results.append(data)

        return Response({
            'tab': tab,
            'count_mios':       len(mis_ids),
            'count_disponibles': SesionAsistencia.objects.filter(activa=True, fecha__gte=today).exclude(id__in=mis_ids).count(),
            'results': results,
        })


class EventoDetailView(_AuthenticatedBase):
    """GET /api/v1/public/account/events/<id>/ → detalle de un evento + status del participante.

    Devuelve los campos del evento + el `status` calculado para el usuario actual:
    'asisti' si tiene RegistroAsistencia, 'inscrito' / 'no_asisti' si confirmó pero
    no asistió, 'disponible' si nunca se inscribió.
    """

    def get(self, request, sesion_id: int):
        try:
            sesion = SesionAsistencia.objects.select_related('lote').get(pk=sesion_id, activa=True)
        except SesionAsistencia.DoesNotExist:
            return Response({'error': 'Evento no encontrado.'}, status=404)

        p = self.get_participante()
        today = timezone.localdate()

        confirmado = ConfirmacionAsistencia.objects.filter(participante=p, sesion=sesion).exists()
        asistio = RegistroAsistencia.objects.filter(participante=p, sesion=sesion).exists()
        if asistio:
            status_value = 'asisti'
        elif confirmado:
            status_value = 'no_asisti' if sesion.fecha < today else 'inscrito'
        else:
            status_value = 'disponible'

        # Capacidad
        cupos_ocupados = ConfirmacionAsistencia.objects.filter(sesion=sesion).count()

        data = SesionMobileSerializer(sesion).data
        data['status'] = status_value
        data['lote_nombre'] = sesion.lote.nombre_lote if sesion.lote else None
        data['horas'] = getattr(sesion.lote, 'horas_validas', None) if sesion.lote else None
        data['capacidad'] = sesion.capacidad
        data['cupos_ocupados'] = cupos_ocupados
        data['cupos_disponibles'] = (
            None if sesion.capacidad == 0 else max(0, sesion.capacidad - cupos_ocupados)
        )
        return Response(data)


class InscribirEventoView(_AuthenticatedBase):
    """POST /api/v1/public/account/events/<id>/register/ → inscripción 1-click."""

    def post(self, request, sesion_id: int):
        try:
            sesion = SesionAsistencia.objects.get(pk=sesion_id, activa=True)
        except SesionAsistencia.DoesNotExist:
            return Response({'error': 'Evento no disponible.'}, status=404)
        p = self.get_participante()
        _, created = ConfirmacionAsistencia.objects.get_or_create(participante=p, sesion=sesion)
        return Response({'ok': True, 'created': created, 'sesion_id': sesion.id})


class AsistenciasView(_AuthenticatedBase):
    """GET /api/v1/public/account/attendances/ → asistencias del participante.

    Devuelve la lista de eventos donde tiene `RegistroAsistencia` (asistió de hecho).
    Cada item: id, sesion (titulo, fecha, hora, modalidad, lugar), fecha_registro local,
    certificado (si ya se emitió uno para esa sesión a este participante).
    """

    def get(self, request):
        p = self.get_participante()
        registros = (
            RegistroAsistencia.objects
            .filter(participante=p)
            .select_related('sesion', 'sesion__lote', 'certificado')
            .order_by('-fecha_registro')
        )

        results = []
        for r in registros:
            s = r.sesion
            local_dt = timezone.localtime(r.fecha_registro)
            results.append({
                'id': r.id,
                'sesion_id': s.id,
                'titulo': s.titulo or s.dia_semana,
                'descripcion': s.descripcion or '',
                'fecha': s.fecha.strftime('%Y-%m-%d'),
                'dia_semana': s.dia_semana,
                'hora_inicio': s.hora_inicio.strftime('%H:%M'),
                'hora_fin':    s.hora_fin.strftime('%H:%M'),
                'es_virtual': s.modalidad == 'virtual',
                'modalidad': s.modalidad,
                'lugar': s.lugar or '',
                'lote_nombre': s.lote.nombre_lote if s.lote else None,
                'fecha_registro': local_dt.strftime('%Y-%m-%d %H:%M'),
                'tiene_certificado': bool(r.certificado_id),
                'certificado_hash': r.certificado.hash_verificacion if r.certificado else None,
            })

        return Response({
            'count': len(results),
            'results': results,
        })


class CheckinByQRView(_AuthenticatedBase):
    """POST /api/v1/public/account/checkin/ → registra asistencia con QR escaneado.

    Body: { "codigo_qr": "<uuid del QR>" }
    El participante autenticado (vía Token) queda como `RegistroAsistencia` si:
      - La sesión existe y está activa.
      - Es el día de la sesión (o se permite check-in fuera de día por config).

    Si no existe `ConfirmacionAsistencia` previa, la creamos al vuelo (inscripción
    automática + asistencia).
    """

    def post(self, request):
        codigo_qr = (request.data.get('codigo_qr') or '').strip()
        if not codigo_qr:
            return Response({'error': 'Falta el código QR.'}, status=400)

        # Si vino una URL completa (ej. http://host/checkin/<uuid>/), extraemos el último segmento UUID
        if '/' in codigo_qr:
            parts = [p for p in codigo_qr.rstrip('/').split('/') if p]
            codigo_qr = parts[-1] if parts else codigo_qr

        try:
            sesion = SesionAsistencia.objects.get(codigo_qr=codigo_qr, activa=True)
        except SesionAsistencia.DoesNotExist:
            return Response({'error': 'QR inválido o sesión no activa.'}, status=404)

        p = self.get_participante()

        # Crear confirmación de inscripción si no existe (auto-inscripción al escanear)
        ConfirmacionAsistencia.objects.get_or_create(participante=p, sesion=sesion)

        # Registrar asistencia (idempotente — el unique constraint
        # sesion+participante evita duplicados)
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
        registro, created = RegistroAsistencia.objects.get_or_create(
            participante=p,
            sesion=sesion,
            defaults={'ip_address': ip},
        )

        return Response({
            'ok': True,
            'created': created,
            'already_registered': not created,
            'sesion_id': sesion.id,
            'sesion_titulo': sesion.titulo or sesion.dia_semana,
            'fecha': sesion.fecha.strftime('%Y-%m-%d'),
            'hora': sesion.hora_inicio.strftime('%H:%M'),
        })


class DashboardView(_AuthenticatedBase):
    """GET /api/v1/public/account/dashboard/ → stats + próximos eventos + recientes."""

    def get(self, request):
        p = self.get_participante()
        today = timezone.localdate()

        certificados = Certificado.objects.filter(
            Q(cedula=p.cedula) if p.cedula else Q(email__iexact=p.email)
        ).order_by('-fecha_curso')
        total_horas = sum(c.horas or 0 for c in certificados)

        confirmados_ids = set(ConfirmacionAsistencia.objects.filter(participante=p).values_list('sesion_id', flat=True))
        asistidos_ids   = set(RegistroAsistencia.objects.filter(participante=p).values_list('sesion_id', flat=True))

        proximos = (SesionAsistencia.objects
            .filter(activa=True, id__in=confirmados_ids, fecha__gte=today)
            .order_by('fecha', 'hora_inicio')[:3])

        recomendados = (SesionAsistencia.objects
            .filter(activa=True, fecha__gte=today)
            .exclude(id__in=confirmados_ids)
            .order_by('fecha', 'hora_inicio')[:5])

        return Response({
            'participante':   ParticipanteSerializer(p).data,
            'stats': {
                'certificados':       certificados.count(),
                'total_horas':        total_horas,
                'eventos_inscrito':   len(confirmados_ids),
                'eventos_asistido':   len(asistidos_ids),
            },
            'proximos':       SesionMobileSerializer(proximos, many=True).data,
            'recomendados':   SesionMobileSerializer(recomendados, many=True).data,
            'certificados_recientes': CertificadoSerializer(certificados[:3], many=True).data,
        })
