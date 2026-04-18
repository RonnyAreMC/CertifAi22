from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import (
    SesionAsistencia, Participante, ConfirmacionAsistencia, Certificado,
)

from .serializers import SesionListSerializer, SesionDetailSerializer
from .utils import sesion_payload


class PublicSesionViewSet(viewsets.ReadOnlyModelViewSet):
    """Endpoint público: listar sesiones activas e inscribirse."""
    queryset = SesionAsistencia.objects.active().select_related('lote')
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['modalidad', 'solo_lideres']
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
