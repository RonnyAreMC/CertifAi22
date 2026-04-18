"""Fase 8: Copilot para el cuerpo del certificado — PLACEHOLDER."""
from .client import is_configured


def generate_body_text(
    tipo_evento: str = 'seminario',
    contexto: str = '',
    tono: str = 'formal',
    accion: str = 'create',
) -> dict:
    if not is_configured():
        return {
            'implemented': False,
            'message': 'Feature pendiente (Fase 8). Configura ANTHROPIC_API_KEY para habilitar.',
        }
    # TODO Fase 8: implementar con call_claude()
    return {
        'implemented': False,
        'message': 'Generador de cuerpo — en desarrollo',
    }
