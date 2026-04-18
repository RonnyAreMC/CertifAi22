from django.db.models import Max
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import LandingBloque, SesionAsistencia
from api.common.viewsets import AuditedModelViewSet

from .serializers import LandingBloqueSerializer, ReorderSerializer


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_superuser or getattr(u, 'rol', '') == 'superadmin'))


class LandingBloqueViewSet(AuditedModelViewSet):
    """CRUD de bloques del landing + reorder + meta (tipos/estilos/eventos futuros)."""
    queryset = LandingBloque.objects.all().order_by('orden')
    serializer_class = LandingBloqueSerializer
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['tipo', 'estilo', 'activo']
    ordering_fields = ['orden', 'id']
    ordering = ['orden']

    audit_verbose_name = 'bloque_landing'

    def perform_create(self, serializer):
        max_orden = LandingBloque.objects.aggregate(m=Max('orden'))['m'] or 0
        instance = serializer.save(orden=max_orden + 1)
        self.log_audit(self._action_code('create'), f'Bloque #{instance.pk} creado ({instance.tipo}/{instance.estilo})')

    def audit_detail(self, instance, action):
        return f'Bloque #{instance.pk} ({instance.tipo}/{instance.estilo})'

    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """POST {items: [{id, orden}, ...]} → actualiza orden en batch."""
        ser = ReorderSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        for item in ser.validated_data['items']:
            LandingBloque.objects.filter(id=item['id']).update(orden=item['orden'])
        self.log_audit('REORDENAR_LANDING', f'{len(ser.validated_data["items"])} bloques reordenados')
        return Response({'ok': True})

    @action(detail=False, methods=['get'])
    def meta(self, request):
        """GET → choices de tipo/estilo + eventos futuros (para el builder)."""
        from datetime import date
        eventos = SesionAsistencia.objects.filter(
            fecha__gte=date.today(), activa=True
        ).order_by('fecha', 'hora_inicio').values(
            'id', 'titulo', 'dia_semana', 'fecha'
        )[:100]
        return Response({
            'tipo_choices': [{'value': v, 'label': l} for v, l in LandingBloque.TIPO_CHOICES],
            'estilo_choices': [{'value': v, 'label': l} for v, l in LandingBloque.ESTILO_CHOICES],
            'eventos_futuros': [
                {
                    'id': e['id'],
                    'titulo': e['titulo'] or e['dia_semana'],
                    'fecha': e['fecha'].strftime('%d/%m/%Y'),
                }
                for e in eventos
            ],
        })
