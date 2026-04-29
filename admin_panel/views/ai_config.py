"""Shell HTML para la pantalla de configuración IA.

El form hace fetch a `/api/v1/admin/ai/config/` (PUT) y al endpoint
`/api/v1/admin/ai/config/test/` (POST) para probar la conexión.
Solo accesible para superadmins.
"""
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from core.models import AIConfig, PROVIDER_MODELS

from ._shared import _is_superadmin


@login_required
@user_passes_test(_is_superadmin)
def ai_config(request):
    cfg, _ = AIConfig.objects.get_or_create(pk=1)
    # Aplanamos PROVIDER_MODELS para inyectar como JSON en el template.
    available_models = {
        provider: [{'id': mid, 'label': lbl} for mid, lbl in models]
        for provider, models in PROVIDER_MODELS.items()
    }
    return render(request, 'panel/ai/config.html', {
        'cfg': cfg,
        'available_models': available_models,
    })
