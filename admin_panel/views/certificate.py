"""add_certificate: POST handler para form del batch detail.

participante_lookup eliminado: usar /api/v1/admin/participants/?search= directamente.
"""
from datetime import datetime
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect

from core.models import Certificado, LoteCertificados, Participante
from ._shared import _is_admin, _log_audit


@login_required
@user_passes_test(_is_admin)
def add_certificate(request, id):
    """POST form del batch_detail para agregar un certificado al lote."""
    lote = get_object_or_404(LoteCertificados, id=id)

    if request.method != 'POST':
        return redirect('panel:batch_detail', id=lote.id)

    try:
        fecha_str = request.POST.get('fecha_curso')
        fecha_curso = datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None

        cedula_raw = (request.POST.get('cedula') or '').strip()
        nombres_raw = (request.POST.get('nombres') or '').strip().upper()
        apellidos_raw = (request.POST.get('apellidos') or '').strip().upper()
        email_raw = (request.POST.get('email') or '').strip().lower()
        celular_raw = (request.POST.get('celular') or '').strip()

        is_generated = cedula_raw.startswith('GEN-') or not cedula_raw
        real_cedula = '' if is_generated else cedula_raw

        participante = None
        if real_cedula:
            participante = Participante.objects.filter(cedula=real_cedula).first()
        if not participante and email_raw:
            participante = Participante.objects.filter(email__iexact=email_raw).first()

        if participante:
            updated = []
            if real_cedula and not participante.cedula:
                participante.cedula = real_cedula
                updated.append('cedula')
            if celular_raw and not participante.celular:
                participante.celular = celular_raw
                updated.append('celular')
            if updated:
                participante.save(update_fields=updated)
        else:
            participante = Participante.objects.create(
                cedula=real_cedula, nombres=nombres_raw, apellidos=apellidos_raw,
                email=email_raw, celular=celular_raw,
            )

        Certificado.objects.create(
            lote=lote, participante=participante,
            cedula=cedula_raw or f'GEN-{uuid.uuid4().hex[:8].upper()}',
            nombres=nombres_raw, apellidos=apellidos_raw, email=email_raw,
            curso=request.POST.get('curso'),
            horas=int(request.POST.get('horas', 0)),
            fecha_curso=fecha_curso,
        )
        _log_audit(
            request.user, 'AGREGAR_CERTIFICADO',
            f'Certificado agregado manual: {cedula_raw} en lote {lote.nombre_lote}',
        )
        messages.success(request, 'Certificado agregado correctamente.')
    except Exception as e:
        messages.error(request, f'Error al agregar certificado: {e}')

    return redirect('panel:batch_detail', id=lote.id)
