"""Modelo de participantes/estudiantes del sistema."""
from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.core.exceptions import ValidationError

from core.base.models import TimestampedModel
from core.managers import ParticipanteManager
from core.validators import validar_cedula_ecuador, validar_telefono_ecuador


class Participante(TimestampedModel):
    """Registro único de un participante/estudiante en el sistema.

    Invariantes:
      - Debe tener al menos `cedula` O `email` (validado en clean()).
      - `cedula` única cuando no vacía; `email` único cuando no vacío.

    Auth opcional:
      - `password_hash` se setea solo si el participante crea cuenta pública.
      - El flujo "guest" (registro a evento por cédula sin cuenta) sigue
        funcionando: si no hay password, no hay login posible — sólo búsqueda.
    """
    cedula = models.CharField(
        max_length=20, blank=True, default='', db_index=True,
        validators=[validar_cedula_ecuador],
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=200, db_index=True)
    celular = models.CharField(
        max_length=20, blank=True, default='',
        validators=[validar_telefono_ecuador],
    )
    es_lider = models.BooleanField(
        default=False, verbose_name='Líder Académico', db_index=True,
    )

    # ─── Auth pública (opcional) ────────────────────────────────
    password_hash = models.CharField(
        max_length=255, blank=True, default='',
        help_text='Hash PBKDF2 (Django). Vacío = guest (sin cuenta).',
    )
    last_login = models.DateTimeField(null=True, blank=True)
    avatar = models.ImageField(
        upload_to='participantes/avatars/', null=True, blank=True,
        help_text='Foto de perfil (opcional).',
    )

    class Meta:
        verbose_name = 'Participante'
        verbose_name_plural = 'Participantes'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['cedula'],
                name='unique_cedula_when_not_empty',
                condition=~models.Q(cedula=''),
            ),
            models.UniqueConstraint(
                fields=['email'],
                name='unique_email_when_not_empty',
                condition=~models.Q(email=''),
            ),
        ]
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['cedula']),
        ]

    objects = ParticipanteManager()

    def clean(self):
        if not self.cedula and not self.email:
            raise ValidationError('Debe proporcionar al menos cédula o correo electrónico.')

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.cedula or self.email})"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()

    @property
    def has_account(self) -> bool:
        """True si el participante tiene cuenta (password seteado)."""
        return bool(self.password_hash)

    @property
    def initials(self) -> str:
        n = (self.nombres or '').strip()
        a = (self.apellidos or '').strip()
        return ((n[:1] + a[:1]) or 'P').upper()

    # ─── Auth helpers ───────────────────────────────────────────
    def set_password(self, raw_password: str) -> None:
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password(raw_password, self.password_hash)
