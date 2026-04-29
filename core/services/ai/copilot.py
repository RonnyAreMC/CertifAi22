"""Copilot IA para descripciones de eventos.

Genera HTML enriquecido a partir del título del evento + un prompt libre
del usuario + una acción (crear / mejorar / expandir / resumir / formal /
amigable). El HTML que devuelve es compatible con CKEditor (etiquetas
limitadas: p, strong, em, ul, ol, li, h2, h3, blockquote, br).
"""
from __future__ import annotations

from .client import call_ai, is_configured


SYSTEM_PROMPT = """Sos un asistente experto en redacción de descripciones para eventos académicos y de capacitación profesional en español ecuatoriano.

REGLAS ESTRICTAS:
1. Devolvé SOLO HTML válido, sin explicaciones ni markdown. Empezá directo con la primera etiqueta.
2. Etiquetas permitidas: <p>, <strong>, <em>, <ul>, <ol>, <li>, <h2>, <h3>, <blockquote>, <br>.
3. NO uses <html>, <body>, <head>, <div>, <span>, <script>, <style> ni atributos.
4. Tono profesional pero cercano. Sin jerga corporativa vacía.
5. **Usá ESTRUCTURA visual real** (no solo <p>):
   - Primer <p>: párrafo de bienvenida con la propuesta de valor.
   - <h2>¿Qué aprenderás?</h2> seguido de <ul><li>...</li></ul> con 3-5 bullets concretos.
   - <h2>¿A quién va dirigido?</h2> seguido de <p> describiendo el público.
   - <p> de cierre con call-to-action suave (ej.: "Te esperamos para...").
6. Resaltá conceptos clave dentro de los párrafos con <strong>.
7. Entre 100 y 250 palabras (salvo que la acción pida resumir → 1-2 párrafos cortos sin estructura).
8. Sin emojis. Sin firmas. Sin saludos al final.
9. Respetá el español ecuatoriano (usá "ustedes", no "vosotros").
10. Si el contexto del usuario es vago, asumí lo mínimo razonable y no inventes datos específicos (fechas, nombres de ponentes, lugares concretos).

Si no podés generar algo coherente, devolvé un párrafo simple."""


ACTION_INSTRUCTIONS = {
    'create':   'Generá una descripción NUEVA desde cero usando el título y el contexto.',
    'improve':  'MEJORÁ la descripción actual: redacción, claridad, estructura. No agregues información que no esté.',
    'expand':   'EXPANDÍ la descripción actual con más detalle, ejemplos y estructura. Mantené el sentido original.',
    'shorten':  'RESUMÍ la descripción actual a 1-2 párrafos cortos, sin perder lo esencial.',
    'formal':   'Reescribí en un tono FORMAL e institucional, manteniendo la información.',
    'friendly': 'Reescribí en un tono más AMIGABLE y cercano, sin perder profesionalismo.',
}


def improve_event_description(
    titulo: str,
    accion: str = 'create',
    contexto: str = '',
    descripcion_actual: str = '',
) -> dict:
    """Genera HTML para la descripción de un evento.

    Devuelve `{'implemented': bool, 'html'?: str, 'message'?: str}`.
    """
    titulo = (titulo or '').strip()
    if not titulo:
        return {'implemented': False, 'message': 'Necesitamos al menos el título del evento.'}

    if not is_configured():
        return {
            'implemented': False,
            'message': 'IA no configurada. Andá a Admin → Configuración IA y activá un proveedor.',
        }

    action_key = accion if accion in ACTION_INSTRUCTIONS else 'create'
    action_instr = ACTION_INSTRUCTIONS[action_key]

    parts = [
        f'TÍTULO DEL EVENTO: {titulo}',
        f'ACCIÓN: {action_instr}',
    ]
    if contexto.strip():
        parts.append(f'CONTEXTO ADICIONAL DEL ORGANIZADOR:\n{contexto.strip()}')
    if descripcion_actual.strip() and action_key in ('improve', 'expand', 'shorten', 'formal', 'friendly'):
        parts.append(f'DESCRIPCIÓN ACTUAL (para refinar):\n{descripcion_actual.strip()}')

    user_message = '\n\n'.join(parts) + '\n\nDevolvé solo el HTML.'

    try:
        html = call_ai(system=SYSTEM_PROMPT, user=user_message)
    except NotImplementedError as exc:
        return {'implemented': False, 'message': str(exc)}
    except Exception as exc:  # noqa: BLE001 — devolvemos el error al admin
        return {'implemented': False, 'message': f'{type(exc).__name__}: {exc}'}

    return {'implemented': True, 'html': _sanitize_html(html), 'action': action_key}


def _sanitize_html(html: str) -> str:
    """Limpieza ligera: quita backticks o ```html que a veces el modelo devuelve."""
    text = (html or '').strip()
    # Si empieza con ```html ... ``` lo limpiamos
    if text.startswith('```'):
        text = text.lstrip('`').lstrip()
        if text.lower().startswith('html'):
            text = text[4:].lstrip()
        if text.endswith('```'):
            text = text[:-3].rstrip()
    return text.strip()


# ── Compat con código viejo (Fase 8 placeholder) ─────────────

def generate_body_text(
    tipo_evento: str = 'seminario',
    contexto: str = '',
    tono: str = 'formal',
    accion: str = 'create',
) -> dict:
    """Wrapper legacy. Usa el copilot real con `tipo_evento` como título."""
    titulo = f'{tipo_evento.capitalize()}: {contexto[:80]}' if contexto else tipo_evento.capitalize()
    return improve_event_description(
        titulo=titulo, accion=accion, contexto=contexto,
    )
