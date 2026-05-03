"""ResumenSesion — resultado del pipeline IA de Drive → transcript → resumen.

Se mantiene 1-a-1 con `SesionAsistencia` (related_name='resumen') para poder
reprocesar sin tocar el modelo principal de la sesión.
"""
from __future__ import annotations

from django.db import models


class EstadoProcesamiento(models.TextChoices):
    PENDIENTE   = 'pendiente',  'Pendiente'           # creado pero no encolado
    BUSCANDO    = 'buscando',   'Buscando transcript' # explorando Drive
    PROCESANDO  = 'procesando', 'Procesando con IA'   # llamando a Claude
    LISTO       = 'listo',      'Listo'               # resumen disponible
    SIN_TRANSCRIPT = 'sin_transcript', 'Sin transcript' # Meet no generó uno
    FALLIDO     = 'fallido',    'Fallido'             # error fatal


class ResumenSesion(models.Model):
    """Resumen IA de una sesión, generado a partir del transcript de Meet.

    Pipeline:
      1. `drive_client` busca el transcript en la carpeta de la sesión.
      2. `transcript_parser` extrae el texto plano.
      3. `ai/transcript_summary` llama a Claude para generar resumen + Q&A.
      4. Se guarda en este modelo.
    """
    sesion = models.OneToOneField(
        'core.SesionAsistencia',
        on_delete=models.CASCADE,
        related_name='resumen',
    )

    # ── Origen del transcript ────────────────────────────────────────
    drive_file_id = models.CharField(
        max_length=200, blank=True, default='', db_index=True,
        help_text='ID del documento de transcript en Google Drive.'
    )
    drive_file_name = models.CharField(
        max_length=300, blank=True, default='',
        help_text='Nombre del archivo de transcript en Drive (referencia).'
    )
    transcript_raw = models.TextField(
        blank=True, default='',
        help_text='Texto plano del transcript (parseado, sin formato).'
    )
    transcript_chars = models.IntegerField(
        default=0,
        help_text='Cantidad de caracteres del transcript (para auditoría).'
    )

    # ── Resultado IA ─────────────────────────────────────────────────
    resumen_md = models.TextField(
        blank=True, default='',
        help_text='Resumen ejecutivo en Markdown (puntos clave + decisiones).'
    )
    puntos_clave = models.JSONField(
        default=list, blank=True,
        help_text='Lista de strings: bullet points del evento.'
    )
    proximos_pasos = models.JSONField(
        default=list, blank=True,
        help_text='Lista de strings: acciones recomendadas post-evento.'
    )
    cuestionario = models.JSONField(
        default=list, blank=True,
        help_text=(
            'Lista de preguntas para repasar lo aprendido. '
            'Formato: [{pregunta, opciones: [...], correcta_idx, explicacion}]'
        )
    )
    duracion_minutos = models.IntegerField(
        default=0,
        help_text='Duración estimada del evento (de transcript timestamps).'
    )

    # ── Estado y auditoría ───────────────────────────────────────────
    estado = models.CharField(
        max_length=20,
        choices=EstadoProcesamiento.choices,
        default=EstadoProcesamiento.PENDIENTE,
        db_index=True,
    )
    error_msg = models.TextField(
        blank=True, default='',
        help_text='Stack trace si estado=fallido.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    procesado_at = models.DateTimeField(null=True, blank=True)

    # Modelo IA usado (para auditoría de cambios entre versiones)
    ai_model = models.CharField(max_length=80, blank=True, default='')
    ai_input_tokens  = models.IntegerField(default=0)
    ai_output_tokens = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Resumen IA de sesión'
        verbose_name_plural = 'Resúmenes IA de sesiones'
        ordering = ['-created_at']

    def __str__(self):
        return f'Resumen #{self.id} · sesión {self.sesion_id} · {self.estado}'

    @property
    def is_ready(self) -> bool:
        return self.estado == EstadoProcesamiento.LISTO

    @property
    def has_failed(self) -> bool:
        return self.estado in (EstadoProcesamiento.FALLIDO, EstadoProcesamiento.SIN_TRANSCRIPT)


class IntentoCuestionario(models.Model):
    """Intento de un participante respondiendo el cuestionario IA de una sesión.

    Reglas:
      - Cada participante puede tener hasta `MAX_INTENTOS` intentos por sesión.
      - El score se guarda al completar (todas las preguntas respondidas o
        agotadas por timer) — no se persiste si abandona a mitad.
    """
    MAX_INTENTOS = 2

    participante = models.ForeignKey(
        'core.Participante', on_delete=models.CASCADE,
        related_name='intentos_cuestionario',
    )
    sesion = models.ForeignKey(
        'core.SesionAsistencia', on_delete=models.CASCADE,
        related_name='intentos_cuestionario',
    )
    correctas = models.PositiveSmallIntegerField()
    total = models.PositiveSmallIntegerField()
    tiempo_total_seg = models.PositiveIntegerField(default=0)
    respuestas = models.JSONField(
        default=list, blank=True,
        help_text='Lista de índices elegidos por el participante (null = sin responder).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Intento de cuestionario'
        verbose_name_plural = 'Intentos de cuestionario'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['participante', 'sesion']),
        ]

    def __str__(self):
        return f'Intento #{self.id} · sesión {self.sesion_id} · {self.correctas}/{self.total}'

    @property
    def porcentaje(self) -> int:
        if not self.total:
            return 0
        return round(self.correctas / self.total * 100)
