from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from core.models import SolicitudAcceso, Usuario
from ._shared import superadmin_required, _log_audit

class CustomLoginView(DjangoLoginView):
    """Custom login view that checks for pending access requests"""
    template_name = 'panel/auth/login.html'
    redirect_authenticated_user = False  # We handle redirect manually
    
    def get(self, request, *args, **kwargs):
        # If user is already authenticated, route them properly
        if request.user.is_authenticated:
            return self._route_authenticated_user(request.user)
        return super().get(request, *args, **kwargs)
    
    def _route_authenticated_user(self, user):
        """Route an authenticated user to the correct page based on their status."""
        # Check if user has pending access request
        try:
            SolicitudAcceso.objects.get(usuario_creado=user, estado='pendiente')
            return redirect('panel:mi_estado')
        except SolicitudAcceso.DoesNotExist:
            pass
        
        # Check if user is active admin
        if user.activo and user.rol in ['admin', 'superadmin']:
            return redirect('panel:dashboard')
        
        # Inactive user - send to mi_estado
        return redirect('panel:mi_estado')
    
    def form_valid(self, form):
        from django.contrib.auth import login
        user = form.get_user()

        # Always log the user in first
        login(self.request, user, backend='admin_panel.backends.EmailBackend')

        # Route them to the correct page
        return self._route_authenticated_user(user)

    def form_invalid(self, form):
        # Limpiamos los errores genéricos del form y mostramos un mensaje custom
        form.errors.clear()
        if not any(m.level_tag == 'error' for m in messages.get_messages(self.request)):
            messages.error(
                self.request,
                "Has ingresado mal tu usuario o contraseña. Inténtalo de nuevo."
            )
        return super().form_invalid(form)


def register(request):
    """Shell del formulario. Submit va a /api/v1/auth/register/ via fetch."""
    if request.user.is_authenticated:
        if request.user.activo and request.user.rol in ['admin', 'superadmin']:
            return redirect('panel:dashboard')
        return redirect('panel:mi_estado')

    from core.models import FACULTADES_CHOICES
    return render(request, 'panel/auth/register.html', {
        'facultades_choices': FACULTADES_CHOICES,
    })


def solicitud_pendiente(request, id):
    """Página de solicitud pendiente - redirige a mi_estado si está autenticado"""
    if request.user.is_authenticated:
        return redirect('panel:mi_estado')
    
    solicitud = get_object_or_404(SolicitudAcceso, id=id)
    
    # Si está aprobada, redirigir a login
    if solicitud.estado == 'aprobado':
        messages.success(request, 'Tu solicitud fue aprobada. Inicia sesión con tu correo y contraseña.')
        return redirect('panel:login')
    
    # Si está rechazada, mostrar motivo
    if solicitud.estado == 'rechazado':
        return render(request, 'panel/auth/solicitud_rechazada.html', {'solicitud': solicitud})
    
    # Si está pendiente, redirigir a login para que inicie sesión
    messages.info(request, 'Inicia sesión con tu correo y contraseña para ver el estado de tu solicitud.')
    return redirect('panel:login')


@login_required
def mi_estado(request):
    """Página de estado para usuarios pendientes de aprobación"""
    user = request.user
    
    # Si el usuario está activo y es admin, redirigir al dashboard
    if user.activo and user.rol in ['admin', 'superadmin']:
        return redirect('panel:dashboard')
    
    # Buscar la solicitud del usuario
    solicitud = None
    estado = 'pendiente'
    try:
        solicitud = SolicitudAcceso.objects.get(usuario_creado=user)
        estado = solicitud.estado
    except SolicitudAcceso.DoesNotExist:
        # Si no tiene solicitud pero no está activo, mostrar mensaje genérico
        if not user.activo:
            estado = 'desactivado'
    
    # Si la solicitud fue aprobada, verificar si el usuario está activo
    if estado == 'aprobado' and user.activo:
        return redirect('panel:dashboard')
    
    context = {
        'solicitud': solicitud,
        'estado': estado,
        'user': user,
    }
    return render(request, 'panel/auth/mi_estado.html', context)


@superadmin_required
def solicitudes_pendientes(request):
    """Admin view: lista de solicitudes de acceso pendientes"""
    estado_filter = request.GET.get('estado', 'pendiente')
    
    solicitudes = SolicitudAcceso.objects.all().order_by('-fecha_solicitud')
    
    if estado_filter == 'pendiente':
        solicitudes = solicitudes.filter(estado='pendiente')
    elif estado_filter == 'aprobado':
        solicitudes = solicitudes.filter(estado='aprobado')
    elif estado_filter == 'rechazado':
        solicitudes = solicitudes.filter(estado='rechazado')
    
    pendientes_count = SolicitudAcceso.objects.filter(estado='pendiente').count()
    aprobadas_count = SolicitudAcceso.objects.filter(estado='aprobado').count()
    rechazadas_count = SolicitudAcceso.objects.filter(estado='rechazado').count()
    
    context = {
        'solicitudes': solicitudes,
        'estado_filter': estado_filter,
        'pendientes_count': pendientes_count,
        'aprobadas_count': aprobadas_count,
        'rechazadas_count': rechazadas_count,
    }
    return render(request, 'panel/solicitudes/pendientes.html', context)


@superadmin_required
@require_http_methods(["POST"])
def aprobar_solicitud(request, id):
    """Admin action: aprobar una solicitud de acceso - activa el usuario existente"""
    solicitud = get_object_or_404(SolicitudAcceso, id=id)
    
    if solicitud.estado not in ['pendiente', 'rechazado']:
        messages.error(request, 'Esta solicitud no puede ser procesada.')
        return redirect('panel:solicitudes_pendientes')
    
    # Limpiar motivo de rechazo si existía
    if solicitud.estado == 'rechazado':
        solicitud.motivo_rechazo = ''
    
    try:
        if solicitud.usuario_creado:
            # Activar el usuario existente (creado durante el registro)
            usuario = solicitud.usuario_creado
            usuario.activo = True
            usuario.save(update_fields=['activo'])
            nombre_usuario = usuario.username
        else:
            # Solicitud legacy sin usuario vinculado - crear uno nuevo
            nombre_usuario = solicitud.email.split('@')[0]
            base_username = nombre_usuario
            counter = 1
            while Usuario.objects.filter(username=nombre_usuario).exists():
                nombre_usuario = f"{base_username}{counter}"
                counter += 1
            
            usuario = Usuario.objects.create_user(
                username=nombre_usuario,
                email=solicitud.email,
                first_name=solicitud.nombres,
                last_name=solicitud.apellidos,
                telefono=solicitud.telefono,
                facultad=solicitud.facultad,
                rol='admin',
                activo=True,
                is_staff=False,
                is_superuser=False,
            )
            solicitud.usuario_creado = usuario
        
        # Actualizar solicitud
        solicitud.estado = 'aprobado'
        solicitud.aprobado_por = request.user
        solicitud.fecha_respuesta = timezone.now()
        solicitud.save()
        
        # Log de auditoría
        _log_audit(request.user, 'SOLICITUD_APROBADA', 
                  f'Solicitud de {solicitud.email} aprobada. Usuario {nombre_usuario} activado.')
        
        messages.success(request, f'Solicitud aprobada. Usuario activado: {nombre_usuario}')
    except Exception as e:
        messages.error(request, f'Error al procesar la solicitud: {str(e)}')
    
    return redirect('panel:solicitudes_pendientes')


@superadmin_required
@require_http_methods(["GET", "POST"])
def rechazar_solicitud(request, id):
    """Admin action: rechazar una solicitud de acceso"""
    solicitud = get_object_or_404(SolicitudAcceso, id=id)
    
    if solicitud.estado != 'pendiente':
        messages.error(request, 'Esta solicitud ya ha sido procesada.')
        return redirect('panel:solicitudes_pendientes')
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        solicitud.estado = 'rechazado'
        solicitud.motivo_rechazo = motivo
        solicitud.aprobado_por = request.user
        solicitud.fecha_respuesta = timezone.now()
        solicitud.save()
        
        _log_audit(request.user, 'SOLICITUD_RECHAZADA', 
                  f'Solicitud de {solicitud.email} rechazada. Motivo: {motivo}')
        
        messages.success(request, f'Solicitud rechazada: {solicitud.email}')
        return redirect('panel:solicitudes_pendientes')
    
    return render(request, 'panel/solicitudes/rechazar.html', {'solicitud': solicitud})


