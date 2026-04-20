"""Modelo de bloques configurables del landing page público."""
from django.db import models

from core.base.models import TimestampedModel

from ._choices import LandingTipo, LandingEstilo


class LandingBloque(TimestampedModel):
    """Bloque configurable del landing page público (hero, stats, features, CTA, eventos).

    Los bloques se renderizan ordenados por `orden`. Admite vincular a una
    `SesionAsistencia` para promocionar eventos futuros directamente.
    """
    tipo = models.CharField(max_length=20, choices=LandingTipo.choices, default=LandingTipo.HERO)
    estilo = models.CharField(max_length=30, choices=LandingEstilo.choices, default=LandingEstilo.HERO_GRADIENT)
    orden = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    # Contenido
    titulo = models.CharField(max_length=200, blank=True)
    subtitulo = models.CharField(max_length=300, blank=True)
    descripcion = models.TextField(blank=True)

    # Items JSON (para stats, steps, features — lista de objetos)
    # Ej stats: [{"icono":"fa-solid fa-certificate","valor":"5,000+","label":"Certificados","color":"blue"}]
    # Ej steps: [{"icono":"fa-solid fa-search","titulo":"Busca","desc":"...","numero":"1"}]
    # Ej features: [{"icono":"fa-solid fa-shield","titulo":"Seguro","desc":"...","color":"blue"}]
    items_json = models.JSONField(default=list, blank=True)

    # Imágenes
    imagen_principal = models.ImageField(upload_to='landing/', null=True, blank=True)
    imagen_2 = models.ImageField(upload_to='landing/', null=True, blank=True)
    imagen_3 = models.ImageField(upload_to='landing/', null=True, blank=True)

    # Colores
    color_fondo = models.CharField(max_length=7, default='#162054')
    color_texto = models.CharField(max_length=7, default='#FFFFFF')
    color_acento = models.CharField(max_length=7, default='#F58830')

    # Evento vinculado
    sesion = models.ForeignKey(
        'core.SesionAsistencia', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='landing_bloques',
        verbose_name='Evento vinculado'
    )

    # Botones configurables (hasta 2)
    boton_1_texto = models.CharField(max_length=100, blank=True)
    boton_1_url = models.CharField(max_length=500, blank=True)
    boton_1_icono = models.CharField(max_length=50, blank=True, default='fa-solid fa-arrow-right')
    boton_2_texto = models.CharField(max_length=100, blank=True)
    boton_2_url = models.CharField(max_length=500, blank=True)
    boton_2_icono = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['orden']
        verbose_name = 'Bloque de Landing'
        verbose_name_plural = 'Bloques de Landing'

    def __str__(self):
        return f"[{self.orden}] {self.get_tipo_display()} - {self.titulo or 'Sin título'}"
