from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Usuario
from api.common.viewsets import AuditedModelViewSet

from .serializers import UsuarioListSerializer, UsuarioWriteSerializer, PasswordResetSerializer


class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        u = request.user
        return bool(u and u.is_authenticated and (u.is_superuser or getattr(u, 'rol', '') == 'superadmin'))


class UsuarioViewSet(AuditedModelViewSet):
    """Gestión de usuarios admin. Solo superadmin."""
    queryset = Usuario.objects.all()
    permission_classes = [IsSuperAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['rol', 'facultad', 'is_active', 'activo']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'username']
    ordering = ['-date_joined']

    audit_verbose_name = 'usuario'

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return UsuarioWriteSerializer
        return UsuarioListSerializer

    def audit_detail(self, instance, action):
        return f'Usuario #{instance.pk} ({instance.username})'

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        ser = PasswordResetSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user.set_password(ser.validated_data['new_password'])
        user.save(update_fields=['password'])
        self.log_audit('RESET_PASSWORD', f'Password reseteado para {user.username}')
        return Response({'success': True, 'message': 'Contraseña actualizada'})
