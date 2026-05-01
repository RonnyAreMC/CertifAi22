"""Views de cuenta pública (Participante).

Todo se sirve aquí con templates en `public/account/`. Las acciones que
mutan estado (registro, certificados, etc.) tienen forms server-rendered
para evitar la dependencia de JS al inicio.
"""
from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from core.models import (
    Certificado,
    ConfirmacionAsistencia,
    Participante,
    RegistroAsistencia,
    SesionAsistencia,
)
from public.services import auth as account_auth
from public.services import google_auth as gsignin
from core.services.email import sender as email_sender


# ════════════════════════════════════════════════════════════════
# Auth: login / register / logout
# ════════════════════════════════════════════════════════════════

@require_http_methods(['GET', 'POST'])
def login_view(request):
    if account_auth.get_current_participante(request):
        return redirect('public:account_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        next_url = request.POST.get('next') or request.GET.get('next') or 'public:account_dashboard'

        p = account_auth.authenticate(email, password)
        if not p:
            messages.error(request, 'Email o contraseña incorrectos.')
            return render(request, 'public/account/login.html', {'email': email, 'next': next_url})

        account_auth.login(request, p)
        email_sender.send_login_notification(p, method='Email y contraseña', request=request)
        messages.success(request, f'¡Hola de nuevo, {p.nombres}!')
        if next_url.startswith('/'):
            return redirect(next_url)
        return redirect(next_url)

    return render(request, 'public/account/login.html', {
        'next': request.GET.get('next', ''),
    })


@require_http_methods(['GET', 'POST'])
def register_view(request):
    if account_auth.get_current_participante(request):
        return redirect('public:account_dashboard')

    if request.method == 'POST':
        nombres = request.POST.get('nombres', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        email = request.POST.get('email', '').strip().lower()
        cedula = request.POST.get('cedula', '').strip()
        celular = request.POST.get('celular', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        ctx = {
            'form': {'nombres': nombres, 'apellidos': apellidos, 'email': email, 'cedula': cedula, 'celular': celular},
        }

        # Validaciones
        if not nombres or not apellidos:
            messages.error(request, 'Nombre y apellido son obligatorios.')
            return render(request, 'public/account/register.html', ctx)
        if not email:
            messages.error(request, 'El email es obligatorio.')
            return render(request, 'public/account/register.html', ctx)
        if password != password2:
            messages.error(request, 'Las contraseñas no coinciden.')
            return render(request, 'public/account/register.html', ctx)
        if len(password) < 6:
            messages.error(request, 'La contraseña debe tener al menos 6 caracteres.')
            return render(request, 'public/account/register.html', ctx)

        # ¿Ya existe participante con ese email?
        p = Participante.objects.filter(email__iexact=email).first()
        if p:
            if p.has_account:
                messages.error(request, 'Ya existe una cuenta con ese email. Iniciá sesión.')
                return redirect('public:account_login')
            # Existe como guest → upgrade a cuenta
            p.nombres = nombres or p.nombres
            p.apellidos = apellidos or p.apellidos
            if cedula and not p.cedula:
                p.cedula = cedula
            if celular and not p.celular:
                p.celular = celular
        else:
            p = Participante(
                nombres=nombres, apellidos=apellidos, email=email,
                cedula=cedula, celular=celular,
            )

        try:
            p.full_clean(exclude=['password_hash'])
        except Exception as e:
            messages.error(request, f'Datos inválidos: {e}')
            return render(request, 'public/account/register.html', ctx)

        p.set_password(password)
        p.save()
        account_auth.login(request, p)
        email_sender.send_welcome_email(p, request=request)
        messages.success(request, f'¡Bienvenido a CertifAI, {p.nombres}!')
        return redirect('public:account_dashboard')

    return render(request, 'public/account/register.html', {})


def logout_view(request):
    account_auth.logout(request)
    messages.success(request, 'Sesión cerrada.')
    return redirect('public:home')


# ════════════════════════════════════════════════════════════════
# Account Dashboard
# ════════════════════════════════════════════════════════════════

@account_auth.login_required
def dashboard(request):
    import calendar as cal
    from datetime import datetime, timedelta

    p: Participante = request.participante

    certificados = Certificado.objects.filter(
        Q(cedula=p.cedula) if p.cedula else Q(email__iexact=p.email)
    ).order_by('-fecha_curso')

    today = timezone.localdate()
    confirmadas = ConfirmacionAsistencia.objects.filter(participante=p)
    asistencias = RegistroAsistencia.objects.filter(participante=p)
    eventos_inscrito_ids = set(confirmadas.values_list('sesion_id', flat=True))
    eventos_asistido_ids = set(asistencias.values_list('sesion_id', flat=True))

    # Total horas certificadas (suma de horas de todos los certificados)
    total_horas = sum(c.horas or 0 for c in certificados)

    # ── Próximo evento (el más cercano donde está inscrito) ────────
    next_event = (SesionAsistencia.objects
        .filter(activa=True, id__in=eventos_inscrito_ids, fecha__gte=today)
        .order_by('fecha', 'hora_inicio')
        .first())
    next_event_dt_iso = None
    if next_event:
        ne_dt = datetime.combine(next_event.fecha, next_event.hora_inicio)
        next_event_dt_iso = ne_dt.isoformat()

    eventos_proximos = (SesionAsistencia.objects
        .filter(activa=True, id__in=eventos_inscrito_ids, fecha__gte=today)
        .prefetch_related('ponentes')
        .order_by('fecha', 'hora_inicio')[:3])

    # Recomendaciones — futuros activos sin inscripción
    eventos_recomendados = (SesionAsistencia.objects
        .filter(activa=True, fecha__gte=today)
        .exclude(id__in=eventos_inscrito_ids)
        .prefetch_related('ponentes')
        .order_by('fecha', 'hora_inicio')[:6])

    # ── Calendario del mes actual ───────────────────────────────────
    cal.setfirstweekday(cal.MONDAY)
    year, month = today.year, today.month
    month_matrix = cal.monthcalendar(year, month)  # lista de semanas con días (0 = vacío)

    # Eventos del mes (todos los activos para mostrarlos en el calendar) + status del user
    first_of_month = today.replace(day=1)
    last_day = cal.monthrange(year, month)[1]
    last_of_month = today.replace(day=last_day)

    sesiones_mes = SesionAsistencia.objects.filter(
        activa=True,
        fecha__gte=first_of_month,
        fecha__lte=last_of_month,
    ).order_by('fecha', 'hora_inicio')

    cal_days = {}  # day_int → {'inscrito': N, 'disponible': N, 'asisti': N}
    for s in sesiones_mes:
        d = s.fecha.day
        slot = cal_days.setdefault(d, {'inscrito': 0, 'disponible': 0, 'asisti': 0, 'eventos': []})
        slot['eventos'].append({
            'id': s.id,
            'titulo': s.titulo or s.dia_semana,
            'hora': s.hora_inicio.strftime('%H:%M'),
            'es_virtual': s.es_virtual,
        })
        if s.id in eventos_asistido_ids:
            slot['asisti'] += 1
        elif s.id in eventos_inscrito_ids:
            slot['inscrito'] += 1
        else:
            slot['disponible'] += 1

    # Build calendar weeks structure for the template
    cal_weeks = []
    for week in month_matrix:
        cal_week = []
        for day in week:
            if day == 0:
                cal_week.append({'day': None})
            else:
                info = cal_days.get(day, {})
                cal_week.append({
                    'day': day,
                    'is_today': (day == today.day),
                    'is_past': day < today.day,
                    'has_inscrito': info.get('inscrito', 0) > 0,
                    'has_asisti': info.get('asisti', 0) > 0,
                    'has_disponible': info.get('disponible', 0) > 0,
                    'eventos': info.get('eventos', []),
                })
        cal_weeks.append(cal_week)

    meses_es = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

    # ── Actividad reciente (últimos 5 eventos: certificados + inscripciones + asistencias) ──
    from datetime import date as _date_cls
    activity = []
    for c in certificados[:3]:
        if not c.fecha_curso:
            continue  # certificados sin fecha quedan fuera del feed
        activity.append({
            'tipo': 'certificado',
            'titulo': c.curso,
            'fecha': c.fecha_curso,
            'icono': 'fa-certificate',
            'color': 'success',
        })
    for s in eventos_proximos[:2]:
        if not s.fecha:
            continue
        activity.append({
            'tipo': 'inscrito',
            'titulo': s.titulo or s.dia_semana,
            'fecha': s.fecha,
            'icono': 'fa-bookmark',
            'color': 'brand',
        })
    activity.sort(key=lambda x: x['fecha'] or _date_cls.min, reverse=True)
    activity = activity[:5]

    # Día resaltado por deep-link desde correos: ?day=YYYY-MM-DD
    highlight_day = None
    day_param = request.GET.get('day', '').strip()
    if day_param:
        try:
            from datetime import date as _date
            parsed = _date.fromisoformat(day_param)
            if parsed.month == month and parsed.year == year:
                highlight_day = parsed.day
        except ValueError:
            pass

    return render(request, 'public/account/dashboard.html', {
        'p': p,
        'today': today,
        'certificados_count': certificados.count(),
        'total_horas': total_horas,
        'eventos_inscrito_count': len(eventos_inscrito_ids),
        'eventos_asistido_count': len(eventos_asistido_ids),
        'certificados_recientes': certificados[:3],
        'eventos_proximos': eventos_proximos,
        'eventos_recomendados': eventos_recomendados,
        # Calendar
        'cal_weeks': cal_weeks,
        'cal_year': year,
        'cal_month_name': meses_es[month - 1],
        'highlight_day': highlight_day,
        # Próximo evento + countdown
        'next_event': next_event,
        'next_event_dt_iso': next_event_dt_iso,
        # Actividad
        'activity': activity,
    })


# ════════════════════════════════════════════════════════════════
# Mis Certificados
# ════════════════════════════════════════════════════════════════

@account_auth.login_required
def certificados_view(request):
    p: Participante = request.participante
    q = request.GET.get('q', '').strip()

    qs = Certificado.objects.filter(
        Q(cedula=p.cedula) if p.cedula else Q(email__iexact=p.email)
    ).select_related('lote').order_by('-fecha_curso')

    if q:
        qs = qs.filter(Q(curso__icontains=q) | Q(lote__nombre_lote__icontains=q))

    return render(request, 'public/account/certificados.html', {
        'p': p,
        'certificados': qs,
        'total': qs.count(),
        'q': q,
    })


# ════════════════════════════════════════════════════════════════
# Mis Eventos (tabs: registrado · asistido · disponibles)
# ════════════════════════════════════════════════════════════════

@account_auth.login_required
def eventos_view(request):
    p: Participante = request.participante
    tab = request.GET.get('tab', 'mios')  # mios | disponibles
    today = timezone.localdate()

    confirmados_ids = set(ConfirmacionAsistencia.objects.filter(participante=p).values_list('sesion_id', flat=True))
    asistidos_ids = set(RegistroAsistencia.objects.filter(participante=p).values_list('sesion_id', flat=True))
    mis_ids = confirmados_ids | asistidos_ids

    if tab == 'disponibles':
        eventos = (SesionAsistencia.objects
            .filter(activa=True, fecha__gte=today)
            .exclude(id__in=mis_ids)
            .prefetch_related('ponentes')
            .order_by('fecha', 'hora_inicio'))
    else:
        eventos = (SesionAsistencia.objects
            .filter(id__in=mis_ids)
            .prefetch_related('ponentes')
            .order_by('-fecha', '-hora_inicio'))

    # Anotar estado de cada evento para el participante
    eventos_data = []
    for e in eventos:
        status = 'disponible'
        if e.id in asistidos_ids:
            status = 'asisti'
        elif e.id in confirmados_ids:
            if e.fecha < today:
                status = 'no_asisti'
            else:
                status = 'inscrito'
        eventos_data.append({'e': e, 'status': status})

    return render(request, 'public/account/eventos.html', {
        'p': p,
        'tab': tab,
        'eventos_data': eventos_data,
        'count_mios': len(mis_ids),
        'count_disponibles': SesionAsistencia.objects.filter(activa=True, fecha__gte=today).exclude(id__in=mis_ids).count(),
    })


@account_auth.login_required
def perfil_view(request):
    p: Participante = request.participante
    if request.method == 'POST':
        p.nombres = request.POST.get('nombres', p.nombres).strip()
        p.apellidos = request.POST.get('apellidos', p.apellidos).strip()
        cedula_in = request.POST.get('cedula', '').strip()
        if cedula_in and cedula_in != p.cedula:
            p.cedula = cedula_in
        p.celular = request.POST.get('celular', p.celular).strip()
        new_pwd = request.POST.get('new_password', '')
        if new_pwd:
            if len(new_pwd) < 6:
                messages.error(request, 'La nueva contraseña debe tener al menos 6 caracteres.')
                return render(request, 'public/account/perfil.html', {'p': p})
            p.set_password(new_pwd)
        if 'avatar' in request.FILES:
            p.avatar = request.FILES['avatar']
        try:
            p.full_clean(exclude=['password_hash'])
        except Exception as e:
            messages.error(request, f'Datos inválidos: {e}')
            return render(request, 'public/account/perfil.html', {'p': p})
        p.save()
        messages.success(request, 'Perfil actualizado.')
        return redirect('public:account_perfil')

    return render(request, 'public/account/perfil.html', {'p': p})


# ════════════════════════════════════════════════════════════════
# Acción: registrarse a un evento desde la cuenta (1 click)
# ════════════════════════════════════════════════════════════════

@account_auth.login_required
@require_POST
def evento_inscribir(request, sesion_id: int):
    p: Participante = request.participante
    try:
        sesion = SesionAsistencia.objects.get(pk=sesion_id, activa=True)
    except SesionAsistencia.DoesNotExist:
        raise Http404
    _, created = ConfirmacionAsistencia.objects.get_or_create(participante=p, sesion=sesion)
    if created:
        email_sender.send_event_inscription(p, sesion, request=request)
    messages.success(request, f'Te inscribiste a "{sesion.titulo or sesion.dia_semana}"')
    return redirect(request.META.get('HTTP_REFERER') or 'public:account_eventos')


# ════════════════════════════════════════════════════════════════
# Escanear QR desde la cuenta (web — usa cámara del navegador)
# ════════════════════════════════════════════════════════════════

@account_auth.login_required
def escanear_view(request):
    """Pantalla con la cámara del navegador para escanear el QR de un evento."""
    return render(request, 'public/account/escanear.html')


@account_auth.login_required
@require_POST
def escanear_registrar(request):
    """Recibe el codigo_qr (de un POST JSON o form) y registra asistencia.

    Idempotente: si ya estaba registrado, devuelve `already_registered=True`.
    Si nunca se inscribió, lo inscribe automáticamente al escanear.
    """
    import json
    p: Participante = request.participante

    # Aceptar tanto JSON como form
    codigo_qr = ''
    if request.content_type and 'json' in request.content_type:
        try:
            data = json.loads(request.body or b'{}')
            codigo_qr = (data.get('codigo_qr') or '').strip()
        except Exception:
            return JsonResponse({'ok': False, 'error': 'Body inválido.'}, status=400)
    else:
        codigo_qr = (request.POST.get('codigo_qr') or '').strip()

    if not codigo_qr:
        return JsonResponse({'ok': False, 'error': 'Falta el código QR.'}, status=400)

    # Si vino una URL completa, extraemos el último segmento
    if '/' in codigo_qr:
        parts = [s for s in codigo_qr.rstrip('/').split('/') if s]
        if parts:
            codigo_qr = parts[-1]

    try:
        sesion = SesionAsistencia.objects.get(codigo_qr=codigo_qr, activa=True)
    except SesionAsistencia.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'QR inválido o sesión no activa.'}, status=404)

    # Inscribir al vuelo si no estaba inscrito
    ConfirmacionAsistencia.objects.get_or_create(participante=p, sesion=sesion)

    # Registrar asistencia (unique constraint asegura idempotencia)
    ip = (
        request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
        or request.META.get('REMOTE_ADDR')
    )
    _, created = RegistroAsistencia.objects.get_or_create(
        participante=p, sesion=sesion,
        defaults={'ip_address': ip},
    )
    return JsonResponse({
        'ok': True,
        'created': created,
        'already_registered': not created,
        'sesion_titulo': sesion.titulo or sesion.dia_semana,
        'sesion_fecha':  sesion.fecha.strftime('%Y-%m-%d'),
        'sesion_hora':   sesion.hora_inicio.strftime('%H:%M'),
    })


# ════════════════════════════════════════════════════════════════
# Landing pública (rediseñada) — datos para el carousel/swiper
# ════════════════════════════════════════════════════════════════

def home(request):
    today = timezone.localdate()
    eventos = (SesionAsistencia.objects
        .filter(activa=True, fecha__gte=today)
        .order_by('fecha', 'hora_inicio'))

    # 5 destacados para el hero (los más próximos)
    eventos_hero = list(eventos[:5])
    # 9 para el grid
    eventos_grid = list(eventos[:9])

    return render(request, 'public/home.html', {
        'eventos_hero': eventos_hero,
        'eventos_grid': eventos_grid,
        'total_eventos': eventos.count(),
    })


# ════════════════════════════════════════════════════════════════
# Google Sign-In (login con cuenta Google)
# ════════════════════════════════════════════════════════════════

def google_signin_start(request):
    """Inicia el flujo OAuth — redirige a la pantalla de consent de Google."""
    if not getattr(settings, 'GOOGLE_CLIENT_ID', None):
        messages.error(request, 'Google Sign-In no está configurado.')
        return redirect('public:account_login')

    redirect_uri = request.build_absolute_uri('/cuenta/google/callback/')
    flow = gsignin.build_signin_flow(redirect_uri)
    auth_url, state = flow.authorization_url(
        access_type='online',
        include_granted_scopes='true',
        prompt='select_account',
    )
    request.session['gsignin_state'] = state
    # PKCE: guardar code_verifier — el callback necesita restaurarlo
    request.session['gsignin_code_verifier'] = flow.code_verifier
    request.session['gsignin_next'] = request.GET.get('next', '')
    return redirect(auth_url)


def google_signin_callback(request):
    """Recibe el code de Google, valida el id_token y loguea/crea participante."""
    error = request.GET.get('error')
    if error:
        messages.error(request, f'Google rechazó la autorización: {error}')
        return redirect('public:account_login')

    state = request.session.pop('gsignin_state', None)
    code_verifier = request.session.pop('gsignin_code_verifier', None)
    next_url = request.session.pop('gsignin_next', '')
    code = request.GET.get('code')
    if not code:
        messages.error(request, 'Google no devolvió código de autorización.')
        return redirect('public:account_login')

    redirect_uri = request.build_absolute_uri('/cuenta/google/callback/')

    try:
        flow = gsignin.build_signin_flow(redirect_uri, state=state)
        if code_verifier:
            flow.code_verifier = code_verifier  # restaurar PKCE verifier
        flow.fetch_token(code=code)
        creds = flow.credentials
        info = gsignin.fetch_userinfo_from_idtoken(creds.id_token)
    except Exception as exc:
        messages.error(request, f'Error procesando inicio con Google: {exc}')
        return redirect('public:account_login')

    email = (info.get('email') or '').strip().lower()
    if not email:
        messages.error(request, 'Google no devolvió email.')
        return redirect('public:account_login')

    # Buscar o crear el participante por email
    p = Participante.objects.filter(email__iexact=email).first()
    if not p:
        p = Participante(
            email=email,
            nombres=info.get('given_name') or email.split('@')[0],
            apellidos=info.get('family_name') or '',
        )
        p.save()
        created = True
    else:
        if not p.nombres and info.get('given_name'):
            p.nombres = info['given_name']
        if not p.apellidos and info.get('family_name'):
            p.apellidos = info['family_name']
        p.save()
        created = False

    account_auth.login(request, p)
    if created:
        email_sender.send_welcome_email(p, request=request)
    else:
        email_sender.send_login_notification(p, method='Google', request=request)

    messages.success(
        request,
        f'¡Hola {p.nombres}! ' + ('Tu cuenta fue creada con Google.' if created else 'Iniciaste sesión con Google.')
    )

    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('public:account_dashboard')
