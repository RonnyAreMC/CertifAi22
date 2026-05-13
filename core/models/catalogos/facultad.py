"""Catálogo dinámico de Facultades editable desde el admin.

A diferencia de `FACULTADES_CHOICES` (hardcoded), este modelo permite que
el admin agregue, edite o desactive facultades sin redeploy. Coexiste con
el enum por compatibilidad — la migración a usar SOLO el modelo dinámico
se hará cuando todos los `CharField(choices=FACULTADES_CHOICES)` se
reemplacen por `ForeignKey(Facultad)`.

Seed: al aplicar la migración, se crean filas con los 5 valores del enum.
"""
from django.db import models


class Facultad(models.Model):
    """Facultad o programa académico de UNEMI (catálogo administrable)."""
    codigo = models.CharField(
        max_length=20, unique=True,
        help_text='Código corto único (ej. FACI, FACS). Usado en FK desde otros modelos.',
    )
    nombre = models.CharField(
        max_length=120,
        help_text='Nombre completo de la facultad (ej. "FACI - Ingeniería").',
    )
    descripcion = models.TextField(
        blank=True, default='',
        help_text='Descripción opcional de la facultad.',
    )
    orden = models.PositiveSmallIntegerField(
        default=0,
        help_text='Orden de aparición en selects. Menor = primero.',
    )
    activa = models.BooleanField(
        default=True, db_index=True,
        help_text='Si está desactivada, no aparece en selects pero conserva las relaciones existentes.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Facultad'
        verbose_name_plural = 'Facultades'
        ordering = ['orden', 'nombre']

    def __str__(self):
        return self.nombre
