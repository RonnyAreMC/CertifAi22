"""Wrapper para Anthropic Claude API. Se activa al configurar ANTHROPIC_API_KEY."""
import os
from functools import lru_cache


def is_configured() -> bool:
    return bool(os.environ.get('ANTHROPIC_API_KEY'))


@lru_cache
def get_claude_client():
    """Devuelve un cliente de Anthropic si está configurado, si no None.

    Se usa lru_cache para reutilizar la conexión.
    """
    if not is_configured():
        return None
    try:
        from anthropic import Anthropic
    except ImportError:
        return None
    return Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])


def call_claude(
    system: str,
    user: str,
    model: str = 'claude-haiku-4-5-20251001',
    max_tokens: int = 1024,
) -> str:
    """Llama a Claude con prompt caching en el system prompt.

    Retorna el texto de la respuesta, o lanza NotImplementedError si no está configurado.
    """
    client = get_claude_client()
    if client is None:
        raise NotImplementedError(
            'ANTHROPIC_API_KEY no configurado. Instala `anthropic` y setea la env var.'
        )

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[{
            'type': 'text',
            'text': system,
            'cache_control': {'type': 'ephemeral'},
        }],
        messages=[{'role': 'user', 'content': user}],
    )
    return response.content[0].text
