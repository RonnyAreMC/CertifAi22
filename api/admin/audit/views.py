from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import serializers, filters, permissions, viewsets

from core.models import Auditoria


class AuditoriaSerializer(serializers.ModelSerializer):
    usuario_username = serializers.CharField(source='usuario.username', read_only=True)
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Auditoria
        fields = ['id', 'usuario', 'usuario_username', 'usuario_nombre', 'accion', 'detalle', 'fecha']
        read_only_fields = fields

    def get_usuario_nombre(self, obj):
        u = obj.usuario
        return f'{u.first_name} {u.last_name}'.strip() if u else ''


class AuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """Logs de auditoría (solo lectura, solo staff)."""
    queryset = Auditoria.objects.select_related('usuario')
    serializer_class = AuditoriaSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['accion', 'usuario']
    search_fields = ['accion', 'detalle', 'usuario__username']
    ordering_fields = ['fecha']
    ordering = ['-fecha']
