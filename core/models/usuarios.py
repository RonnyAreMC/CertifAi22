"""Modelos de usuarios y solicitudes de acceso al sistema."""
from django.db import models
from django.contrib.auth.models import AbstractUser

from core.validators import validar_telefono_ecuador

from ._choices import FACULTADES_CHOICES, Rol, EstadoSolicitud


class Usuario(AbstractUser):
    """Usuario del sistema (solo administradores).

    Relación con `SolicitudAcceso`: al registrarse se crea una solicitud
    `pendiente`. El superadmin la aprueba para activar el usuario.
    """
    rol = models.CharField(
        max_length=20, choices=Rol.choices, default=Rol.ADMIN, db_index=True,
    )
    facultad = models.CharField(
        max_length=20,
        choices=FACULTADES_CHOICES,
        blank=True,
        db_index=True,
    )
    telefono = models.CharField(
        max_length=20, blank=True, validators=[validar_telefono_ecuador],
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    ultimo_acceso = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Usuario Administrador'
        verbose_name_plural = 'Usuarios Administradores'

    def __str__(self):
        return f"{self.get_full_name()} ({self.rol})"

    @property
    def nombre_completo(self):
        """Nombre + apellido o username como fallback."""
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username

    @property
    def es_superadmin(self):
        return self.rol == Rol.SUPERADMIN


class SolicitudAcceso(models.Model):
    """Solicitud de acceso para nuevos administradores - requiere aprobación.

    Invariantes:
      - Al rechazar debe guardarse `motivo_rechazo`.
      - `usuario_creado` apunta al Usuario que se activa al aprobar.
    """
    nombres = models.CharField(max_length=100, verbose_name='Nombres')
    apellidos = models.CharField(max_length=100, verbose_name='Apellidos')
    email = models.EmailField(unique=True, verbose_name='Email')
    telefono = models.CharField(
        max_length=20, blank=True, verbose_name='Teléfono',
        validators=[validar_telefono_ecuador],
    )
    facultad = models.CharField(
        max_length=20,
        choices=FACULTADES_CHOICES,
        default='FACI',
        verbose_name='Facultad / Departamento'
    )

    estado = models.CharField(
        max_length=20,
        choices=EstadoSolicitud.choices,
        default=EstadoSolicitud.PENDIENTE,
        db_index=True,
    )

    usuario_creado = models.OneToOneField(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitud_acceso',
        verbose_name='Usuario Creado'
    )

    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_respuesta = models.DateTimeField(null=True, blank=True)
    aprobado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='solicitudes_aprobadas',
        verbose_name='Aprobado por'
    )
    motivo_rechazo = models.TextField(blank=True, verbose_name='Motivo del Rechazo')

    class Meta:
        ordering = ['-fecha_solicitud']
        verbose_name = 'Solicitud de Acceso'
        verbose_name_plural = 'Solicitudes de Acceso'
        indexes = [
            models.Index(fields=['estado', '-fecha_solicitud']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.nombres} {self.apellidos} - {self.get_estado_display()}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()
