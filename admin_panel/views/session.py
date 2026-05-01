"""Views de sesión: shells HTML. Toda la lógica (CRUD + forms) va por API.

- list: render con context (filtros server-side para permitir ?fecha= ?estado=)
- edit: shell + fetch PATCH
- create: modal en list.html con fetch POST
- qr_display: shell + fetch a qr-info y attendees
- generate_batch: shell + fetch POST a generate-batch action
"""
from django.contrib import messages
from django.db.models import Count, F
from django.shortcuts import get_object_or_404, redirect, render

from core.models import ConfirmacionAsistencia, LoteCertificados, SesionAsistencia
from ._shared import admin_required


@admin_required
def session_list(request):
    """Lista con filtros (el template renderiza cards server-side).

    Mutaciones (toggle/delete/create/edit) van por /api/v1/admin/sessions/.
    """
    fecha_filter = request.GET.get('fecha', '')
    estado_filter = request.GET.get('estado', '')

    qs = SesionAsistencia.objects.select_related('lote').annotate(
        total_confirmados=Count('confirmaciones'),
        total_asistentes=Count('registros'),
    )
    if fecha_filter:
        qs = qs.filter(fecha=fecha_filter)
    if estado_filter == 'llenas':
        qs = qs.filter(total_confirmados__gte=F('capacidad'))
    elif estado_filter == 'con_registro':
        qs = qs.filter(total_asistentes__gt=0)
    elif estado_filter == 'sin_registro':
        qs = qs.filter(total_asistentes=0)

    return render(request, 'panel/sessions/list.html', {
        'sesiones': qs.order_by('-fecha', '-hora_inicio'),
        'lotes': LoteCertificados.objects.filter(activo=True).order_by('nombre_lote'),
        'fechas_disponibles': SesionAsistencia.objects.dates('fecha', 'day', order='DESC'),
        'fecha_filter': fecha_filter,
        'estado_filter': estado_filter,
    })


@admin_required
def session_create(request):
    """Shell de creación de sesión (form completo con ponentes).

    El submit hace POST a /api/v1/admin/sessions/ vía fetch (igual que edit).
    """
    return render(request, 'panel/sessions/create.html')


@admin_required
def session_edit(request, id):
    """Shell de edición: el submit va a PATCH /api/v1/admin/sessions/{id}/."""
    sesion = get_object_or_404(SesionAsistencia, id=id)
    ponentes = list(sesion.ponentes.values('nombre', 'titulo', 'afiliacion', 'bio'))
    return render(request, 'panel/sessions/edit.html', {
        'sesion': sesion,
        'ponentes_json': ponentes,
    })


@admin_required
def session_qr_display(request, id):
    """Pantalla de QR: muestra el código que apunta a /checkin/<codigo_qr>/.

    El template usa qrcodejs (cliente) para renderizarlo. El feed en vivo se
    consulta vía /api/v1/admin/sessions/<id>/attendees/.
    """
    sesion = get_object_or_404(SesionAsistencia, id=id)
    checkin_url = request.build_absolute_uri(
        f'/checkin/{sesion.codigo_qr}/'
    )
    total_registros = sesion.registros.count()
    return render(request, 'panel/sessions/qr.html', {
        'sesion':           sesion,
        'checkin_url':      checkin_url,
        'total_registros':  total_registros,
    })


@admin_required
def session_generate_batch(request, id):
    """Shell para confirmar. El click del botón POSTea a /api/v1/admin/sessions/{id}/generate-batch/."""
    sesion = get_object_or_404(SesionAsistencia, id=id)
    if sesion.lote:
        messages.warning(request, 'Esta sesión ya tiene un lote asociado.')
        return redirect('panel:batch_configure', id=sesion.lote.id)

    total = ConfirmacionAsistencia.objects.filter(
        sesion=sesion, confirmado=True, participante__isnull=False,
    ).count()
    if total == 0:
        messages.error(request, 'No hay participantes confirmados para generar certificados.')
        return redirect('panel:session_list')

    return render(request, 'panel/sessions/generate_batch.html', {
        'sesion': sesion,
        'total_confirmados': total,
    })
