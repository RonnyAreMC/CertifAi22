from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets

from core.base.mixins import AuditLogMixin


class AuditedModelViewSet(AuditLogMixin, viewsets.ModelViewSet):
    """
    ModelViewSet que registra automáticamente en Auditoria las operaciones
    de escritura (create / update / destroy) y aplica los filter_backends
    estándar (Django filter, search, ordering).

    Personaliza con:
        - audit_verbose_name (str): nombre legible del recurso, ej "sesión"
        - audit_action_create / audit_action_update / audit_action_delete (str)
        - audit_detail(instance, action) -> str para detalle custom
        - filterset_fields / search_fields / ordering_fields: si necesitas filtrar.

    Sobrescribe `filter_backends` si tu recurso no necesita alguno de ellos.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]

    audit_verbose_name = 'recurso'
    audit_action_create = ''
    audit_action_update = ''
    audit_action_delete = ''

    def _action_code(self, verb: str) -> str:
        base = (self.audit_verbose_name or 'recurso').upper().replace(' ', '_')
        return {
            'create': self.audit_action_create or f'CREAR_{base}',
            'update': self.audit_action_update or f'EDITAR_{base}',
            'delete': self.audit_action_delete or f'ELIMINAR_{base}',
        }[verb]

    def audit_detail(self, instance, action: str) -> str:
        """Subclasses can override for richer messages."""
        return f'{self.audit_verbose_name.capitalize()} #{instance.pk}: {instance}'

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_audit(self._action_code('create'), self.audit_detail(instance, 'create'))

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_audit(self._action_code('update'), self.audit_detail(instance, 'update'))

    def perform_destroy(self, instance):
        detail = self.audit_detail(instance, 'delete')
        instance.delete()
        self.log_audit(self._action_code('delete'), detail)


class AuditedReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """ReadOnly sin auditoría (listados no se auditan por volumen).

    También trae los filter_backends estándar para consistencia con AuditedModelViewSet.
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
