"""
Modelos del app core agrupados por dominio.

Todos los modelos se re-exportan aquí para mantener compatibilidad con
imports existentes como `from core.models import Usuario`.
"""
from ._choices import FACULTADES_CHOICES
from .usuarios import Usuario, SolicitudAcceso
from .firmas import FirmaInstitucional, DisenoGlobal
from .participantes import Participante, ParticipanteToken
from .certificados import LoteCertificados, Certificado
from .sesiones import SesionAsistencia, RegistroAsistencia, ConfirmacionAsistencia, Ponente
from .resumenes import ResumenSesion, EstadoProcesamiento, IntentoCuestionario
from .auditoria import Auditoria
from .integrations import GoogleCredential, AIConfig, AIProvider, PROVIDER_MODELS
from .design_system import UIDesignTokens

__all__ = [
    'FACULTADES_CHOICES',
    'Usuario',
    'SolicitudAcceso',
    'FirmaInstitucional',
    'DisenoGlobal',
    'Participante',
    'ParticipanteToken',
    'LoteCertificados',
    'Certificado',
    'SesionAsistencia',
    'RegistroAsistencia',
    'ConfirmacionAsistencia',
    'Ponente',
    'ResumenSesion',
    'EstadoProcesamiento',
    'IntentoCuestionario',
    'Auditoria',
    'GoogleCredential',
    'AIConfig',
    'AIProvider',
    'PROVIDER_MODELS',
    'UIDesignTokens',
]
