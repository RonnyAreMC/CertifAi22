"""
Modelos del app core agrupados por dominio.

Todos los modelos se re-exportan aquí para mantener compatibilidad con
imports existentes como `from core.models import Usuario`.
"""
from ._choices import FACULTADES_CHOICES
from .usuarios import Usuario, SolicitudAcceso
from .firmas import FirmaInstitucional, DisenoGlobal
from .participantes import Participante
from .certificados import LoteCertificados, Certificado
from .sesiones import SesionAsistencia, RegistroAsistencia, ConfirmacionAsistencia
from .auditoria import Auditoria
from .landing import LandingBloque

__all__ = [
    'FACULTADES_CHOICES',
    'Usuario',
    'SolicitudAcceso',
    'FirmaInstitucional',
    'DisenoGlobal',
    'Participante',
    'LoteCertificados',
    'Certificado',
    'SesionAsistencia',
    'RegistroAsistencia',
    'ConfirmacionAsistencia',
    'Auditoria',
    'LandingBloque',
]
