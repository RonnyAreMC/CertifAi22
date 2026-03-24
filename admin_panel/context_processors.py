from core.models import SolicitudAcceso


def solicitudes_pendientes(request):
    """Context processor para mostrar el contador de solicitudes pendientes en el menú"""
    if request.user.is_authenticated and hasattr(request.user, 'rol') and request.user.rol == 'superadmin':
        pendientes_count = SolicitudAcceso.objects.filter(estado='pendiente').count()
        return {'pendientes_count': pendientes_count}
    return {'pendientes_count': 0}
