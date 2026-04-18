"""Views de batch (lotes de certificados).

Solo las que tienen forms con uploads Excel / mapping / file uploads del diseño
se quedan como Django views. El resto (list, delete, preview_pdf) va por API.
"""
import base64

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect, render

from core.models import FirmaInstitucional, LoteCertificados
from core.services.excel_service import analyze_headers, process_excel_batch
from ._shared import _is_admin


@login_required
@user_passes_test(_is_admin)
def list_batches(request):
    """Render con los lotes para el template de lista."""
    return render(request, 'panel/batch/list.html', {
        'lotes': LoteCertificados.objects.all().order_by('id'),
    })


@login_required
@user_passes_test(_is_admin)
def create_batch(request):
    """Shell del form. Submit va a /api/v1/admin/batches/ via fetch+FormData."""
    from core.models import FACULTADES_CHOICES
    return render(request, 'panel/batch/form.html', {
        'facultades_choices': FACULTADES_CHOICES,
    })


@login_required
@user_passes_test(_is_admin)
def process_batch_mapping(request, id):
    """UI de mapeo de columnas Excel tras crear el lote."""
    lote = get_object_or_404(LoteCertificados, id=id)

    if request.method == 'POST':
        name_strategy = request.POST.get('name_strategy', 'single')
        if name_strategy == 'split':
            col_nombres = request.POST.get('col_nombres_split')
            col_apellidos = request.POST.get('col_apellidos')
        else:
            col_nombres = request.POST.get('col_nombres')
            col_apellidos = None

        mapping = {
            'cedula': request.POST.get('col_cedula'),
            'nombres': col_nombres,
            'apellidos': col_apellidos,
            'email': request.POST.get('col_email'),
            'celular': request.POST.get('col_celular'),
            'curso': request.POST.get('col_curso'),
        }
        try:
            success, msg = process_excel_batch(lote.id, mapping=mapping)
            if success:
                messages.success(request, f'Lote cargado exitosamente. {msg}')
                if lote.archivo_excel:
                    lote.archivo_excel.delete(save=True)
                return redirect('panel:batch_list')
            messages.error(request, f'Error al procesar: {msg}')
        except Exception as e:
            messages.error(request, f'Error crítico: {e}')
        return redirect('panel:batch_process_mapping', id=lote.id)

    analysis = analyze_headers(lote.id)
    if not analysis['success']:
        messages.error(request, f"Error leyendo el Excel: {analysis.get('error')}")
        return redirect('panel:batch_list')

    return render(request, 'panel/batch/mapping.html', {
        'lotes': lote,
        'columns': analysis['columns'],
        'suggestions': analysis['suggestions'],
        'preview': analysis['preview'],
    })


@login_required
@user_passes_test(_is_admin)
def batch_detail(request, id):
    lote = get_object_or_404(LoteCertificados, id=id)
    return render(request, 'panel/batch/detail.html', {
        'lote': lote,
        'certificados': lote.certificados.all(),
    })


@login_required
@user_passes_test(_is_admin)
def configure_batch(request, id):
    """Form de diseño personalizado para un lote (colores, firmas, logos)."""
    lote = get_object_or_404(LoteCertificados, id=id)

    if request.method == 'POST':
        from core.models import DisenoGlobal
        try:
            diseno_global = DisenoGlobal.get_solo()
        except Exception:
            diseno_global = None

        lote.personalizar_diseno = request.POST.get('personalizar_diseno') == 'on'
        lote.cuerpo_certificado = request.POST.get('cuerpo_certificado') or lote.cuerpo_certificado

        plantilla = request.POST.get('plantilla')
        if plantilla:
            lote.plantilla = plantilla
            if diseno_global and plantilla != diseno_global.plantilla:
                lote.personalizar_diseno = True

        for field in ('color_primario', 'color_secundario', 'color_terciario', 'color_texto'):
            val = request.POST.get(field)
            if val:
                setattr(lote, field, val)
                if diseno_global and val != getattr(diseno_global, field, None):
                    lote.personalizar_diseno = True

        for i in range(1, 4):
            firma_id = request.POST.get(f'firma_inst_{i}')
            if firma_id:
                setattr(lote, f'firma_inst_{i}_id', int(firma_id))
            else:
                setattr(lote, f'firma_inst_{i}', None)

        lote.firma_inst_4 = None
        if (nombre := request.POST.get('nombre_firma_4')) is not None:
            lote.nombre_firma_4 = nombre
        if (cargo := request.POST.get('cargo_firma_4')) is not None:
            lote.cargo_firma_4 = cargo
        if 'imagen_firma_4' in request.FILES:
            file_obj = request.FILES['imagen_firma_4']
            lote.imagen_firma_4 = base64.b64encode(file_obj.read()).decode('utf-8')

        for i in (1, 2, 3):
            key = f'logo_header_{i}'
            if key in request.FILES:
                setattr(lote, key, request.FILES[key])

        lote.save()
        messages.success(
            request,
            'Diseño personalizado guardado para este lote.' if lote.personalizar_diseno
            else 'Lote actualizado. Está usando el Diseño Global.',
        )
        return redirect('panel:batch_configure', id=lote.id)

    return render(request, 'panel/batch/config.html', {
        'lote': lote,
        'firmas_institucionales': FirmaInstitucional.objects.filter(activa=True).order_by('nombre'),
    })
