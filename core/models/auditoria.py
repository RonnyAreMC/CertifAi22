"""Modelo de registro de auditoría para acciones administrativas.

Diseño:
- Vincula al usuario que ejecutó la acción
- Identifica el objeto auditado vía `ContentType` (polimórfico) — permite
  preguntas como "todos los cambios sobre este Certificado"
- Guarda los cambios en `cambios` (JSON) para trazabilidad granular
- Persiste IP y user-agent para forensics
- Mantiene `detalle` legacy para no romper escritos existentes
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AccionAuditoria(models.TextChoices):
    CREAR = 'CREAR', 'Crear'
    EDITAR = 'EDITAR', 'Editar'
    ELIMINAR = 'ELIMINAR', 'Eliminar'
    APROBAR = 'APROBAR', 'Aprobar'
    RECHAZAR = 'RECHAZAR', 'Rechazar'
    LOGIN = 'LOGIN', 'Inicio de sesión'
    LOGOUT = 'LOGOUT', 'Cierre de sesión'
    DESCARGAR = 'DESCARGAR', 'Descargar archivo'
    OTRA = 'OTRA', 'Otra acción'


class Auditoria(models.Model):
    """Log de acciones administrativas para trazabilidad legal y forense."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,                          # no perder log si se borra user
        related_name='acciones_auditoria',
    )
    accion = models.CharField(
        max_length=50,
        choices=AccionAuditoria.choices,
        db_index=True,
    )
    detalle = models.TextField(
        blank=True, default='',
        help_text='Descripción humana de la acción (compat con logs legacy).',
    )

    # ── Objeto auditado (polimórfico vía ContentType) ──────────────
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        help_text='Tipo de modelo del objeto auditado (ej. Certificado, Sesión).',
    )
    object_id = models.PositiveBigIntegerField(
        null=True, blank=True,
        help_text='PK del objeto auditado.',
    )
    objeto = GenericForeignKey('content_type', 'object_id')

    # ── Cambios granulares ─────────────────────────────────────────
    cambios = models.JSONField(
        default=dict, blank=True,
        help_text='Diff campo→{antes, despues}. Vacío si no aplica (ej. LOGIN).',
    )

    # ── Forensics ──────────────────────────────────────────────────
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True, default='')

    fecha = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Registro de Auditoría'
        verbose_name_plural = 'Registros de Auditoría'
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['accion', '-fecha']),
        ]

    def __str__(self):
        target = f' · {self.content_type}#{self.object_id}' if self.content_type_id else ''
        return f"{self.usuario} - {self.accion}{target} - {self.fecha:%Y-%m-%d %H:%M}"
