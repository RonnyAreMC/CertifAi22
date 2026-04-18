"""Helpers compartidos entre las views del admin panel."""
from core.models import Auditoria


def _is_admin(user):
    """True si el user tiene rol admin o superadmin."""
    return user.is_authenticated and user.rol in ('admin', 'superadmin')


def _is_superadmin(user):
    """True solo para superadmin (config global)."""
    return user.is_authenticated and user.rol == 'superadmin'


def _log_audit(user, action, detail):
    """Crea entry en Auditoria si user es autenticado."""
    if user and user.is_authenticated:
        Auditoria.objects.create(usuario=user, accion=action, detalle=detail)
