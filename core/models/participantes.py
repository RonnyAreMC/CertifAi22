"""Modelo de participantes/estudiantes del sistema."""
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
