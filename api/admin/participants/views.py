from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Participante
from api.common.viewsets import AuditedModelViewSet

from .serializers import (
    ParticipanteListSerializer,
    ParticipanteDetailSerializer,
    ParticipanteWriteSerializer,
    CertificadoMiniSerializer,
)


class ParticipanteViewSet(AuditedModelViewSet):
    queryset = Participante.objects.annotate(certificados_count=Count('certificados'))
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['es_lider']
    search_fields = ['cedula', 'email', 'nombres', 'apellidos']
    ordering_fields = ['created_at', 'nombres', 'apellidos']
    ordering = ['-created_at']

    audit_verbose_name = 'participante'

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ParticipanteWriteSerializer
        if self.action == 'retrieve':
            return ParticipanteDetailSerializer
        return ParticipanteListSerializer

    def audit_detail(self, instance, action):
        return f'Participante #{instance.pk} ({instance.nombres} {instance.apellidos})'

    @action(detail=True, methods=['get'])
    def certificates(self, request, pk=None):
        p = self.get_object()
        return Response(CertificadoMiniSerializer(p.certificados.all(), many=True).data)

    @action(detail=True, methods=['post'])
    def toggle_leader(self, request, pk=None):
        p = self.get_object()
        p.es_lider = not p.es_lider
        p.save(update_fields=['es_lider'])
        self.log_audit('TOGGLE_LIDER', f'Participante #{p.pk} → es_lider={p.es_lider}')
        return Response({'id': p.id, 'es_lider': p.es_lider})
