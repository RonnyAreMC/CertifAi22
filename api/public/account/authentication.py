"""DRF Authentication para participantes vía bearer token.

Uso desde el cliente móvil:
    Authorization: Token <key>

El backend valida que el token exista, no esté expirado y devuelve el
Participante correspondiente envuelto en `request.user` (proxy mínimo
para compatibilidad con permission_classes de DRF).
"""
from __future__ import annotations

from django.utils import timezone
from rest_framework import authentication, exceptions

from core.models import ParticipanteToken


class _ParticipantePrincipal:
    """Wrapper que hace que `request.user` sea compatible con DRF.

    Define `is_authenticated=True` y expone el participante real como
    `request.user.participante`.
    """
    def __init__(self, participante):
        self.participante = participante
        self.is_authenticated = True
        self.is_anonymous = False
        self.is_staff = False
        self.is_superuser = False
        self.id = participante.id
        self.pk = participante.pk
        self.email = participante.email
        self.username = participante.email

    def __str__(self):
        return f'Participante<{self.email}>'


class ParticipanteTokenAuthentication(authentication.BaseAuthentication):
    keyword = 'Token'

    def authenticate(self, request):
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header.startswith(self.keyword + ' '):
            return None

        key = header.split(' ', 1)[1].strip()
        if not key:
            raise exceptions.AuthenticationFailed('Token vacío.')

        try:
            tok = ParticipanteToken.objects.select_related('participante').get(key=key)
        except ParticipanteToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('Token inválido.')

        if tok.is_expired:
            raise exceptions.AuthenticationFailed('Token expirado.')

        # Touch last_used (sin disparar updated_at)
        ParticipanteToken.objects.filter(pk=tok.pk).update(last_used_at=timezone.now())

        return (_ParticipantePrincipal(tok.participante), tok)

    def authenticate_header(self, request):
        return self.keyword
