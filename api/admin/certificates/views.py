from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions

from core.models import Certificado
from api.common.viewsets import AuditedModelViewSet

from .serializers import (
    CertificadoListSerializer,
    CertificadoDetailSerializer,
    CertificadoWriteSerializer,
)


class CertificadoViewSet(AuditedModelViewSet):
    """CRUD admin de certificados. La parte pública está en api/public/."""
    queryset = Certificado.objects.with_relations()
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['lote', 'participante']
    search_fields = ['cedula', 'email', 'nombres', 'apellidos', 'curso', 'hash_verificacion']
    ordering_fields = ['created_at', 'descargas_count']
    ordering = ['-created_at']
    lookup_field = 'hash_verificacion'

    audit_verbose_name = 'certificado'

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CertificadoWriteSerializer
        if self.action == 'retrieve':
            return CertificadoDetailSerializer
        return CertificadoListSerializer

    def audit_detail(self, instance, action):
        return f'Certificado #{instance.pk} ({instance.cedula} - {instance.curso})'
