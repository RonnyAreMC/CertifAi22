def log_audit(user, action: str, detail: str) -> None:
    """Crea un registro de auditoría. Seguro si user es None o anónimo."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return
    # Import lazy para evitar circular imports con core.models
    from core.models import Auditoria
    Auditoria.objects.create(usuario=user, accion=action, detalle=detail)


class AuditLogMixin:
    """Mixin para views/viewsets que registran auditoría.

    Uso:
        class MyView(AuditLogMixin, APIView):
            audit_action = 'CREAR_COSA'
            audit_detail_template = 'Cosa creada: {obj}'
    """
    audit_action = ''
    audit_detail_template = ''

    def log_audit(self, action: str = '', detail: str = '', user=None) -> None:
        user = user or getattr(getattr(self, 'request', None), 'user', None)
        log_audit(user, action or self.audit_action, detail)
