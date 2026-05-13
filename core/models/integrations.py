"""Credenciales OAuth de servicios externos (Google Workspace) y configuración IA.

Diseño: una sola fila representa la cuenta institucional que organiza
los Meets. El refresh_token vive aquí para que la app pueda llamar a
Calendar/Drive/Docs sin intervención humana.

`AIConfig` es un singleton con la configuración del proveedor de IA
(Claude / OpenAI / Groq) — selecciona uno y administra su API key sin
tocar `.env`.
"""
from django.db import models

from core.base.fields import EncryptedCharField, EncryptedTextField
from core.base.models import SingletonModel, TimestampedModel


class GoogleCredential(TimestampedModel):
    """OAuth 2.0 access + refresh tokens para una cuenta Google.

    Convención: existe **una sola fila** con la cuenta institucional
    (rarellanou@unemi.edu.ec). Si en el futuro hace falta multi-cuenta,
    se quita el unique=True del email.

    Tokens y client_secret están **cifrados at-rest** con Fernet (AES-128 +
    HMAC) derivado de SECRET_KEY. La lectura/escritura es transparente.
    """
    email = models.EmailField(unique=True, help_text='Cuenta Google conectada')
    access_token = EncryptedTextField()
    refresh_token = EncryptedTextField(help_text='Token de larga duración para auto-refrescar')
    token_uri = models.URLField(default='https://oauth2.googleapis.com/token')
    client_id = models.CharField(max_length=200)
    client_secret = EncryptedCharField(max_length=500, help_text='Cifrado at-rest con Fernet')
    scopes = models.JSONField(default=list)
    expiry = models.DateTimeField(null=True, blank=True, help_text='Cuándo expira el access_token')

    class Meta:
        verbose_name = 'Credencial Google'
        verbose_name_plural = 'Credenciales Google'

    def __str__(self) -> str:
        return f'GoogleCredential<{self.email}>'

    @classmethod
    def get_singleton(cls) -> 'GoogleCredential | None':
        """Devuelve la primera credencial registrada (o None si no hay)."""
        return cls.objects.first()


class AIProvider(models.TextChoices):
    CLAUDE = 'claude', 'Anthropic Claude'
    OPENAI = 'openai', 'OpenAI (GPT)'
    GROQ = 'groq', 'Groq (Llama / Mixtral)'


# Modelos sugeridos por proveedor (para el dropdown del form).
# Claude usa IDs con fecha (más estables); OpenAI y Groq usan slugs.
PROVIDER_MODELS = {
    AIProvider.CLAUDE: [
        ('claude-haiku-4-5-20251001', 'Claude Haiku 4.5 (rápido y económico)'),
        ('claude-sonnet-4-6', 'Claude Sonnet 4.6 (equilibrado)'),
        ('claude-opus-4-7', 'Claude Opus 4.7 (máxima calidad)'),
    ],
    AIProvider.OPENAI: [
        ('gpt-4o-mini', 'GPT-4o mini (rápido y económico)'),
        ('gpt-4o', 'GPT-4o (equilibrado)'),
        ('gpt-4-turbo', 'GPT-4 Turbo'),
    ],
    AIProvider.GROQ: [
        ('llama-3.3-70b-versatile', 'Llama 3.3 70B (recomendado)'),
        ('llama-3.1-8b-instant', 'Llama 3.1 8B (ultra rápido)'),
        ('mixtral-8x7b-32768', 'Mixtral 8×7B'),
    ],
}


class AIConfig(SingletonModel, TimestampedModel):
    """Singleton con la configuración del proveedor de IA activo.

    Solo existe una fila (pk=1). El admin elige proveedor + modelo,
    pega la API key y los servicios `core.services.ai.*` la usan
    automáticamente. Si está deshabilitado o sin key, las features de
    IA devuelven 501 y los formularios funcionan sin asistencia IA.
    """
    provider = models.CharField(
        max_length=20, choices=AIProvider.choices, default=AIProvider.CLAUDE,
        verbose_name='Proveedor de IA',
    )
    model = models.CharField(
        max_length=80, blank=True, default='claude-haiku-4-5-20251001',
        verbose_name='Modelo',
        help_text='Identificador del modelo según el proveedor (ej. claude-haiku-4-5-20251001).',
    )
    api_key = EncryptedCharField(
        max_length=1000, blank=True, default='',
        help_text='Cifrado at-rest con Fernet. Solo visible para Python (no SQL).',
    )
    temperature = models.FloatField(
        default=0.7,
        help_text='0.0 = más determinista, 1.0 = más creativo.',
    )
    max_tokens = models.PositiveIntegerField(
        default=1024,
        help_text='Tope máximo de tokens en la respuesta.',
    )
    system_prompt_override = models.TextField(
        blank=True, default='',
        verbose_name='System prompt global (opcional)',
        help_text='Si se llena, se antepone a todos los prompts del sistema.',
    )
    enabled = models.BooleanField(
        default=False,
        help_text='Si está apagado, todas las features de IA quedan deshabilitadas.',
    )

    class Meta:
        verbose_name = 'Configuración IA'
        verbose_name_plural = 'Configuración IA'

    def __str__(self) -> str:
        return f'AIConfig<{self.provider}:{self.model} {"ON" if self.enabled else "OFF"}>'

    def is_ready(self) -> bool:
        """True si está habilitada y tiene api_key."""
        return self.enabled and bool(self.api_key) and bool(self.model)

    def masked_api_key(self) -> str:
        """Devuelve la key con todo enmascarado salvo los últimos 4 chars."""
        if not self.api_key:
            return ''
        if len(self.api_key) <= 8:
            return '••••••••'
        return f'{self.api_key[:4]}••••••••{self.api_key[-4:]}'
