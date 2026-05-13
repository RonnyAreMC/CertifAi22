"""Catálogos del sistema — tanto enums estáticos como tablas lookup dinámicas.

División interna:
- `enums.py`       → TextChoices Django (valores cerrados conocidos en código)
- `facultad.py`    → modelo dinámico Facultad (editable desde admin)

Los enums siguen siendo la fuente de verdad para campos cerrados como `Rol`,
`EstadoSolicitud`, `Plantilla`, etc. Los modelos dinámicos son para
entidades que el cliente puede querer ampliar sin redeploy.
"""
from .enums import (
    FACULTADES_CHOICES,
    Rol,
    EstadoSolicitud,
    Plantilla,
    DiaSemana,
    Modalidad,
    PlataformaVirtual,
)
from .facultad import Facultad

__all__ = [
    'FACULTADES_CHOICES',
    'Rol',
    'EstadoSolicitud',
    'Plantilla',
    'DiaSemana',
    'Modalidad',
    'PlataformaVirtual',
    'Facultad',
]
