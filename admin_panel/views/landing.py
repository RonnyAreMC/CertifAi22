"""Shell del builder. Las mutaciones van por /api/v1/admin/landing/blocks/."""
from datetime import date

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

from core.models import LandingBloque, SesionAsistencia


@login_required
@user_passes_test(lambda u: u.rol == 'superadmin')
def landing_builder(request):
    return render(request, 'panel/landing/builder.html', {
        'bloques': LandingBloque.objects.all(),
        'eventos_futuros': SesionAsistencia.objects.filter(
            fecha__gte=date.today(), activa=True
        ).order_by('fecha', 'hora_inicio'),
        'tipo_choices': LandingBloque.TIPO_CHOICES,
        'estilo_choices': LandingBloque.ESTILO_CHOICES,
    })
