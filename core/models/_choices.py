"""Shim de compatibilidad — el contenido real vive en `catalogos.enums`.

Mantener este archivo para que los imports legacy
    from core.models._choices import FACULTADES_CHOICES, Rol, …
sigan funcionando. Código nuevo debería importar desde
    from core.models.catalogos import …
"""
from .catalogos.enums import (  # noqa: F401
    FACULTADES_CHOICES,
    Rol,
    EstadoSolicitud,
    Plantilla,
    DiaSemana,
    Modalidad,
    PlataformaVirtual,
)
