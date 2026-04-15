from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.http import FileResponse, HttpResponse, JsonResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.conf import settings
from core.models import (
    Certificado, SesionAsistencia, RegistroAsistencia,
    ConfirmacionAsistencia, Participante,
    LoteCertificados,
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


def search_autocomplete(request):
    """AJAX endpoint: return certificate-holder names for live search autocomplete."""
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': []})

    tokens = [t.strip() for t in query.split() if t.strip()]
    if not tokens:
        return JsonResponse({'results': []})

    # Search Participante first (canonical, deduplicated source)
    q_filter = Q()
    for token in tokens:
        q_filter &= (
            Q(cedula__icontains=token) |
            Q(email__icontains=token) |
            Q(nombres__icontains=token) |
            Q(apellidos__icontains=token)
        )

    participantes = Participante.objects.filter(q_filter)[:20]
    resultados = []
    seen = set()

    for p in participantes:
        full_name = f"{p.nombres.strip()} {p.apellidos.strip()}".strip()
        if not full_name:
            continue
        key = full_name.lower()
        if key in seen:
            continue
        seen.add(key)
        resultados.append({'name': full_name})
        if len(resultados) >= 12:
            break

    # Fallback: also check Certificado for orphaned records without Participante
    if len(resultados) < 12:
        q_cert = Q()
        for token in tokens:
            q_cert &= (
                Q(cedula__icontains=token) |
                Q(email__icontains=token) |
                Q(nombres__icontains=token) |
                Q(apellidos__icontains=token)
            )
        orphan_certs = (
            Certificado.objects.filter(q_cert, participante__isnull=True)
            .values('nombres', 'apellidos').distinct()[:20]
        )
        for cert in orphan_certs:
            full_name = f"{cert.get('nombres', '').strip()} {cert.get('apellidos', '').strip()}".strip()
            if not full_name:
                continue
            key = full_name.lower()
            if key in seen:
                continue
            seen.add(key)
            resultados.append({'name': full_name})
            if len(resultados) >= 12:
                break

    return JsonResponse({'results': resultados})


def _get_client_ip(request):
    """Extract real IP from request (supports proxies)."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ─── Landing & Home ──────────────────────────────────────────────

def landing(request):
    """Landing page — siempre static con stats reales calculadas en vivo."""
    total_certificados = Certificado.objects.count()
    total_seminarios = LoteCertificados.objects.count()
    total_participantes = Participante.objects.count()
    total_sesiones = SesionAsistencia.objects.filter(activa=True).count()

    return render(request, 'public/landing.html', {
        'total_certificados': total_certificados,
        'total_seminarios': total_seminarios,
        'total_participantes': total_participantes,
        'total_sesiones': total_sesiones,
    })


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

    # Search in Participante model directly
    q_filter = (
        Q(cedula__icontains=query) |
        Q(email__icontains=query)
    )
    for token in tokens:
        q_filter = q_filter | Q(nombres__icontains=token) | Q(apellidos__icontains=token)

    participantes = Participante.objects.filter(q_filter)[:50]

    personas = []
    for p in participantes:
        cursos = list(p.certificados.values_list('curso', flat=True).distinct())
        personas.append({
            'cedula': p.cedula,
            'nombres': p.nombres,
            'apellidos': p.apellidos,
            'email': p.email,
            'celular': p.celular or '',
            'cursos': cursos,
            'participante_id': p.id,
            'cert_id': p.certificados.values_list('id', flat=True).first(),
        })

    # If only one person found, auto-select
    persona_seleccionada = personas[0] if len(personas) == 1 else None

    # Check if person already confirmed for a session
    confirmacion_existente = None
    if persona_seleccionada:
        conf = ConfirmacionAsistencia.objects.filter(
            participante_id=persona_seleccionada['participante_id'], confirmado=True
        ).select_related('sesion').first()
        if conf:
            confirmacion_existente = {
                'dia': conf.sesion.dia_semana,
                'fecha': conf.sesion.fecha.strftime('%d/%m/%Y'),
                'horario': conf.sesion.label,
            }

    # Get ALL available sessions grouped by day
    sesiones_activas = SesionAsistencia.objects.filter(
        activa=True
    ).order_by('fecha', 'hora_inicio')
    dias_disponibles = {}
    for s in sesiones_activas:
        dia_key = f"{s.dia_semana} - {s.fecha.strftime('%d/%m/%Y')}"
        if dia_key not in dias_disponibles:
            dias_disponibles[dia_key] = []
        cupos = s.cupos_disponibles
        dias_disponibles[dia_key].append({
            'id': s.id,
            'label': s.label,
            'titulo': s.titulo,
            'cupos': cupos if cupos is not None else 9999,
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

    participantes = Participante.objects.filter(q_filter)[:20]

    results = []
    for p in participantes:
        results.append({
            'id': p.id,
            'cedula': p.cedula,
            'nombres': p.nombres,
            'apellidos': p.apellidos,
            'email': p.email,
            'cursos_count': p.certificados.count(),
        })

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
    # Support both participante_id (new) and cert_id (legacy)
    participante_id = request.POST.get('participante_id')
    cert_id = request.POST.get('cert_id')
    sesion_id = request.POST.get('sesion_id')

    if not sesion_id:
        return JsonResponse({'ok': False, 'error': 'Datos incompletos.'}, status=400)

    try:
        sesion = SesionAsistencia.objects.get(id=sesion_id, activa=True)
    except SesionAsistencia.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Sesión no encontrada.'}, status=404)

    # Resolve participante
    participante = None
    if participante_id:
        try:
            participante = Participante.objects.get(id=participante_id)
        except Participante.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Participante no encontrado.'}, status=404)
    elif cert_id:
        try:
            cert = Certificado.objects.get(id=cert_id)
            participante = cert.participante
            if not participante:
                return JsonResponse({'ok': False, 'error': 'Participante no vinculado.'}, status=404)
        except Certificado.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Certificado no encontrado.'}, status=404)
    else:
        return JsonResponse({'ok': False, 'error': 'Datos incompletos.'}, status=400)

    # Check if session is full
    if sesion.esta_llena:
        return JsonResponse({
            'ok': False,
            'error': f'Esta sesión ya alcanzó el cupo máximo de {sesion.capacidad} personas. Por favor, elige otro horario.'
        }, status=409)

    # Check if already confirmed
    conf, created = ConfirmacionAsistencia.objects.get_or_create(
        participante=participante,
        sesion=sesion,
        defaults={'confirmado': True}
    )

    if not created:
        return JsonResponse({'ok': True, 'already': True, 'message': 'Ya estás confirmado para esta sesión.'})

    cupos = sesion.cupos_disponibles
    cupos_msg = f'Quedan {cupos} cupos.' if cupos is not None else ''
    return JsonResponse({
        'ok': True,
        'already': False,
        'message': f'Asistencia confirmada para {sesion.dia_semana} {sesion.label}. {cupos_msg} ¡Recuerda asistir!'
    })


@require_POST
def attendance_update_phone(request):
    """AJAX: Update attendee's phone number."""
    participante_id = request.POST.get('participante_id')
    cert_id = request.POST.get('cert_id')
    celular = request.POST.get('celular', '').strip()

    if participante_id:
        try:
            p = Participante.objects.get(id=participante_id)
            p.celular = celular
            p.save(update_fields=['celular'])
            # Sync to certificates
            Certificado.objects.filter(participante=p).update(celular=celular)
            return JsonResponse({'ok': True, 'celular': celular})
        except Participante.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Participante no encontrado.'}, status=404)
    elif cert_id:
        try:
            certificado = Certificado.objects.get(id=cert_id)
            Certificado.objects.filter(cedula=certificado.cedula).update(celular=celular)
            if certificado.participante:
                certificado.participante.celular = celular
                certificado.participante.save(update_fields=['celular'])
            return JsonResponse({'ok': True, 'celular': celular})
        except Certificado.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'Participante no encontrado.'}, status=404)

    return JsonResponse({'ok': False, 'error': 'Faltan datos.'}, status=400)
        

# ─── QR Check-in (Public Scan) ──────────────────────────────────

def qr_checkin(request, codigo_qr):
    """Public QR check-in page — shown when attendee scans QR code."""
    sesion = get_object_or_404(SesionAsistencia, codigo_qr=codigo_qr, activa=True)
    return render(request, 'public/qr_checkin.html', {
        'sesion': sesion,
        'codigo_qr': codigo_qr,
    })


def qr_checkin_search(request, codigo_qr):
    """AJAX: Search for a person during QR check-in."""
    sesion = get_object_or_404(SesionAsistencia, codigo_qr=codigo_qr, activa=True)
    query = request.GET.get('q', '').strip()

    if len(query) < 3:
        return JsonResponse({'results': []})

    tokens = query.split()
    q_filter = Q(cedula__icontains=query) | Q(email__icontains=query)
    for token in tokens:
        q_filter = q_filter | Q(nombres__icontains=token) | Q(apellidos__icontains=token)

    participantes = Participante.objects.filter(q_filter)[:15]

    results = []
    for p in participantes:
        already = RegistroAsistencia.objects.filter(
            sesion=sesion, participante=p
        ).exists()
        confirmed = ConfirmacionAsistencia.objects.filter(
            sesion=sesion, participante=p, confirmado=True
        ).exists()

        results.append({
            'id': p.id,
            'cedula': p.cedula,
            'nombres': p.nombres,
            'apellidos': p.apellidos,
            'email': p.email,
            'already_registered': already,
            'is_confirmed': confirmed,
        })

    return JsonResponse({'results': results})


@require_POST
def qr_checkin_register(request, codigo_qr):
    """Register attendance via QR scan — marks the person present."""
    sesion = get_object_or_404(SesionAsistencia, codigo_qr=codigo_qr, activa=True)

    try:
        data = json.loads(request.body)
        participant_id = data.get('id') or data.get('cert_id')
    except (json.JSONDecodeError, AttributeError):
        participant_id = request.POST.get('id') or request.POST.get('cert_id')

    if not participant_id:
        return JsonResponse({'ok': False, 'error': 'Datos incompletos.'}, status=400)

    # Try Participante first, fallback to Certificado for legacy
    participante = None
    try:
        participante = Participante.objects.get(id=participant_id)
    except Participante.DoesNotExist:
        try:
            cert = Certificado.objects.get(id=participant_id)
            participante = cert.participante
        except Certificado.DoesNotExist:
            pass

    if not participante:
        return JsonResponse({'ok': False, 'error': 'Participante no encontrado.'}, status=404)

    # 1. Check if blocked
    blocked = ConfirmacionAsistencia.objects.filter(
        participante=participante, bloqueado=True
    ).exists()
    if blocked:
        return JsonResponse({
            'ok': False,
            'error': 'Tu cuenta está bloqueada por inasistencias previas. Contacta al administrador.'
        }, status=403)

    # 2. Check if confirmed for THIS specific session
    is_confirmed = ConfirmacionAsistencia.objects.filter(
        participante=participante,
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
        participante=participante,
        defaults={'ip_address': _get_client_ip(request)}
    )

    if not created:
        return JsonResponse({
            'ok': True,
            'already': True,
            'message': '¡Ya registraste tu asistencia anteriormente!',
            'nombre': f'{participante.nombres} {participante.apellidos}',
        })

    return JsonResponse({
        'ok': True,
        'already': False,
        'message': '¡Gracias por estar aquí! Tu asistencia fue registrada exitosamente.',
        'nombre': f'{participante.nombres} {participante.apellidos}',
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
    """Search certificates by ID, email, or verification hash."""
    denied = _check_cert_search_enabled(request)
    if denied:
        return denied

    query = request.GET.get('q', '').strip()
    certificados = []

    if query:
        query_lower = query.lower()

        # Build token-aware name search (to support full name and partial matching)
        tokens = [t.strip() for t in query.split() if t.strip()]
        name_filter = Q()
        if tokens:
            for token in tokens:
                name_filter &= (
                    Q(nombres__icontains=token) |
                    Q(apellidos__icontains=token)
                )

        certificados = list(
            Certificado.objects.filter(
                Q(cedula__iexact=query) |
                Q(email__iexact=query_lower) |
                Q(hash_verificacion__iexact=query) |
                name_filter
            ).select_related('lote').distinct()
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

        safe_curso = slugify(certificado.curso or 'certificado') or 'certificado'
        short_hash = str(certificado.hash_verificacion)[:8]
        filename = f"Certificado_{certificado.cedula}_{safe_curso}_{short_hash}.pdf"

        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'

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
        seen_names = {}
        for cert in certificados:
            try:
                pdf_buffer = generate_certificate_pdf(cert)
                safe_curso = slugify(cert.curso) or 'certificado'
                base = f"{safe_curso}_{cert.cedula}"
                count = seen_names.get(base, 0)
                seen_names[base] = count + 1
                filename = f"{base}.pdf" if count == 0 else f"{base}_{count+1}.pdf"
                zip_file.writestr(filename, pdf_buffer.getvalue())
            except Exception:
                continue

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Certificados_{query}.zip"'
    return response


# ─── Smart Session Registration (Public) ─────────────────────────

def _find_participante(query):
    """Find a Participante by cedula or email."""
    query = query.strip()
    if not query:
        return None
    # Try cedula first
    p = Participante.objects.filter(cedula__iexact=query).first()
    if p:
        return p
    # Try email
    p = Participante.objects.filter(email__iexact=query).first()
    return p


def session_register(request, id):
    """Smart registration page for a session."""
    sesion = get_object_or_404(SesionAsistencia, id=id, activa=True)

    context = {
        'sesion': sesion,
        'cupos': sesion.cupos_disponibles,
        'capacidad_ilimitada': sesion.capacidad_ilimitada,
    }
    return render(request, 'public/session_register.html', context)


def session_register_search(request, id):
    """AJAX: Search for existing participant by cedula, email, or name."""
    sesion = get_object_or_404(SesionAsistencia, id=id, activa=True)
    query = request.GET.get('q', '').strip()

    if len(query) < 3:
        return JsonResponse({'found': False, 'results': []})

    # Smart search: tokens for flexible matching
    tokens = query.split()
    q_filter = Q(cedula__icontains=query) | Q(email__icontains=query)
    for token in tokens:
        q_filter |= Q(nombres__icontains=token) | Q(apellidos__icontains=token)

    participantes = Participante.objects.filter(q_filter).distinct()[:15]

    if not participantes.exists():
        return JsonResponse({'found': False, 'results': []})

    results = []
    for p in participantes:
        # Check if already confirmed for this session
        ya_confirmado = ConfirmacionAsistencia.objects.filter(
            participante=p, sesion=sesion, confirmado=True
        ).exists()

        # Get courses (including legacy ones not linked to Participante but matching ID/Email)
        q_cursos = Q(participante=p)
        if p.cedula: q_cursos |= Q(cedula=p.cedula)
        if p.email: q_cursos |= Q(email=p.email)
        
        cursos = list(Certificado.objects.filter(q_cursos).values_list('curso', flat=True).distinct()[:5])

        # Check for missing info
        missing = []
        if not p.cedula: missing.append('cedula')
        if not p.email: missing.append('email')
        if not p.nombres: missing.append('nombres')
        if not p.apellidos: missing.append('apellidos')
        if not p.celular: missing.append('celular')

        results.append({
            'id': p.id,
            'cedula': p.cedula,
            'nombres': p.nombres,
            'apellidos': p.apellidos,
            'email': p.email,
            'celular': p.celular,
            'cursos': cursos,
            'ya_confirmado': ya_confirmado,
            'missing_info': missing
        })

    return JsonResponse({
        'found': True,
        'count': len(results),
        'results': results,
        # Legacy support for single-result logic
        'participante': results[0],
        'ya_confirmado': results[0]['ya_confirmado'],
        'missing_info': results[0]['missing_info']
    })


@require_POST
def session_register_confirm(request, id):
    """Confirm an existing participant for a session."""
    sesion = get_object_or_404(SesionAsistencia, id=id, activa=True)

    participante_id = request.POST.get('participante_id')
    if not participante_id:
        return JsonResponse({'ok': False, 'error': 'Datos incompletos.'}, status=400)

    try:
        participante = Participante.objects.get(id=participante_id)
    except Participante.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Participante no encontrado.'}, status=404)

    # Check líder restriction
    if sesion.solo_lideres and not participante.es_lider:
        return JsonResponse({
            'ok': False,
            'error': 'Este evento es exclusivo para Líderes Académicos. Si crees que es un error, contacta al administrador.'
        }, status=403)

    # Update fields if provided
    celular = request.POST.get('celular', '').strip()
    email = request.POST.get('email', '').strip()
    cedula = request.POST.get('cedula', '').strip()
    nombres = request.POST.get('nombres', '').strip()
    apellidos = request.POST.get('apellidos', '').strip()

    fields_to_update = []
    if celular and celular != participante.celular:
        participante.celular = celular
        fields_to_update.append('celular')
    if email and email != participante.email:
        participante.email = email
        fields_to_update.append('email')
    if cedula and not participante.cedula:
        participante.cedula = cedula
        fields_to_update.append('cedula')
    if nombres and not participante.nombres:
        participante.nombres = nombres
        fields_to_update.append('nombres')
    if apellidos and not participante.apellidos:
        participante.apellidos = apellidos
        fields_to_update.append('apellidos')

    if fields_to_update:
        participante.save(update_fields=fields_to_update)

    # Check capacity
    if sesion.esta_llena:
        return JsonResponse({
            'ok': False,
            'error': 'Esta sesión ya alcanzó el cupo máximo. Por favor, intenta otro horario.'
        }, status=409)

    # Create confirmation
    conf, created = ConfirmacionAsistencia.objects.get_or_create(
        participante=participante,
        sesion=sesion,
        defaults={'confirmado': True}
    )

    if not created:
        return JsonResponse({'ok': True, 'already': True, 'message': 'Ya estás registrado en esta sesión.'})

    return JsonResponse({
        'ok': True,
        'already': False,
        'message': f'Registro exitoso para {participante.nombres}.',
        'sesion': {
            'titulo': sesion.titulo or sesion.dia_semana,
            'fecha': sesion.fecha.strftime('%d/%m/%Y'),
            'horario': sesion.label,
            'lugar': sesion.lugar,
        }
    })


@require_POST
def session_register_new(request, id):
    """Register a new participant for a session."""
    sesion = get_object_or_404(SesionAsistencia, id=id, activa=True)

    cedula = request.POST.get('cedula', '').strip().upper()
    nombres = request.POST.get('nombres', '').strip().upper()
    apellidos = request.POST.get('apellidos', '').strip().upper()
    email = request.POST.get('email', '').strip().lower()
    celular = request.POST.get('celular', '').strip()

    if not nombres or not apellidos:
        return JsonResponse({'ok': False, 'error': 'Nombres y apellidos son obligatorios.'}, status=400)
    if not cedula and not email:
        return JsonResponse({'ok': False, 'error': 'Debe proporcionar al menos cédula o correo.'}, status=400)

    # Check for existing participant (deduplication)
    participante = None
    if cedula:
        participante = Participante.objects.filter(cedula=cedula).first()
    if not participante and email:
        participante = Participante.objects.filter(email__iexact=email).first()

    # Check líder restriction
    if sesion.solo_lideres:
        if participante and not participante.es_lider:
            return JsonResponse({
                'ok': False,
                'error': 'Este evento es exclusivo para Líderes Académicos. Si crees que es un error, contacta al administrador.'
            }, status=403)
        if not participante:
            return JsonResponse({
                'ok': False,
                'error': 'Este evento es exclusivo para Líderes Académicos. No se encontró tu registro como líder.'
            }, status=403)

    if participante:
        # Participant exists - update missing fields and confirm
        updated_fields = []
        if celular and not participante.celular:
            participante.celular = celular
            updated_fields.append('celular')
        if cedula and not participante.cedula:
            participante.cedula = cedula
            updated_fields.append('cedula')
        if email and not participante.email:
            participante.email = email
            updated_fields.append('email')
        if updated_fields:
            participante.save(update_fields=updated_fields)
    else:
        # Create new participant
        participante = Participante.objects.create(
            cedula=cedula,
            nombres=nombres,
            apellidos=apellidos,
            email=email,
            celular=celular,
        )

    # Check capacity
    if sesion.esta_llena:
        return JsonResponse({
            'ok': False,
            'error': 'Esta sesión ya alcanzó el cupo máximo.'
        }, status=409)

    # Create confirmation
    conf, created = ConfirmacionAsistencia.objects.get_or_create(
        participante=participante,
        sesion=sesion,
        defaults={'confirmado': True}
    )

    if not created:
        return JsonResponse({'ok': True, 'already': True, 'message': 'Ya estás registrado en esta sesión.'})

    return JsonResponse({
        'ok': True,
        'already': False,
        'message': f'Registro exitoso para {participante.nombres} {participante.apellidos}.',
        'participante': {
            'id': participante.id,
            'nombres': participante.nombres,
            'apellidos': participante.apellidos,
        },
        'sesion': {
            'titulo': sesion.titulo or sesion.dia_semana,
            'fecha': sesion.fecha.strftime('%d/%m/%Y'),
            'horario': sesion.label,
            'lugar': sesion.lugar,
        }
    })


# ─── Certificate Verification (QR Page) ──────────────────────────

def verify_certificate(request, hash):
    """Public certificate verification page — linked from QR code on certificate."""
    certificado = Certificado.objects.filter(hash_verificacion=hash).select_related('lote').first()
    
    return render(request, 'public/verify_certificate.html', {
        'certificado': certificado,
        'hash': hash,
        'found': certificado is not None,
    })
