from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from core.models import (
    Certificado, SesionAsistencia, RegistroAsistencia,
    ConfirmacionAsistencia,
)
from core.services.pdf_service import generate_certificate_pdf
import zipfile
import io
import json
from django.utils.text import slugify
from django.utils import timezone


def _check_cert_search_enabled(request):
    """Return access_denied response if cert search is disabled, else None."""
    if not getattr(settings, 'CERT_SEARCH_ENABLED', False):
        return render(request, 'public/access_denied.html', status=403)
    return None


def _get_client_ip(request):
    """Extract real IP from request (supports proxies)."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ─── Landing & Home ──────────────────────────────────────────────

def landing(request):
    """Landing page with options."""
    return render(request, 'public/landing.html')


# ─── Attendance Search & Verify ──────────────────────────────────

def attendance_search(request):
    """Search for attendance verification."""
    query = request.GET.get('q', '').strip()
    return render(request, 'public/attendance_search.html', {'query': query})


def attendance_verify(request):
    """Verify data for a person — smart search by cedula, email, or name."""
    query = request.GET.get('q', '').strip()

    if not query:
        return render(request, 'public/attendance_verify.html', {
            'query': query,
            'personas': [],
            'no_query': True,
        })

    # Smart search: split query into tokens for flexible name matching
    tokens = query.split()

    # Start with broad OR search across all relevant fields
    q_filter = (
        Q(cedula__icontains=query) |
        Q(email__icontains=query)
    )

    # Add name-based search: each token matches against nombres or apellidos
    for token in tokens:
        q_filter = q_filter | Q(nombres__icontains=token) | Q(apellidos__icontains=token)

    resultados = Certificado.objects.filter(q_filter).select_related('lote')

    # Group by unique person (cedula + email combo)
    personas_dict = {}
    for cert in resultados:
        key = (cert.cedula.strip().lower(), cert.email.strip().lower())
        if key not in personas_dict:
            personas_dict[key] = {
                'cedula': cert.cedula,
                'nombres': cert.nombres,
                'apellidos': cert.apellidos,
                'email': cert.email,
                'celular': cert.celular or '',
                'cursos': [],
                'cert_id': cert.id,  # Need first cert ID for confirmation
            }
        personas_dict[key]['cursos'].append(cert.curso)

    personas = list(personas_dict.values())

    # If only one person found, auto-select
    persona_seleccionada = personas[0] if len(personas) == 1 else None

    # Check if person already confirmed for a session
    confirmacion_existente = None
    if persona_seleccionada:
        cert_ids = [c.id for c in resultados if c.cedula == persona_seleccionada['cedula']]
        conf = ConfirmacionAsistencia.objects.filter(
            certificado_id__in=cert_ids, confirmado=True
        ).select_related('sesion').first()
        if conf:
            confirmacion_existente = {
                'dia': conf.sesion.dia_semana,
                'fecha': conf.sesion.fecha.strftime('%d/%m/%Y'),
                'horario': conf.sesion.label,
            }

    # Get the lote IDs this person belongs to
    lote_ids = list(resultados.values_list('lote_id', flat=True).distinct())

    # Get ALL available sessions grouped by day
    sesiones_activas = SesionAsistencia.objects.filter(
        activa=True
    ).order_by('fecha', 'hora_inicio')
    dias_disponibles = {}
    for s in sesiones_activas:
        dia_key = f"{s.dia_semana} - {s.fecha.strftime('%d/%m/%Y')}"
        if dia_key not in dias_disponibles:
            dias_disponibles[dia_key] = []
        dias_disponibles[dia_key].append({
            'id': s.id,
            'label': s.label,
            'titulo': s.titulo,
            'cupos': s.cupos_disponibles,
            'llena': s.esta_llena,
        })

    return render(request, 'public/attendance_verify.html', {
        'query': query,
        'personas': personas,
        'persona': persona_seleccionada,
        'total_resultados': len(personas),
        'dias_disponibles_json': json.dumps(dias_disponibles),
        'confirmacion_existente': confirmacion_existente,
    })


def attendance_autocomplete(request):
    """AJAX endpoint: return matching persons as JSON for live search."""
    query = request.GET.get('q', '').strip()

    if len(query) < 3:
        return JsonResponse({'results': []})

    tokens = query.split()

    q_filter = (
        Q(cedula__icontains=query) |
        Q(email__icontains=query)
    )
    for token in tokens:
        q_filter = q_filter | Q(nombres__icontains=token) | Q(apellidos__icontains=token)

    resultados = Certificado.objects.filter(q_filter).select_related('lote')[:100]

    personas_dict = {}
    for cert in resultados:
        key = (cert.cedula.strip().lower(), cert.email.strip().lower())
        if key not in personas_dict:
            personas_dict[key] = {
                'id': cert.id,
                'cedula': cert.cedula,
                'nombres': cert.nombres,
                'apellidos': cert.apellidos,
                'email': cert.email,
                'cursos_count': 0,
            }
        personas_dict[key]['cursos_count'] += 1

    results = list(personas_dict.values())[:20]

    return JsonResponse({'results': results})


# ─── Attendance Confirmation ─────────────────────────────────────

def attendance_sessions_api(request):
    """AJAX: Return active sessions grouped by day for the dependent select."""
    sesiones = SesionAsistencia.objects.filter(activa=True).order_by('fecha', 'hora_inicio')
    dias = {}
    for s in sesiones:
        dia_key = f"{s.dia_semana} - {s.fecha.strftime('%d/%m/%Y')}"
        if dia_key not in dias:
            dias[dia_key] = []
        dias[dia_key].append({
            'id': s.id,
            'label': s.label,
            'titulo': s.titulo,
            'cupos': s.cupos_disponibles,
            'llena': s.esta_llena,
        })
    return JsonResponse({'dias': dias})


@require_POST
def attendance_confirm(request):
    """Confirm attendance for a session — creates ConfirmacionAsistencia."""
    cert_id = request.POST.get('cert_id')
    sesion_id = request.POST.get('sesion_id')

    if not cert_id or not sesion_id:
        return JsonResponse({'ok': False, 'error': 'Datos incompletos.'}, status=400)

    try:
        certificado = Certificado.objects.get(id=cert_id)
        sesion = SesionAsistencia.objects.get(id=sesion_id, activa=True)
    except (Certificado.DoesNotExist, SesionAsistencia.DoesNotExist):
        return JsonResponse({'ok': False, 'error': 'Sesión o participante no encontrado.'}, status=404)

    # Check if session is full
    if sesion.esta_llena:
        return JsonResponse({
            'ok': False,
            'error': f'Esta sesión ya alcanzó el cupo máximo de {sesion.capacidad} personas. Por favor, elige otro horario.'
        }, status=409)

    # Check if already confirmed
    conf, created = ConfirmacionAsistencia.objects.get_or_create(
        certificado=certificado,
        sesion=sesion,
        defaults={'confirmado': True}
    )

    if not created:
        return JsonResponse({'ok': True, 'already': True, 'message': 'Ya estás confirmado para esta sesión.'})

    cupos = sesion.cupos_disponibles
    return JsonResponse({
        'ok': True,
        'already': False,
        'message': f'Asistencia confirmada para {sesion.dia_semana} {sesion.label}. Quedan {cupos} cupos. ¡Recuerda asistir!'
    })


@require_POST
def attendance_update_phone(request):
    """AJAX: Update attendee's phone number on all their certificates."""
    cert_id = request.POST.get('cert_id')
    celular = request.POST.get('celular', '').strip()

    if not cert_id:
        return JsonResponse({'ok': False, 'error': 'Faltan datos.'}, status=400)

    try:
        certificado = Certificado.objects.get(id=cert_id)
        # Keep data synchronized across all certificates assigned to this person (by cédula)
        Certificado.objects.filter(cedula=certificado.cedula).update(celular=celular)
        return JsonResponse({'ok': True, 'celular': celular})
    except Certificado.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Participante no encontrado.'}, status=404)
        

# ─── QR Check-in (Public Scan) ──────────────────────────────────

def qr_checkin(request, codigo_qr):
    """Public QR check-in page — shown when attendee scans QR code."""
    sesion = get_object_or_404(SesionAsistencia, codigo_qr=codigo_qr, activa=True)
    return render(request, 'public/qr_checkin.html', {
        'sesion': sesion,
        'codigo_qr': codigo_qr,
    })


def qr_checkin_search(request, codigo_qr):
    """AJAX: Search for a person during QR check-in (reuses autocomplete logic)."""
    sesion = get_object_or_404(SesionAsistencia, codigo_qr=codigo_qr, activa=True)
    query = request.GET.get('q', '').strip()

    if len(query) < 3:
        return JsonResponse({'results': []})

    tokens = query.split()
    q_filter = Q(cedula__icontains=query) | Q(email__icontains=query)
    for token in tokens:
        q_filter = q_filter | Q(nombres__icontains=token) | Q(apellidos__icontains=token)

    resultados = Certificado.objects.filter(q_filter)[:50]

    personas_dict = {}
    for cert in resultados:
        key = (cert.cedula.strip().lower(), cert.email.strip().lower())
        if key not in personas_dict:
            # Check if already registered in this session
            already = RegistroAsistencia.objects.filter(
                sesion=sesion, certificado=cert
            ).exists()
            # Check if confirmed/associated with this session
            confirmed = ConfirmacionAsistencia.objects.filter(
                sesion=sesion, certificado=cert, confirmado=True
            ).exists()

            personas_dict[key] = {
                'id': cert.id,
                'cedula': cert.cedula,
                'nombres': cert.nombres,
                'apellidos': cert.apellidos,
                'email': cert.email,
                'already_registered': already,
                'is_confirmed': confirmed,
            }

    return JsonResponse({'results': list(personas_dict.values())[:15]})


@require_POST
def qr_checkin_register(request, codigo_qr):
    """Register attendance via QR scan — marks the person present."""
    sesion = get_object_or_404(SesionAsistencia, codigo_qr=codigo_qr, activa=True)

    try:
        data = json.loads(request.body)
        cert_id = data.get('cert_id')
    except (json.JSONDecodeError, AttributeError):
        cert_id = request.POST.get('cert_id')

    if not cert_id:
        return JsonResponse({'ok': False, 'error': 'Datos incompletos.'}, status=400)

    try:
        certificado = Certificado.objects.get(id=cert_id)
    except Certificado.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Participante no encontrado.'}, status=404)

    # 1. Check if blocked
    blocked = ConfirmacionAsistencia.objects.filter(
        certificado=certificado, bloqueado=True
    ).exists()
    if blocked:
        return JsonResponse({
            'ok': False,
            'error': 'Tu cuenta está bloqueada por inasistencias previas. Contacta al administrador.'
        }, status=403)

    # 2. Check if person is associated/confirmed for THIS specific session
    is_confirmed = ConfirmacionAsistencia.objects.filter(
        certificado=certificado,
        sesion=sesion,
        confirmado=True
    ).exists()
    
    if not is_confirmed:
        return JsonResponse({
            'ok': False,
            'error': f'No tienes una confirmación de cupo registrada para la sesión de {sesion.dia_semana} {sesion.label}.'
        }, status=403)

    # 3. Create or get attendance record
    registro, created = RegistroAsistencia.objects.get_or_create(
        sesion=sesion,
        certificado=certificado,
        defaults={'ip_address': _get_client_ip(request)}
    )

    if not created:
        return JsonResponse({
            'ok': True,
            'already': True,
            'message': '¡Ya registraste tu asistencia anteriormente!',
            'nombre': f'{certificado.nombres} {certificado.apellidos}',
        })

    return JsonResponse({
        'ok': True,
        'already': False,
        'message': '¡Gracias por estar aquí! Tu asistencia fue registrada exitosamente.',
        'nombre': f'{certificado.nombres} {certificado.apellidos}',
        'hora': timezone.now().strftime('%H:%M'),
    })


# ─── Certificate Search & Download ──────────────────────────────

def home(request):
    """Public homepage."""
    denied = _check_cert_search_enabled(request)
    if denied:
        return denied
    return render(request, 'public/home.html')


def search(request):
    """Search certificates by ID, email, or name."""
    denied = _check_cert_search_enabled(request)
    if denied:
        return denied

    query = request.GET.get('q', '').strip()
    certificados = []

    if query:
        query_lower = query.lower()
        certificados = list(
            Certificado.objects.filter(
                Q(cedula__iexact=query) |
                Q(email__iexact=query_lower) |
                Q(hash_verificacion__iexact=query)
            ).select_related('lote')
        )

        for c in certificados:
            c.veces_buscado += 1
            c.save(update_fields=['veces_buscado'])

    nombre_estudiante = None
    if certificados:
        cert = certificados[0]
        nombre_estudiante = f"{cert.nombres} {cert.apellidos}".title()

    return render(request, 'public/search.html', {
        'certificados': certificados,
        'query': query,
        'nombre_estudiante': nombre_estudiante,
        'total_certificados': len(certificados),
    })


@xframe_options_exempt
def download_pdf(request, hash):
    """Download/preview a single certificate PDF."""
    denied = _check_cert_search_enabled(request)
    if denied:
        return denied

    certificado = get_object_or_404(Certificado, hash_verificacion=hash)

    try:
        pdf_buffer = generate_certificate_pdf(certificado)
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'inline; filename="Certificado_{certificado.cedula}.pdf"'
        )

        certificado.descargas_count += 1
        certificado.save(update_fields=['descargas_count'])

        return response
    except Exception as e:
        return HttpResponse(f"Error generando PDF: {str(e)}", status=500)


def download_zip(request):
    """Bulk download all certificates matching a search query as ZIP."""
    denied = _check_cert_search_enabled(request)
    if denied:
        return denied

    query = request.GET.get('q', '').strip()
    if not query:
        return HttpResponse("No query provided", status=400)

    certificados = Certificado.objects.filter(
        Q(cedula__icontains=query)
        | Q(email__icontains=query)
        | Q(nombres__icontains=query)
        | Q(apellidos__icontains=query)
    ).select_related('lote')

    if not certificados:
        return HttpResponse("No certificates found", status=404)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for cert in certificados:
            try:
                pdf_buffer = generate_certificate_pdf(cert)
                safe_curso = slugify(cert.curso)
                filename = f"{safe_curso}_{cert.cedula}.pdf"
                zip_file.writestr(filename, pdf_buffer.getvalue())
            except Exception:
                continue

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Certificados_{query}.zip"'
    return response


