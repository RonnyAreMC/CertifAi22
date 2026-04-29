"""Auth de cuentas públicas (Participante).

No usamos Django's auth.User para `Participante` porque ya existe el flujo
guest (registrarse a un evento sin cuenta) y queremos preservarlo.

En vez de eso, mantenemos una sesión simple via `request.session['participante_id']`.
Compatible con el middleware de sesión de Django.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone

from core.models import Participante

SESSION_KEY = 'participante_id'


def authenticate(email: str, password: str) -> Participante | None:
    """Devuelve el Participante si credenciales son válidas; None si no."""
    if not email or not password:
        return None
    try:
        p = Participante.objects.get(email__iexact=email.strip())
    except Participante.DoesNotExist:
        return None
    if not p.has_account:
        return None
    if not p.check_password(password):
        return None
    return p


def login(request, participante: Participante) -> None:
    """Setea la sesión y actualiza last_login."""
    request.session[SESSION_KEY] = participante.id
    participante.last_login = timezone.now()
    participante.save(update_fields=['last_login'])


def logout(request) -> None:
    request.session.pop(SESSION_KEY, None)


def get_current_participante(request) -> Participante | None:
    """Recupera el Participante de la sesión, o None si no logueado."""
    pid = request.session.get(SESSION_KEY)
    if not pid:
        return None
    try:
        return Participante.objects.get(pk=pid)
    except Participante.DoesNotExist:
        request.session.pop(SESSION_KEY, None)
        return None


def login_required(view_func):
    """Decorator: redirige a login si no hay sesión activa de participante."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        p = get_current_participante(request)
        if not p:
            messages.info(request, 'Iniciá sesión para acceder a tu cuenta.')
            return redirect(f'/cuenta/login/?next={request.path}')
        request.participante = p
        return view_func(request, *args, **kwargs)
    return wrapper
