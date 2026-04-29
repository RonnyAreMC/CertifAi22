"""Modelos de sesiones, registro de asistencia y confirmaciones."""
import uuid
from django.db import models

from core.managers import SesionManager

from ._choices import DiaSemana, Modalidad, PlataformaVirtual


class SesionAsistencia(models.Model):
    """Sesión con día/horario específico para tomar asistencia.

    Invariantes:
      - Si `modalidad='virtual'`, debe tener `enlace_virtual` (clean()).
      - `codigo_qr` es único e inmutable (usado en URL pública de check-in).
      - Sesiones pueden cruzar medianoche (hora_fin < hora_inicio) para eventos nocturnos.
    """
    lote = models.ForeignKey(
        'core.LoteCertificados', on_delete=models.CASCADE,
        related_name='sesiones', verbose_name='Seminario',
        null=True, blank=True
    )
    titulo = models.CharField(
        max_length=200, blank=True,
        help_text='Título descriptivo (ej: "Sesión Mañana - Lunes")'
    )
    descripcion = models.TextField(blank=True, default='', verbose_name='Descripción')
    imagen_banner = models.ImageField(
        upload_to='sesiones_banners/', null=True, blank=True,
        verbose_name='Imagen de banner',
        help_text='Imagen promocional que se muestra en la página de registro'
    )
    modalidad = models.CharField(
        max_length=15, choices=Modalidad.choices, default=Modalidad.PRESENCIAL,
        verbose_name='Modalidad'
    )
    plataforma_virtual = models.CharField(
        max_length=15, choices=PlataformaVirtual.choices, blank=True, default='',
        verbose_name='Plataforma',
        help_text='Solo aplica si la modalidad es virtual'
    )
    enlace_virtual = models.URLField(
        max_length=500, blank=True, default='',
        verbose_name='Enlace de reunión',
        help_text='URL de Zoom/Meet/Teams u otra plataforma (solo si es virtual)'
    )
    lugar = models.CharField(max_length=300, blank=True, default='', verbose_name='Lugar')
    fecha = models.DateField(verbose_name='Fecha de la Sesión')
    dia_semana = models.CharField(
        max_length=12, choices=DiaSemana.choices, verbose_name='Día'
    )
    hora_inicio = models.TimeField(verbose_name='Hora Inicio')
    hora_fin = models.TimeField(verbose_name='Hora Fin')
    codigo_qr = models.CharField(
        max_length=64, unique=True, default=uuid.uuid4,
        editable=False, db_index=True
    )
    capacidad = models.PositiveIntegerField(
        default=0, verbose_name='Cupos Máximos',
        help_text='0 = ilimitado'
    )
    solo_lideres = models.BooleanField(
        default=False, verbose_name='Solo Líderes Académicos',
        help_text='Solo participantes marcados como líderes pueden registrarse'
    )
    activa = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Integración Google Meet (Fase 2)
    google_calendar_event_id = models.CharField(
        max_length=200, blank=True, default='', db_index=True,
        help_text='ID del evento en Google Calendar (para actualizarlo o eliminarlo).'
    )
    transcripcion_habilitada = models.BooleanField(
        default=True, verbose_name='Generar resumen IA del evento',
        help_text='Si está activo, el transcript de Meet se procesa con IA tras la sesión.'
    )

    objects = SesionManager()

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        verbose_name = 'Sesión de Asistencia'
        verbose_name_plural = 'Sesiones de Asistencia'
        indexes = [
            models.Index(fields=['codigo_qr']),
            models.Index(fields=['fecha', 'activa']),
        ]

    def __str__(self):
        return (
            f"{self.dia_semana} {self.fecha} "
            f"({self.hora_inicio:%H:%M}–{self.hora_fin:%H:%M})"
        )

    @property
    def label(self):
        return f"{self.hora_inicio:%H:%M} – {self.hora_fin:%H:%M}"

    @property
    def capacidad_ilimitada(self):
        return self.capacidad == 0

    @property
    def confirmados_count(self):
        return self.confirmaciones.count()

    @property
    def cupos_disponibles(self):
        if self.capacidad_ilimitada:
            return None  # None = ilimitado
        return max(0, self.capacidad - self.confirmados_count)

    @property
    def esta_llena(self):
        if self.capacidad_ilimitada:
            return False
        return self.confirmados_count >= self.capacidad

    @property
    def es_virtual(self):
        return self.modalidad == Modalidad.VIRTUAL

    @property
    def plataforma_display_safe(self):
        if self.plataforma_virtual:
            return self.get_plataforma_virtual_display()
        return 'Reunión virtual'

    def clean(self):
        """Una sesión virtual con plataforma=meet puede dejar el enlace vacío:
        se rellena automáticamente al crear el evento en Google Calendar.
        Para otras plataformas (Zoom/Teams) sigue siendo obligatorio.
        """
        from django.core.exceptions import ValidationError
        if self.modalidad == Modalidad.VIRTUAL and not self.enlace_virtual:
            if self.plataforma_virtual != PlataformaVirtual.MEET:
                raise ValidationError({
                    'enlace_virtual': 'Debes proporcionar un enlace para eventos virtuales.'
                })


class Ponente(models.Model):
    """Persona que dicta una sesión.

    Una sesión puede tener 1 o varios ponentes. Si se elimina la sesión, se
    eliminan sus ponentes (cascada). El campo `orden` controla el orden de
    aparición en la página pública del evento.
    """
    sesion = models.ForeignKey(
        SesionAsistencia, on_delete=models.CASCADE,
        related_name='ponentes',
    )
    nombre = models.CharField(max_length=200, verbose_name='Nombre completo')
    titulo = models.CharField(
        max_length=100, blank=True, default='',
        verbose_name='Título / Cargo',
        help_text='Ej.: Dr., Mgs., Ing., PhD'
    )
    afiliacion = models.CharField(
        max_length=200, blank=True, default='',
        verbose_name='Afiliación / Institución',
        help_text='Ej.: UNEMI, MIT, Stanford'
    )
    bio = models.TextField(blank=True, default='', verbose_name='Biografía corta')
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['orden', 'nombre']
        verbose_name = 'Ponente'
        verbose_name_plural = 'Ponentes'

    def __str__(self):
        prefix = f'{self.titulo} ' if self.titulo else ''
        return f'{prefix}{self.nombre}'.strip()

    @property
    def display_name(self) -> str:
        prefix = f'{self.titulo} ' if self.titulo else ''
        sufijo = f' · {self.afiliacion}' if self.afiliacion else ''
        return f'{prefix}{self.nombre}{sufijo}'.strip()


class RegistroAsistencia(models.Model):
    """Marca de asistencia al escanear el QR durante la sesión.

    Un participante NO puede registrar asistencia 2 veces en la misma sesión
    (unique sesion+participante). Se guarda IP para auditoría.
    """
    sesion = models.ForeignKey(
        SesionAsistencia, on_delete=models.CASCADE,
        related_name='registros'
    )
    certificado = models.ForeignKey(
        'core.Certificado', on_delete=models.CASCADE,
        related_name='asistencias',
        null=True, blank=True
    )
    participante = models.ForeignKey(
        'core.Participante', on_delete=models.CASCADE,
        related_name='asistencias',
        null=True, blank=True
    )
    fecha_registro = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-fecha_registro']
        verbose_name = 'Registro de Asistencia'
        verbose_name_plural = 'Registros de Asistencia'
        constraints = [
            models.UniqueConstraint(
                fields=['sesion', 'participante'],
                name='unique_registro_sesion_participante',
            ),
        ]

    def __str__(self):
        nombre = self.participante.nombres if self.participante else (self.certificado.nombres if self.certificado else '?')
        return f"{nombre} → {self.sesion}"


class ConfirmacionAsistencia(models.Model):
    """Confirmación previa: el participante se compromete a asistir.

    Invariantes:
      - Único por (participante, sesion): no se puede confirmar 2 veces.
      - `bloqueado=True` cuando el participante confirmó pero no asistió
        (marcado manualmente por admin para penalizar ausencias).
    """
    certificado = models.ForeignKey(
        'core.Certificado', on_delete=models.CASCADE,
        related_name='confirmaciones',
        null=True, blank=True
    )
    participante = models.ForeignKey(
        'core.Participante', on_delete=models.CASCADE,
        related_name='confirmaciones',
        null=True, blank=True
    )
    sesion = models.ForeignKey(
        SesionAsistencia, on_delete=models.CASCADE,
        related_name='confirmaciones'
    )
    confirmado = models.BooleanField(default=True)
    bloqueado = models.BooleanField(
        default=False,
        help_text='Si faltó sin justificación, se bloquea la cuenta.'
    )
    fecha_confirmacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_confirmacion']
        verbose_name = 'Confirmación de Asistencia'
        verbose_name_plural = 'Confirmaciones de Asistencia'
        constraints = [
            models.UniqueConstraint(
                fields=['participante', 'sesion'],
                name='unique_confirmacion_participante_sesion',
            ),
        ]

    def __str__(self):
        nombre = self.participante.nombres if self.participante else (self.certificado.nombres if self.certificado else '?')
        status = 'Bloqueado' if self.bloqueado else 'Confirmado'
        return f"{nombre} — {status}"
