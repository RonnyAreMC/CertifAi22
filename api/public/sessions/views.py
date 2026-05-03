from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import action
from rest_framework.response import Response

from api.public.account.authentication import ParticipanteTokenAuthentication

from core.models import (
    SesionAsistencia, Participante, ConfirmacionAsistencia, Certificado,
    ResumenSesion, IntentoCuestionario, RegistroAsistencia,
)

from .resumen_serializers import ResumenSesionSerializer, IntentoCuestionarioSerializer
from .serializers import SesionListSerializer, SesionDetailSerializer
from .utils import sesion_payload


class PublicSesionViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint público: listar sesiones activas e inscribirse."""
    queryset = SesionAsistencia.objects.active().select_related('lote')
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['modalidad']
    search_fields = ['titulo', 'descripcion', 'lugar']
    ordering_fields = ['fecha', 'hora_inicio']
    ordering = ['fecha', 'hora_inicio']

    def get_serializer_class(self):
        return SesionDetailSerializer if self.action == 'retrieve' else SesionListSerializer

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        qs = SesionAsistencia.objects.upcoming().select_related('lote')
        page = self.paginate_queryset(qs)
        ser = self.get_serializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(ser.data)
        return Response(ser.data)

    @action(detail=False, methods=['get'])
    def past(self, request):
        qs = SesionAsistencia.objects.past().select_related('lote')[:50]
        return Response(self.get_serializer(qs, many=True).data)

    # ── Inscripción pública ─────────────────────────────────────

    @action(detail=True, methods=['get'], url_path='search-participant')
    def search_participant(self, request, pk=None):
        sesion = self.get_object()
        query = request.query_params.get('q', '').strip()
        if len(query) < 3:
            return Response({'found': False, 'results': []})

        tokens = query.split()
        q_filter = Q(cedula__icontains=query) | Q(email__icontains=query)
        for t in tokens:
            q_filter |= Q(nombres__icontains=t) | Q(apellidos__icontains=t)
        participantes = list(Participante.objects.filter(q_filter).distinct()[:15])

        if not participantes:
            return Response({'found': False, 'results': []})

        def _data(p):
            ya = ConfirmacionAsistencia.objects.filter(
                participante=p, sesion=sesion, confirmado=True
            ).exists()
            q_cursos = Q(participante=p)
            if p.cedula:
                q_cursos |= Q(cedula__iexact=p.cedula)
            if p.email:
                q_cursos |= Q(email__iexact=p.email)
            cursos = list(
                Certificado.objects.filter(q_cursos)
                .values_list('lote__nombre_lote', flat=True).distinct()[:10]
            )
            missing = []
            for field in ('cedula', 'email', 'nombres', 'apellidos'):
                if not getattr(p, field):
                    missing.append(field)
            return {
                'id': p.id, 'cedula': p.cedula, 'email': p.email,
                'nombres': p.nombres, 'apellidos': p.apellidos,
                'celular': p.celular or '',
                'cursos': [c for c in cursos if c],
                'missing_info': missing, 'ya_confirmado': ya,
            }

        if len(participantes) == 1:
            p = participantes[0]
            return Response({
                'found': True, 'count': 1,
                'participante': _data(p),
                'ya_confirmado': ConfirmacionAsistencia.objects.filter(
                    participante=p, sesion=sesion, confirmado=True
                ).exists(),
            })

        return Response({
            'found': True, 'count': len(participantes),
            'results': [_data(p) for p in participantes],
        })

    @action(detail=True, methods=['post'], url_path='confirm-participant')
    def confirm_participant(self, request, pk=None):
        sesion = self.get_object()
        pid = request.data.get('participante_id')
        if not pid:
            return Response({'ok': False, 'error': 'Datos incompletos.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            p = Participante.objects.get(id=pid)
        except Participante.DoesNotExist:
            return Response({'ok': False, 'error': 'Participante no encontrado.'},
                            status=status.HTTP_404_NOT_FOUND)

        if sesion.solo_lideres and not p.es_lider:
            return Response({'ok': False, 'error': 'Este evento es exclusivo para Líderes Académicos.'},
                            status=status.HTTP_403_FORBIDDEN)

        fields = []
        for name in ('celular', 'email', 'cedula', 'nombres', 'apellidos'):
            val = (request.data.get(name) or '').strip()
            if not val:
                continue
            current = getattr(p, name)
            if name in ('celular', 'email'):
                if val != current:
                    setattr(p, name, val)
                    fields.append(name)
            elif not current:
                setattr(p, name, val)
                fields.append(name)
        if fields:
            p.save(update_fields=fields)

        if sesion.esta_llena:
            return Response({'ok': False, 'error': 'Esta sesión ya alcanzó el cupo máximo.'},
                            status=status.HTTP_409_CONFLICT)

        conf, created = ConfirmacionAsistencia.objects.get_or_create(
            participante=p, sesion=sesion, defaults={'confirmado': True}
        )
        if not created:
            return Response({'ok': True, 'already': True, 'message': 'Ya estás registrado en esta sesión.'})

        return Response({
            'ok': True, 'already': False,
            'message': f'Registro exitoso para {p.nombres}.',
            'sesion': sesion_payload(sesion),
        })

    # ── Resumen IA del transcript (Drive → IA → Markdown) ─────────

    @action(
        detail=True, methods=['get'], url_path='resumen',
        authentication_classes=[ParticipanteTokenAuthentication, SessionAuthentication],
        permission_classes=[permissions.AllowAny],  # endpoint público (read-only)
    )
    def resumen(self, request, pk=None):
        """Devuelve el ResumenSesion + grabación + intentos del participante.

        Si el request viene autenticado con ParticipanteToken, también incluye:
          - intentos: lista de IntentoCuestionario del participante
          - mejor_intento: el con mayor `correctas`
          - intentos_disponibles: int (MAX_INTENTOS - usados)
          - asistio: bool
          - inscrito: bool
          - recording: { name, web_link } o null

        Estados:
          - 200 + payload → resumen disponible
          - 200 + {estado: 'no_existe'} → sesión válida pero sin resumen aún
          - 404 → sesión no existe
        """
        sesion = self.get_object()
        resumen = ResumenSesion.objects.filter(sesion=sesion).first()

        # Datos del participante (si viene autenticado)
        participante = None
        principal = getattr(request, 'user', None)
        if principal is not None and getattr(principal, 'is_authenticated', False):
            participante = getattr(principal, 'participante', None)

        intentos_data = []
        mejor_intento = None
        intentos_disponibles = IntentoCuestionario.MAX_INTENTOS
        asistio = False
        inscrito = False
        if participante is not None:
            intentos = list(IntentoCuestionario.objects.filter(participante=participante, sesion=sesion))
            intentos_data = IntentoCuestionarioSerializer(intentos, many=True).data
            if intentos:
                mejor = max(intentos, key=lambda x: x.correctas)
                mejor_intento = IntentoCuestionarioSerializer(mejor).data
            intentos_disponibles = max(0, IntentoCuestionario.MAX_INTENTOS - len(intentos))
            asistio = RegistroAsistencia.objects.filter(participante=participante, sesion=sesion).exists()
            inscrito = ConfirmacionAsistencia.objects.filter(participante=participante, sesion=sesion).exists()

        # Grabación de Drive (lazy, solo si resumen LISTO)
        recording = None
        if resumen and resumen.estado == 'listo':
            try:
                from core.services.meet.drive_client import find_recording_for_session
                rec = find_recording_for_session(sesion)
                if rec:
                    recording = {
                        'file_id': rec.file_id,
                        'name': rec.name,
                        'web_link': rec.web_link,
                    }
            except Exception:
                recording = None

        if resumen is None:
            return Response({
                'estado': 'no_existe',
                'message': 'Esta sesión todavía no tiene resumen IA generado.',
                'transcripcion_habilitada': sesion.transcripcion_habilitada,
                'intentos': intentos_data,
                'intentos_disponibles': intentos_disponibles,
                'mejor_intento': mejor_intento,
                'max_intentos': IntentoCuestionario.MAX_INTENTOS,
                'recording': None,
                'asistio': asistio,
                'inscrito': inscrito,
            })
        ser = ResumenSesionSerializer(resumen)
        return Response({
            **ser.data,
            'intentos': intentos_data,
            'mejor_intento': mejor_intento,
            'intentos_disponibles': intentos_disponibles,
            'max_intentos': IntentoCuestionario.MAX_INTENTOS,
            'recording': recording,
            'asistio': asistio,
            'inscrito': inscrito,
        })

    @action(
        detail=True, methods=['post'], url_path='cuestionario/submit',
        authentication_classes=[ParticipanteTokenAuthentication, SessionAuthentication],
        permission_classes=[permissions.IsAuthenticated],
    )
    def submit_cuestionario(self, request, pk=None):
        """Registra un intento del cuestionario para el participante autenticado.

        Body: { respuestas: [int|null], tiempo_total_seg: int }
        Devuelve: { ok, intento, intentos_restantes }
        """
        sesion = self.get_object()
        participante = getattr(request.user, 'participante', None)
        if participante is None:
            return Response({'ok': False, 'error': 'Auth requerida.'}, status=status.HTTP_401_UNAUTHORIZED)

        inscrito = ConfirmacionAsistencia.objects.filter(participante=participante, sesion=sesion).exists()
        asistio  = RegistroAsistencia.objects.filter(participante=participante, sesion=sesion).exists()
        if not (inscrito or asistio):
            return Response({'ok': False, 'error': 'Sin acceso al cuestionario.'}, status=status.HTTP_403_FORBIDDEN)

        resumen = ResumenSesion.objects.filter(sesion=sesion).first()
        if not resumen or resumen.estado != 'listo' or not resumen.cuestionario:
            return Response({'ok': False, 'error': 'Cuestionario no disponible.'}, status=status.HTTP_400_BAD_REQUEST)

        intentos_count = IntentoCuestionario.objects.filter(participante=participante, sesion=sesion).count()
        if intentos_count >= IntentoCuestionario.MAX_INTENTOS:
            return Response({
                'ok': False,
                'error': f'Ya alcanzaste el máximo de {IntentoCuestionario.MAX_INTENTOS} intentos.',
            }, status=status.HTTP_409_CONFLICT)

        respuestas = request.data.get('respuestas') or []
        tiempo_total = int(request.data.get('tiempo_total_seg') or 0)

        preguntas = resumen.cuestionario
        total = len(preguntas)
        correctas = 0
        for i, q in enumerate(preguntas):
            if i < len(respuestas) and respuestas[i] is not None:
                if respuestas[i] == q.get('correcta_idx'):
                    correctas += 1

        intento = IntentoCuestionario.objects.create(
            participante=participante,
            sesion=sesion,
            correctas=correctas,
            total=total,
            tiempo_total_seg=tiempo_total,
            respuestas=respuestas,
        )
        return Response({
            'ok': True,
            'intento': IntentoCuestionarioSerializer(intento).data,
            'intentos_restantes': IntentoCuestionario.MAX_INTENTOS - (intentos_count + 1),
        }, status=status.HTTP_201_CREATED)

    @action(
        detail=True, methods=['post'], url_path='resumen/procesar',
        authentication_classes=[ParticipanteTokenAuthentication, SessionAuthentication],
        permission_classes=[permissions.IsAuthenticated],
    )
    def procesar_resumen(self, request, pk=None):
        """Dispara el procesamiento IA en background (Celery task).

        Requiere autenticación: token de participante o sesión de admin Django.
        Esto evita que cualquier visitante sin auth queme tokens IA gratis.
        """
        from core.tasks.transcript_tasks import procesar_transcript_sesion

        sesion = self.get_object()
        if not sesion.transcripcion_habilitada:
            return Response(
                {'ok': False, 'error': 'La transcripción IA está deshabilitada para esta sesión.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        procesar_transcript_sesion.delay(sesion.id)
        return Response(
            {'ok': True, 'message': 'Procesamiento encolado.', 'sesion_id': sesion.id},
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=['post'], url_path='register-participant')
    def register_participant(self, request, pk=None):
        sesion = self.get_object()
        cedula = (request.data.get('cedula') or '').strip().upper()
        nombres = (request.data.get('nombres') or '').strip().upper()
        apellidos = (request.data.get('apellidos') or '').strip().upper()
        email = (request.data.get('email') or '').strip().lower()
        celular = (request.data.get('celular') or '').strip()

        if not nombres or not apellidos:
            return Response({'ok': False, 'error': 'Nombres y apellidos son obligatorios.'},
                            status=status.HTTP_400_BAD_REQUEST)
        if not cedula and not email:
            return Response({'ok': False, 'error': 'Debe proporcionar al menos cédula o correo.'},
                            status=status.HTTP_400_BAD_REQUEST)

        p = None
        if cedula:
            p = Participante.objects.filter(cedula=cedula).first()
        if not p and email:
            p = Participante.objects.filter(email__iexact=email).first()

        if sesion.solo_lideres and (not p or not p.es_lider):
            return Response({'ok': False, 'error': 'Este evento es exclusivo para Líderes Académicos.'},
                            status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            if p:
                fields = []
                if celular and not p.celular:
                    p.celular = celular; fields.append('celular')
                if cedula and not p.cedula:
                    p.cedula = cedula; fields.append('cedula')
                if email and not p.email:
                    p.email = email; fields.append('email')
                if fields:
                    p.save(update_fields=fields)
            else:
                p = Participante.objects.create(
                    cedula=cedula, nombres=nombres, apellidos=apellidos,
                    email=email, celular=celular,
                )

            if sesion.esta_llena:
                return Response({'ok': False, 'error': 'Esta sesión ya alcanzó el cupo máximo.'},
                                status=status.HTTP_409_CONFLICT)

            conf, created = ConfirmacionAsistencia.objects.get_or_create(
                participante=p, sesion=sesion, defaults={'confirmado': True}
            )

        if not created:
            return Response({'ok': True, 'already': True, 'message': 'Ya estás registrado en esta sesión.'})

        return Response({
            'ok': True, 'already': False,
            'message': f'Registro exitoso para {p.nombres} {p.apellidos}.',
            'participante': {'id': p.id, 'nombres': p.nombres, 'apellidos': p.apellidos},
            'sesion': sesion_payload(sesion),
        })
