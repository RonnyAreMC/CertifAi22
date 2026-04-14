from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib import messages
from django.http import FileResponse, HttpResponse, JsonResponse
from django.db import models as db_models
from django.db.models import Sum, Count, F, Max, Q as models_Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, datetime, date, time
from django.views.decorators.http import require_http_methods, require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.views import LoginView as DjangoLoginView

from core.models import (
    LoteCertificados, Certificado, Auditoria,
    SesionAsistencia, RegistroAsistencia, ConfirmacionAsistencia,
    Usuario, SolicitudAcceso, Participante, LandingBloque, FirmaInstitucional
)
from core.services.pdf_service import generate_certificate_pdf
from core.services.excel_service import process_excel_batch, analyze_headers, analyze_excel_file
from .forms import BatchForm, SolicitudAccesoForm, SesionForm

import base64
import uuid
import random
import json
from io import BytesIO


# ---------------------------------------------------------------------------
# Custom Login View
# ---------------------------------------------------------------------------

class CustomLoginView(DjangoLoginView):
    """Custom login view that checks for pending access requests"""
    template_name = 'panel/auth/login.html'
    redirect_authenticated_user = False  # We handle redirect manually
    
    def get(self, request, *args, **kwargs):
        # If user is already authenticated, route them properly
        if request.user.is_authenticated:
            return self._route_authenticated_user(request.user)
        return super().get(request, *args, **kwargs)
    
    def _route_authenticated_user(self, user):
        """Route an authenticated user to the correct page based on their status."""
        # Check if user has pending access request
        try:
            SolicitudAcceso.objects.get(usuario_creado=user, estado='pendiente')
            return redirect('panel:mi_estado')
        except SolicitudAcceso.DoesNotExist:
            pass
        
        # Check if user is active admin
        if user.activo and user.rol in ['admin', 'superadmin']:
            return redirect('panel:dashboard')
        
        # Inactive user - send to mi_estado
        return redirect('panel:mi_estado')
    
    def form_valid(self, form):
        from django.contrib.auth import login
        user = form.get_user()

        # Always log the user in first
        login(self.request, user, backend='admin_panel.backends.EmailBackend')

        # Route them to the correct page
        return self._route_authenticated_user(user)

    def form_invalid(self, form):
        # Limpiamos los errores genéricos del form y mostramos un mensaje custom
        form.errors.clear()
        if not any(m.level_tag == 'error' for m in messages.get_messages(self.request)):
            messages.error(
                self.request,
                "Has ingresado mal tu usuario o contraseña. Inténtalo de nuevo."
            )
        return super().form_invalid(form)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_admin(user):
    """Check if user has admin privileges."""
    return user.is_authenticated and user.rol in ['admin', 'superadmin']


def _is_superadmin(user):
    """Solo superadmin (para configuración global)."""
    return user.is_authenticated and user.rol == 'superadmin'


def _log_audit(user, action, detail):
    """Create an audit log entry."""
    if user:  # Solo crear log si el usuario no es None
        Auditoria.objects.create(usuario=user, accion=action, detalle=detail)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(_is_admin)
def dashboard(request):
    """Admin dashboard with metrics and charts."""
    total_certificados = Certificado.objects.count()
    total_descargas = Certificado.objects.aggregate(
        total=Sum('descargas_count'))['total'] or 0
    total_busquedas = Certificado.objects.aggregate(
        total=Sum('veces_buscado'))['total'] or 0

    lotes = LoteCertificados.objects.all().order_by('-fecha_creacion')[:5]
    auditoria = Auditoria.objects.all()[:10]

    # Chart: Distribution by Faculty
    stats_facultad = (
        Certificado.objects.values('lote__facultad')
        .annotate(total=Count('id'))
        .order_by('-total')
    )
    labels_facultad = [item['lote__facultad'] for item in stats_facultad]
    data_facultad = [item['total'] for item in stats_facultad]

    # Chart: Top 5 Batches by Downloads
    top_lotes = (
        Certificado.objects.values('lote__nombre_lote')
        .annotate(downloads=Sum('descargas_count'))
        .order_by('-downloads')[:5]
    )
    labels_top_lotes = [item['lote__nombre_lote'] for item in top_lotes]
    data_top_lotes = [item['downloads'] for item in top_lotes]

    # Chart: Certificates Issued Last 14 Days
    last_14_days = timezone.now().date() - timedelta(days=14)
    stats_daily = (
        Certificado.objects.filter(created_at__gte=last_14_days)
        .annotate(date=TruncDate('created_at'))
        .values('date')
        .annotate(count=Count('id'))
        .order_by('date')
    )
    labels_daily = [item['date'].strftime('%d/%m') for item in stats_daily]
    data_daily = [item['count'] for item in stats_daily]

    context = {
        'total_certificados': total_certificados,
        'total_descargas': total_descargas,
        'total_busquedas': total_busquedas,
        'recent_lotes': lotes,
        'auditoria': auditoria,
        'labels_facultad': labels_facultad,
        'data_facultad': data_facultad,
        'labels_top_lotes': labels_top_lotes,
        'data_top_lotes': data_top_lotes,
        'labels_daily': labels_daily,
        'data_daily': data_daily,
    }
    return render(request, 'panel/dashboard/index.html', context)


# ---------------------------------------------------------------------------
# Batch CRUD
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(_is_admin)
def list_batches(request):
    """List all certificate batches."""
    lotes = LoteCertificados.objects.all().order_by('id')
    return render(request, 'panel/batch/list.html', {'lotes': lotes})


@login_required
@user_passes_test(_is_admin)
def create_batch(request):
    """Create a new batch and process its Excel file."""
    if request.method == 'POST':
        form = BatchForm(request.POST, request.FILES)
        if form.is_valid():
            from django.db import transaction
            with transaction.atomic():
                lote = form.save(commit=False)
                lote.administrador = request.user
                lote.save()
            _log_audit(request.user, 'CREAR_LOTE', f'Lote creado: {lote.nombre_lote}')

            # Redirect to mapping page instead of immediate processing
            messages.info(request, "Lote creado. Por favor confirma las columnas del Excel.")
            return redirect('panel:batch_process_mapping', id=lote.id)
    else:
        form = BatchForm()
    return render(request, 'panel/batch/form.html', {'form': form})


@login_required
@user_passes_test(_is_admin)
def process_batch_mapping(request, id):
    """Analyze Excel headers and allow user to map them to system fields."""
    lote = get_object_or_404(LoteCertificados, id=id)

    # 1. POST: Process with mapping
    if request.method == 'POST':
        name_strategy = request.POST.get('name_strategy', 'single')
        
        col_nombres = None
        col_apellidos = None
        
        if name_strategy == 'split':
            col_nombres = request.POST.get('col_nombres_split')
            col_apellidos = request.POST.get('col_apellidos')
        else:
            col_nombres = request.POST.get('col_nombres')
            
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
                    lote.archivo_excel.delete(save=True) # Cleanup
                return redirect('panel:batch_list')
            else:
                 messages.error(request, f'Error al procesar: {msg}')
        except Exception as e:
             messages.error(request, f'Error crítico: {str(e)}')
        
        # If error, stay on same page (get logic will re-run) or redirect
        return redirect('panel:batch_process_mapping', id=lote.id)

    # 2. GET: Analyze and show form
    analysis = analyze_headers(lote.id)
    
    if not analysis['success']:
        messages.error(request, f"Error leyendo el archivo Excel: {analysis.get('error')}")
        return redirect('panel:batch_list')

    return render(request, 'panel/batch/mapping.html', {
        'lotes': lote, # using 'lotes' to match template variable if any
        'columns': analysis['columns'],
        'suggestions': analysis['suggestions'],
        'preview': analysis['preview'],
    })


@login_required
@user_passes_test(_is_admin)
def batch_detail(request, id):
    """View batch details and its certificates."""
    lote = get_object_or_404(LoteCertificados, id=id)
    certificados = lote.certificados.all()
    return render(request, 'panel/batch/detail.html', {
        'lote': lote,
        'certificados': certificados,
    })


@login_required
@user_passes_test(_is_admin)
def configure_batch(request, id):
    """
    Configurar diseño específico de un lote.
    Por defecto un lote usa el Diseño Global; aquí el admin puede activar
    'personalizar_diseno' y editar los campos solo para este lote.
    """
    lote = get_object_or_404(LoteCertificados, id=id)

    if request.method == 'POST':
        lote.personalizar_diseno = request.POST.get('personalizar_diseno') == 'on'
        lote.cuerpo_certificado = request.POST.get('cuerpo_certificado') or lote.cuerpo_certificado

        plantilla = request.POST.get('plantilla')
        if plantilla:
            lote.plantilla = plantilla

        for color_field in ('color_primario', 'color_secundario', 'color_terciario', 'color_texto'):
            val = request.POST.get(color_field)
            if val:
                setattr(lote, color_field, val)

        # Firmas institucionales (1, 2, 3)
        for i in range(1, 4):
            firma_id = request.POST.get(f'firma_inst_{i}')
            if firma_id:
                setattr(lote, f'firma_inst_{i}_id', int(firma_id))
            else:
                setattr(lote, f'firma_inst_{i}', None)

        # Firma personalizada (4)
        lote.firma_inst_4 = None
        nombre = request.POST.get('nombre_firma_4')
        cargo = request.POST.get('cargo_firma_4')
        if nombre is not None:
            lote.nombre_firma_4 = nombre
        if cargo is not None:
            lote.cargo_firma_4 = cargo
        if 'imagen_firma_4' in request.FILES:
            file_obj = request.FILES['imagen_firma_4']
            encoded = base64.b64encode(file_obj.read()).decode('utf-8')
            lote.imagen_firma_4 = encoded

        if 'logo_header_1' in request.FILES:
            lote.logo_header_1 = request.FILES['logo_header_1']
        if 'logo_header_2' in request.FILES:
            lote.logo_header_2 = request.FILES['logo_header_2']
        if 'logo_header_3' in request.FILES:
            lote.logo_header_3 = request.FILES['logo_header_3']

        lote.save()
        if lote.personalizar_diseno:
            messages.success(request, 'Diseño personalizado guardado para este lote.')
        else:
            messages.success(request, 'Lote actualizado. Está usando el Diseño Global.')
        return redirect('panel:batch_configure', id=lote.id)

    firmas_institucionales = FirmaInstitucional.objects.filter(activa=True).order_by('nombre')
    return render(request, 'panel/batch/config.html', {
        'lote': lote,
        'firmas_institucionales': firmas_institucionales,
    })


@login_required
@user_passes_test(_is_superadmin)
def design_global(request):
    """
    Configuración GLOBAL del diseño de certificados.
    Solo el superadmin puede modificarla. Aplica a todos los lotes.
    """
    from core.models import DisenoGlobal
    diseno = DisenoGlobal.get_solo()

    if request.method == 'POST':
        cuerpo = request.POST.get('cuerpo_certificado')
        if cuerpo is not None:
            diseno.cuerpo_certificado = cuerpo

        plantilla = request.POST.get('plantilla')
        if plantilla:
            diseno.plantilla = plantilla

        for color_field in ('color_primario', 'color_secundario', 'color_terciario', 'color_texto'):
            val = request.POST.get(color_field)
            if val:
                setattr(diseno, color_field, val)

        # Firmas institucionales 1, 2, 3
        for i in range(1, 4):
            firma_id = request.POST.get(f'firma_inst_{i}')
            if firma_id:
                setattr(diseno, f'firma_inst_{i}_id', int(firma_id))
            else:
                setattr(diseno, f'firma_inst_{i}', None)

        # Firma personalizada (4)
        nombre = request.POST.get('nombre_firma_4')
        cargo = request.POST.get('cargo_firma_4')
        if nombre is not None:
            diseno.nombre_firma_4 = nombre
        if cargo is not None:
            diseno.cargo_firma_4 = cargo
        if 'imagen_firma_4' in request.FILES:
            file_obj = request.FILES['imagen_firma_4']
            encoded = base64.b64encode(file_obj.read()).decode('utf-8')
            diseno.imagen_firma_4 = encoded

        if 'logo_header_1' in request.FILES:
            diseno.logo_header_1 = request.FILES['logo_header_1']
        if 'logo_header_2' in request.FILES:
            diseno.logo_header_2 = request.FILES['logo_header_2']
        if 'logo_header_3' in request.FILES:
            diseno.logo_header_3 = request.FILES['logo_header_3']

        # Posición de firmas
        posicion = request.POST.get('posicion_firmas')
        if posicion:
            try:
                diseno.posicion_firmas = float(posicion)
            except (ValueError, TypeError):
                pass

        diseno.save()
        _log_audit(request.user, 'EDITAR_DISENO_GLOBAL', 'Diseño global actualizado')
        messages.success(request, 'Diseño global guardado. Aplica a todos los certificados.')
        return redirect('panel:design_global')

    firmas_institucionales = FirmaInstitucional.objects.filter(activa=True).order_by('nombre')
    
    # Build signature preview data for visual editor
    firma_preview = []
    for i in range(1, 4):
        firma = getattr(diseno, f'firma_inst_{i}')
        if firma:
            firma_preview.append({
                'slot': i,
                'name': firma.nombre or '',
                'cargo': firma.cargo or '',
                'has_img': bool(firma.imagen),
                'offset_y': getattr(diseno, f'firma_{i}_offset_y', 0),
                'escala': getattr(diseno, f'firma_{i}_escala', 100),
            })
    # Firma 4 (custom)
    if diseno.nombre_firma_4:
        firma_preview.append({
            'slot': 4,
            'name': diseno.nombre_firma_4,
            'cargo': diseno.cargo_firma_4 or '',
            'has_img': bool(diseno.imagen_firma_4),
            'offset_y': getattr(diseno, 'firma_4_offset_y', 0),
            'escala': getattr(diseno, 'firma_4_escala', 100),
        })
    
    import json as json_mod
    return render(request, 'panel/design/config.html', {
        'diseno': diseno,
        'firmas_institucionales': firmas_institucionales,
        'firma_preview_json': json_mod.dumps(firma_preview),
    })


@login_required
@user_passes_test(_is_superadmin)
@require_POST
def design_save_firma_pos(request):
    """AJAX: Save per-signature position/scale from the visual editor."""
    from core.models import DisenoGlobal
    import json as json_mod
    
    try:
        data = json_mod.loads(request.body)
    except (json_mod.JSONDecodeError, AttributeError):
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)
    
    diseno = DisenoGlobal.get_solo()
    
    for item in data.get('firmas', []):
        slot = item.get('slot')
        if slot not in (1, 2, 3, 4):
            continue
        offset_y = item.get('offset_y', 0)
        escala = item.get('escala', 100)
        setattr(diseno, f'firma_{slot}_offset_y', float(offset_y))
        setattr(diseno, f'firma_{slot}_escala', float(escala))
    
    # Also save global posicion_firmas if provided
    if 'posicion_firmas' in data:
        diseno.posicion_firmas = float(data['posicion_firmas'])
    
    diseno.save()
    return JsonResponse({'ok': True})

@login_required
@user_passes_test(_is_superadmin)
@xframe_options_exempt
def design_global_preview(request):
    """Preview del diseño global con datos dummy."""
    # Buscar cualquier lote para asociar el dummy_cert (necesario por FK)
    lote = LoteCertificados.objects.first()
    if not lote:
        # Crear un lote temporal en memoria (no se persiste)
        return HttpResponse("Crea primero un lote para previsualizar el diseño.", status=400)

    dummy_cert = Certificado(
        lote=lote,
        cedula="0999999999",
        nombres="ESTUDIANTE",
        apellidos="DE PRUEBA",
        email="prueba@unemi.edu.ec",
        curso="CURSO DE DEMOSTRACIÓN",
        fecha_curso=date.today(),
        horas=40,
        hash_verificacion=uuid.uuid4(),
    )
    dummy_cert.id = random.randint(10000, 99999)

    try:
        pdf_buffer = generate_certificate_pdf(dummy_cert)
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'inline; filename="DesignPreview.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Error generando preview: {str(e)}", status=500)


@login_required
@user_passes_test(_is_admin)
def delete_batch(request, id):
    """Delete a batch and all its certificates."""
    lote = get_object_or_404(LoteCertificados, id=id)

    if request.method == 'POST':
        nombre = lote.nombre_lote
        lote.delete()
        _log_audit(request.user, 'ELIMINAR_LOTE', f'Lote eliminado: {nombre}')
        messages.success(request, f'El lote "{nombre}" y sus certificados han sido eliminados.')
        return redirect('panel:batch_list')

    return redirect('panel:batch_detail', id=id)


@login_required
@user_passes_test(_is_admin)
@xframe_options_exempt
def preview_pdf(request, id):
    """Preview a certificate PDF with dummy data."""
    lote = get_object_or_404(LoteCertificados, id=id)

    dummy_cert = Certificado(
        lote=lote,
        cedula="0999999999",
        nombres="ESTUDIANTE",
        apellidos="DE PRUEBA",
        email="prueba@unemi.edu.ec",
        curso="CURSO DE DEMOSTRACIÓN",
        fecha_curso=date.today(),
        horas=40,
        hash_verificacion=uuid.uuid4(),
    )
    dummy_cert.id = random.randint(10000, 99999)

    try:
        pdf_buffer = generate_certificate_pdf(dummy_cert)
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="Preview_{lote.id}.pdf"'
        return response
    except Exception as e:
        return HttpResponse(f"Error generando preview: {str(e)}", status=500)


# ---------------------------------------------------------------------------
# Certificate Management
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(_is_admin)
def add_certificate(request, id):
    """Manually add a certificate to a batch."""
    lote = get_object_or_404(LoteCertificados, id=id)

    if request.method == 'POST':
        try:
            fecha_str = request.POST.get('fecha_curso')
            fecha_curso = (
                datetime.strptime(fecha_str, '%Y-%m-%d').date() if fecha_str else None
            )

            cedula_raw = (request.POST.get('cedula') or '').strip()
            nombres_raw = (request.POST.get('nombres') or '').strip().upper()
            apellidos_raw = (request.POST.get('apellidos') or '').strip().upper()
            email_raw = (request.POST.get('email') or '').strip().lower()
            celular_raw = (request.POST.get('celular') or '').strip()

            # Deduplication: find or create Participante
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
                    cedula=real_cedula,
                    nombres=nombres_raw,
                    apellidos=apellidos_raw,
                    email=email_raw,
                    celular=celular_raw,
                )

            Certificado.objects.create(
                lote=lote,
                participante=participante,
                cedula=cedula_raw or f'GEN-{uuid.uuid4().hex[:8].upper()}',
                nombres=nombres_raw,
                apellidos=apellidos_raw,
                email=email_raw,
                curso=request.POST.get('curso'),
                horas=int(request.POST.get('horas', 0)),
                fecha_curso=fecha_curso,
            )
            _log_audit(
                request.user,
                'AGREGAR_CERTIFICADO',
                f'Certificado agregado manual: {request.POST.get("cedula")} en lote {lote.nombre_lote}',
            )
            messages.success(request, 'Certificado agregado correctamente.')
        except Exception as e:
            messages.error(request, f'Error al agregar certificado: {str(e)}')

        return redirect('panel:batch_detail', id=lote.id)

    return redirect('panel:batch_detail', id=lote.id)


# ---------------------------------------------------------------------------
# Session Management (QR Attendance)
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(_is_admin)
def session_list(request):
    """List all attendance sessions with status and QR links."""
    fecha_filter = request.GET.get('fecha', '')
    estado_filter = request.GET.get('estado', '')

    sesiones = SesionAsistencia.objects.select_related('lote').annotate(
        total_confirmados=Count('confirmaciones'),
        total_asistentes=Count('registros'),
    )

    if fecha_filter:
        sesiones = sesiones.filter(fecha=fecha_filter)
        
    if estado_filter == 'llenas':
        sesiones = sesiones.filter(total_confirmados__gte=F('capacidad'))
    elif estado_filter == 'con_registro':
        sesiones = sesiones.filter(total_asistentes__gt=0)
    elif estado_filter == 'sin_registro':
        sesiones = sesiones.filter(total_asistentes=0)

    sesiones = sesiones.order_by('-fecha', '-hora_inicio')

    lotes = LoteCertificados.objects.filter(activo=True).order_by('nombre_lote')

    # Get distinct dates that have at least one session
    fechas_disponibles = SesionAsistencia.objects.dates('fecha', 'day', order='DESC')

    return render(request, 'panel/sessions/list.html', {
        'sesiones': sesiones,
        'lotes': lotes,
        'fechas_disponibles': fechas_disponibles,
        'fecha_filter': fecha_filter,
        'estado_filter': estado_filter,
    })


@login_required
@user_passes_test(_is_admin)
def session_create(request):
    """Create a new attendance session."""
    if request.method == 'POST':
        form = SesionForm(request.POST)
        if form.is_valid():
            sesion = form.save()
            _log_audit(request.user, 'CREAR_SESION',
                       f'Sesión creada: {sesion.titulo or sesion.dia_semana} {sesion.fecha}')
            messages.success(request, 'Sesión creada exitosamente.')
        else:
            for error in form.errors.values():
                messages.error(request, error.as_text())
        return redirect('panel:session_list')
    return redirect('panel:session_list')


@login_required
@user_passes_test(_is_admin)
def session_edit(request, id):
    """Edit an existing attendance session."""
    sesion = get_object_or_404(SesionAsistencia, id=id)
    if request.method == 'POST':
        form = SesionForm(request.POST, instance=sesion)
        if form.is_valid():
            form.save()
            _log_audit(request.user, 'EDITAR_SESION', f'Sesión editada: {sesion.id}')
            messages.success(request, 'Sesión actualizada correctamente.')
            return redirect('panel:session_list')
    else:
        form = SesionForm(instance=sesion)
    return render(request, 'panel/sessions/edit.html', {'form': form, 'sesion': sesion})


@login_required
@user_passes_test(_is_admin)
def session_generate_batch(request, id):
    """Generate a LoteCertificados from session's confirmed participants."""
    sesion = get_object_or_404(SesionAsistencia, id=id)

    if sesion.lote:
        messages.warning(request, 'Esta sesión ya tiene un lote de certificados asociado.')
        return redirect('panel:batch_configure', id=sesion.lote.id)

    confirmaciones = ConfirmacionAsistencia.objects.filter(
        sesion=sesion, confirmado=True, participante__isnull=False
    ).select_related('participante')

    if not confirmaciones.exists():
        messages.error(request, 'No hay participantes confirmados para generar certificados.')
        return redirect('panel:session_list')

    if request.method == 'POST':
        from django.db import transaction
        with transaction.atomic():
            # Re-fetch with lock to prevent race condition (double-click creates 2 batches)
            sesion = SesionAsistencia.objects.select_for_update().get(id=id)
            if sesion.lote:
                messages.warning(request, 'Esta sesión ya tiene un lote de certificados asociado.')
                return redirect('panel:batch_configure', id=sesion.lote.id)

            # Create batch
            lote = LoteCertificados.objects.create(
                nombre_lote=sesion.titulo or f'Sesión {sesion.fecha} {sesion.label}',
                administrador=request.user,
                facultad=request.POST.get('facultad', 'FACI'),
            )
            # Auto-asignar firmas institucionales por defecto
            firmas_default = list(FirmaInstitucional.objects.filter(activa=True).order_by('orden')[:3])
            if len(firmas_default) >= 1:
                lote.firma_inst_1 = firmas_default[0]
            if len(firmas_default) >= 2:
                lote.firma_inst_2 = firmas_default[1]
            if len(firmas_default) >= 3:
                lote.firma_inst_3 = firmas_default[2]

            # Precargar logos de cabecera por defecto
            import os
            from django.conf import settings as django_settings
            from django.core.files import File
            default_logos = [
                ('logo_header_1', 'muc.png'),
                ('logo_header_2', 'logo-unemi-removebg-preview.png'),
                ('logo_header_3', 'feue.png'),
            ]
            for field_name, filename in default_logos:
                img_path = os.path.join(django_settings.BASE_DIR, 'static', 'img', filename)
                if os.path.exists(img_path):
                    with open(img_path, 'rb') as f:
                        getattr(lote, field_name).save(filename, File(f), save=False)

            lote.save()

            # Create certificates from participants
            certs = []
            for conf in confirmaciones:
                p = conf.participante
                certs.append(Certificado(
                    lote=lote,
                    participante=p,
                    cedula=p.cedula or f'GEN-{uuid.uuid4().hex[:8].upper()}',
                    nombres=p.nombres,
                    apellidos=p.apellidos,
                    email=p.email,
                    celular=p.celular,
                    curso=lote.nombre_lote.upper(),
                ))
            Certificado.objects.bulk_create(certs)

            # Link session to batch
            sesion.lote = lote
            sesion.save(update_fields=['lote'])

        _log_audit(request.user, 'GENERAR_LOTE_SESION',
                   f'Lote "{lote.nombre_lote}" generado desde sesión {sesion.id} con {len(certs)} certificados')
        messages.success(request, f'Lote creado con {len(certs)} certificados. Ahora configura el diseño.')
        return redirect('panel:batch_configure', id=lote.id)

    return render(request, 'panel/sessions/generate_batch.html', {
        'sesion': sesion,
        'total_confirmados': confirmaciones.count(),
    })


@login_required
@user_passes_test(_is_admin)
def session_toggle(request, id):
    """Toggle session active/inactive."""
    sesion = get_object_or_404(SesionAsistencia, id=id)
    sesion.activa = not sesion.activa
    sesion.save(update_fields=['activa'])
    status = 'activada' if sesion.activa else 'desactivada'
    messages.success(request, f'Sesión {status}.')
    return redirect('panel:session_list')


@login_required
@user_passes_test(_is_admin)
def session_delete(request, id):
    """Delete a session if it has no attendees."""
    sesion = get_object_or_404(SesionAsistencia, id=id)
    if request.method == 'POST':
        if sesion.confirmaciones.exists() or sesion.registros.exists():
            messages.error(request, 'No puedes eliminar una sesión que ya tiene participantes registrados o confirmados.')
        else:
            sesion.delete()
            _log_audit(request.user, 'ELIMINAR_SESION', f'Sesión eliminada: {sesion.id}')
            messages.success(request, 'Sesión eliminada correctamente.')
    return redirect('panel:session_list')


@login_required
@user_passes_test(_is_admin)
def session_qr_display(request, id):
    """Full-screen QR display with real-time attendee feed."""
    sesion = get_object_or_404(SesionAsistencia, id=id)
    total_registros = RegistroAsistencia.objects.filter(sesion=sesion).count()

    # Build full URL for QR
    checkin_url = request.build_absolute_uri(f'/checkin/{sesion.codigo_qr}/')

    return render(request, 'panel/sessions/qr.html', {
        'sesion': sesion,
        'checkin_url': checkin_url,
        'total_registros': total_registros,
    })


@login_required
@user_passes_test(_is_admin)
def session_attendees_api(request, id):
    """JSON API: return latest attendees for polling (real-time feed)."""
    sesion = get_object_or_404(SesionAsistencia, id=id)
    
    # Get 'since' parameter for incremental updates
    since_str = request.GET.get('since', '')
    
    registros = RegistroAsistencia.objects.filter(sesion=sesion).select_related('participante', 'certificado')

    if since_str:
        try:
            since_dt = datetime.fromisoformat(since_str)
            registros = registros.filter(fecha_registro__gt=since_dt)
        except (ValueError, TypeError):
            pass

    registros = registros.order_by('-fecha_registro')[:50]

    total = RegistroAsistencia.objects.filter(sesion=sesion).count()

    attendees = []
    for r in registros:
        # Prefer participante, fallback to certificado
        p = r.participante
        c = r.certificado
        nombre = f'{p.nombres} {p.apellidos}' if p else (f'{c.nombres} {c.apellidos}' if c else '?')
        cedula = p.cedula if p else (c.cedula if c else '')
        email = p.email if p else (c.email if c else '')
        attendees.append({
            'id': r.id,
            'nombre': nombre,
            'cedula': cedula,
            'email': email,
            'hora': r.fecha_registro.strftime('%H:%M:%S'),
            'timestamp': r.fecha_registro.isoformat(),
        })
    
    return JsonResponse({
        'total': total,
        'attendees': attendees,
        'server_time': timezone.now().isoformat(),
    })


@login_required
@user_passes_test(_is_admin)
def session_bulk_pdf(request, id):
    """Generate a single PDF with all certificates for enrolled participants in a session."""
    sesion = get_object_or_404(SesionAsistencia, id=id)

    # Get all confirmed participants for this session
    confirmaciones = ConfirmacionAsistencia.objects.filter(
        sesion=sesion, confirmado=True
    ).select_related('certificado', 'certificado__lote')

    if not confirmaciones.exists():
        messages.warning(request, 'No hay participantes confirmados para esta sesión.')
        return redirect('panel:session_list')

    # Build one big PDF by merging individual certificate PDFs
    from PyPDF2 import PdfMerger

    merger = PdfMerger()
    count = 0

    for conf in confirmaciones:
        try:
            cert = conf.certificado
            pdf_buffer = generate_certificate_pdf(cert)
            merger.append(pdf_buffer)
            count += 1
        except Exception as e:
            # Skip problematic certificates, continue with the rest
            continue

    if count == 0:
        messages.error(request, 'No se pudo generar ningún certificado.')
        return redirect('panel:session_list')

    # Write merged PDF to response
    output_buffer = BytesIO()
    merger.write(output_buffer)
    merger.close()
    output_buffer.seek(0)

    safe_dia = sesion.dia_semana.replace('é', 'e').replace('á', 'a')
    filename = f"Certificados_{safe_dia}_{sesion.hora_inicio:%H%M}_{count}personas.pdf"

    response = HttpResponse(output_buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ---------------------------------------------------------------------------
# Register & Access Requests Management
# ---------------------------------------------------------------------------

@csrf_protect
@require_http_methods(["GET", "POST"])
def register(request):
    """Página de registro - solicitud de acceso con creación de usuario inactivo"""
    if request.user.is_authenticated:
        if request.user.activo and request.user.rol in ['admin', 'superadmin']:
            return redirect('panel:dashboard')
        return redirect('panel:mi_estado')
    
    if request.method == 'POST':
        form = SolicitudAccesoForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Verificar si el email ya existe
            if SolicitudAcceso.objects.filter(email=email).exists():
                messages.error(request, 'Este email ya tiene una solicitud registrada. Inicia sesión para ver el estado.')
            elif Usuario.objects.filter(email=email).exists():
                messages.error(request, 'Este email ya está registrado en el sistema.')
            else:
                # Crear usuario inactivo con la contraseña proporcionada
                nombre_usuario = email.split('@')[0]
                base_username = nombre_usuario
                counter = 1
                while Usuario.objects.filter(username=nombre_usuario).exists():
                    nombre_usuario = f"{base_username}{counter}"
                    counter += 1
                
                usuario = Usuario.objects.create_user(
                    username=nombre_usuario,
                    email=email,
                    password=password,
                    first_name=form.cleaned_data['nombres'],
                    last_name=form.cleaned_data['apellidos'],
                    telefono=form.cleaned_data.get('telefono', ''),
                    facultad=form.cleaned_data['facultad'],
                    rol='admin',
                    activo=False,  # Inactivo hasta que el admin apruebe
                    is_staff=False,
                    is_superuser=False,
                )
                
                # Crear la solicitud y vincular usuario
                solicitud = form.save(commit=False)
                solicitud.usuario_creado = usuario
                solicitud.save()
                
                _log_audit(None, 'SOLICITUD_ACCESO_CREADA', f'Nueva solicitud de acceso: {email}')
                
                # Iniciar sesión automáticamente y redirigir a mi_estado
                from django.contrib.auth import login
                login(request, usuario, backend='admin_panel.backends.EmailBackend')
                return redirect('panel:mi_estado')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f'{error}')
    else:
        form = SolicitudAccesoForm()
    
    return render(request, 'panel/auth/register.html', {'form': form})


def solicitud_pendiente(request, id):
    """Página de solicitud pendiente - redirige a mi_estado si está autenticado"""
    if request.user.is_authenticated:
        return redirect('panel:mi_estado')
    
    solicitud = get_object_or_404(SolicitudAcceso, id=id)
    
    # Si está aprobada, redirigir a login
    if solicitud.estado == 'aprobado':
        messages.success(request, 'Tu solicitud fue aprobada. Inicia sesión con tu correo y contraseña.')
        return redirect('panel:login')
    
    # Si está rechazada, mostrar motivo
    if solicitud.estado == 'rechazado':
        return render(request, 'panel/auth/solicitud_rechazada.html', {'solicitud': solicitud})
    
    # Si está pendiente, redirigir a login para que inicie sesión
    messages.info(request, 'Inicia sesión con tu correo y contraseña para ver el estado de tu solicitud.')
    return redirect('panel:login')


@login_required
def mi_estado(request):
    """Página de estado para usuarios pendientes de aprobación"""
    user = request.user
    
    # Si el usuario está activo y es admin, redirigir al dashboard
    if user.activo and user.rol in ['admin', 'superadmin']:
        return redirect('panel:dashboard')
    
    # Buscar la solicitud del usuario
    solicitud = None
    estado = 'pendiente'
    try:
        solicitud = SolicitudAcceso.objects.get(usuario_creado=user)
        estado = solicitud.estado
    except SolicitudAcceso.DoesNotExist:
        # Si no tiene solicitud pero no está activo, mostrar mensaje genérico
        if not user.activo:
            estado = 'desactivado'
    
    # Si la solicitud fue aprobada, verificar si el usuario está activo
    if estado == 'aprobado' and user.activo:
        return redirect('panel:dashboard')
    
    context = {
        'solicitud': solicitud,
        'estado': estado,
        'user': user,
    }
    return render(request, 'panel/auth/mi_estado.html', context)


@login_required
@user_passes_test(lambda user: user.rol == 'superadmin')
def solicitudes_pendientes(request):
    """Admin view: lista de solicitudes de acceso pendientes"""
    estado_filter = request.GET.get('estado', 'pendiente')
    
    solicitudes = SolicitudAcceso.objects.all().order_by('-fecha_solicitud')
    
    if estado_filter == 'pendiente':
        solicitudes = solicitudes.filter(estado='pendiente')
    elif estado_filter == 'aprobado':
        solicitudes = solicitudes.filter(estado='aprobado')
    elif estado_filter == 'rechazado':
        solicitudes = solicitudes.filter(estado='rechazado')
    
    pendientes_count = SolicitudAcceso.objects.filter(estado='pendiente').count()
    aprobadas_count = SolicitudAcceso.objects.filter(estado='aprobado').count()
    rechazadas_count = SolicitudAcceso.objects.filter(estado='rechazado').count()
    
    context = {
        'solicitudes': solicitudes,
        'estado_filter': estado_filter,
        'pendientes_count': pendientes_count,
        'aprobadas_count': aprobadas_count,
        'rechazadas_count': rechazadas_count,
    }
    return render(request, 'panel/solicitudes/pendientes.html', context)


@login_required
@user_passes_test(lambda user: user.rol == 'superadmin')
@require_http_methods(["POST"])
def aprobar_solicitud(request, id):
    """Admin action: aprobar una solicitud de acceso - activa el usuario existente"""
    solicitud = get_object_or_404(SolicitudAcceso, id=id)
    
    if solicitud.estado not in ['pendiente', 'rechazado']:
        messages.error(request, 'Esta solicitud no puede ser procesada.')
        return redirect('panel:solicitudes_pendientes')
    
    # Limpiar motivo de rechazo si existía
    if solicitud.estado == 'rechazado':
        solicitud.motivo_rechazo = ''
    
    try:
        if solicitud.usuario_creado:
            # Activar el usuario existente (creado durante el registro)
            usuario = solicitud.usuario_creado
            usuario.activo = True
            usuario.save(update_fields=['activo'])
            nombre_usuario = usuario.username
        else:
            # Solicitud legacy sin usuario vinculado - crear uno nuevo
            nombre_usuario = solicitud.email.split('@')[0]
            base_username = nombre_usuario
            counter = 1
            while Usuario.objects.filter(username=nombre_usuario).exists():
                nombre_usuario = f"{base_username}{counter}"
                counter += 1
            
            usuario = Usuario.objects.create_user(
                username=nombre_usuario,
                email=solicitud.email,
                first_name=solicitud.nombres,
                last_name=solicitud.apellidos,
                telefono=solicitud.telefono,
                facultad=solicitud.facultad,
                rol='admin',
                activo=True,
                is_staff=False,
                is_superuser=False,
            )
            solicitud.usuario_creado = usuario
        
        # Actualizar solicitud
        solicitud.estado = 'aprobado'
        solicitud.aprobado_por = request.user
        solicitud.fecha_respuesta = timezone.now()
        solicitud.save()
        
        # Log de auditoría
        _log_audit(request.user, 'SOLICITUD_APROBADA', 
                  f'Solicitud de {solicitud.email} aprobada. Usuario {nombre_usuario} activado.')
        
        messages.success(request, f'Solicitud aprobada. Usuario activado: {nombre_usuario}')
    except Exception as e:
        messages.error(request, f'Error al procesar la solicitud: {str(e)}')
    
    return redirect('panel:solicitudes_pendientes')


@login_required
@user_passes_test(lambda user: user.rol == 'superadmin')
@require_http_methods(["GET", "POST"])
def rechazar_solicitud(request, id):
    """Admin action: rechazar una solicitud de acceso"""
    solicitud = get_object_or_404(SolicitudAcceso, id=id)
    
    if solicitud.estado != 'pendiente':
        messages.error(request, 'Esta solicitud ya ha sido procesada.')
        return redirect('panel:solicitudes_pendientes')
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        solicitud.estado = 'rechazado'
        solicitud.motivo_rechazo = motivo
        solicitud.aprobado_por = request.user
        solicitud.fecha_respuesta = timezone.now()
        solicitud.save()
        
        _log_audit(request.user, 'SOLICITUD_RECHAZADA', 
                  f'Solicitud de {solicitud.email} rechazada. Motivo: {motivo}')
        
        messages.success(request, f'Solicitud rechazada: {solicitud.email}')
        return redirect('panel:solicitudes_pendientes')
    
    return render(request, 'panel/solicitudes/rechazar.html', {'solicitud': solicitud})


# ---------------------------------------------------------------------------
# Landing Page Builder (Superadmin Only)
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(lambda u: u.rol == 'superadmin')
def landing_builder(request):
    """Landing page builder — manage blocks visually."""
    bloques = LandingBloque.objects.all()
    # Only future events for the event selector
    eventos_futuros = SesionAsistencia.objects.filter(
        fecha__gte=date.today(), activa=True
    ).order_by('fecha', 'hora_inicio')

    return render(request, 'panel/landing/builder.html', {
        'bloques': bloques,
        'eventos_futuros': eventos_futuros,
        'tipo_choices': LandingBloque.TIPO_CHOICES,
        'estilo_choices': LandingBloque.ESTILO_CHOICES,
    })


@login_required
@user_passes_test(lambda u: u.rol == 'superadmin')
@require_http_methods(["POST"])
def landing_add_block(request):
    """AJAX: Add a new landing block."""
    tipo = request.POST.get('tipo', 'hero')
    estilo = request.POST.get('estilo', 'hero_gradient')

    # Assign next order
    max_orden = LandingBloque.objects.aggregate(m=Max('orden'))['m'] or 0

    bloque = LandingBloque.objects.create(
        tipo=tipo,
        estilo=estilo,
        orden=max_orden + 1,
        titulo=request.POST.get('titulo', ''),
    )

    return JsonResponse({'ok': True, 'id': bloque.id, 'orden': bloque.orden})


@login_required
@user_passes_test(lambda u: u.rol == 'superadmin')
@require_http_methods(["POST"])
def landing_update_block(request, id):
    """AJAX: Update a landing block."""
    bloque = get_object_or_404(LandingBloque, id=id)

    # Text fields
    for field in ['titulo', 'subtitulo', 'descripcion', 'tipo', 'estilo',
                  'color_fondo', 'color_texto', 'color_acento',
                  'boton_1_texto', 'boton_1_url', 'boton_1_icono',
                  'boton_2_texto', 'boton_2_url', 'boton_2_icono']:
        if field in request.POST:
            setattr(bloque, field, request.POST[field])

    # Activo toggle
    if 'activo' in request.POST:
        bloque.activo = request.POST['activo'] == 'true'

    # Evento vinculado
    sesion_id = request.POST.get('sesion_id')
    if sesion_id:
        try:
            bloque.sesion = SesionAsistencia.objects.get(id=sesion_id)
        except SesionAsistencia.DoesNotExist:
            bloque.sesion = None
    elif 'sesion_id' in request.POST:
        bloque.sesion = None

    # Items JSON
    items_raw = request.POST.get('items_json')
    if items_raw:
        try:
            bloque.items_json = json.loads(items_raw)
        except (json.JSONDecodeError, TypeError):
            pass

    # Images
    for img_field in ['imagen_principal', 'imagen_2', 'imagen_3']:
        if img_field in request.FILES:
            setattr(bloque, img_field, request.FILES[img_field])

    # Auto-configure button 1 when event is linked
    if bloque.sesion and not bloque.boton_1_texto:
        bloque.boton_1_texto = 'Regístrate Aquí'
        bloque.boton_1_url = f'/sesion/{bloque.sesion.id}/registro/'
        bloque.boton_1_icono = 'fa-solid fa-user-plus'

    bloque.save()
    return JsonResponse({'ok': True})


@login_required
@user_passes_test(lambda u: u.rol == 'superadmin')
@require_http_methods(["POST"])
def landing_delete_block(request, id):
    """AJAX: Delete a landing block."""
    bloque = get_object_or_404(LandingBloque, id=id)
    bloque.delete()
    return JsonResponse({'ok': True})


@login_required
@user_passes_test(lambda u: u.rol == 'superadmin')
@require_http_methods(["POST"])
def landing_reorder(request):
    """AJAX: Reorder landing blocks."""
    try:
        order_data = json.loads(request.body)
        for item in order_data:
            LandingBloque.objects.filter(id=item['id']).update(orden=item['orden'])
        return JsonResponse({'ok': True})
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)


# ---------------------------------------------------------------------------
# Líderes Académicos
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(_is_admin)
def lideres_list(request):
    """Lista de líderes académicos con búsqueda."""
    q = request.GET.get('q', '').strip()
    lideres = Participante.objects.filter(es_lider=True).order_by('-created_at')
    if q:
        lideres = lideres.filter(
            models_Q(cedula__icontains=q) |
            models_Q(email__icontains=q) |
            models_Q(nombres__icontains=q) |
            models_Q(apellidos__icontains=q)
        )
    return render(request, 'panel/lideres/list.html', {
        'lideres': lideres,
        'total': Participante.objects.filter(es_lider=True).count(),
        'q': q,
    })


@login_required
@user_passes_test(_is_admin)
@require_http_methods(["POST"])
def lideres_add_manual(request):
    """Registrar un líder manualmente."""
    cedula = request.POST.get('cedula', '').strip()
    nombres = request.POST.get('nombres', '').strip().upper()
    apellidos = request.POST.get('apellidos', '').strip().upper()
    email = request.POST.get('email', '').strip().lower()
    celular = request.POST.get('celular', '').strip()

    if not nombres or not apellidos:
        messages.error(request, 'Nombres y apellidos son obligatorios.')
        return redirect('panel:lideres_list')
    if not cedula and not email:
        messages.error(request, 'Debe proporcionar al menos cédula o correo.')
        return redirect('panel:lideres_list')

    # Deduplication: find existing participante
    participante = None
    if cedula:
        participante = Participante.objects.filter(cedula=cedula).first()
    if not participante and email:
        participante = Participante.objects.filter(email__iexact=email).first()

    if participante:
        if participante.es_lider:
            messages.info(request, f'{participante.nombres} {participante.apellidos} ya es líder académico.')
        else:
            participante.es_lider = True
            updated = ['es_lider']
            if cedula and not participante.cedula:
                participante.cedula = cedula
                updated.append('cedula')
            if celular and not participante.celular:
                participante.celular = celular
                updated.append('celular')
            participante.save(update_fields=updated)
            messages.success(request, f'{participante.nombres} {participante.apellidos} marcado como líder.')
    else:
        Participante.objects.create(
            cedula=cedula, nombres=nombres, apellidos=apellidos,
            email=email, celular=celular, es_lider=True,
        )
        messages.success(request, f'Líder {nombres} {apellidos} registrado exitosamente.')

    _log_audit(request.user, 'AGREGAR_LIDER', f'Líder: {cedula or email}')
    return redirect('panel:lideres_list')


@login_required
@user_passes_test(_is_admin)
@require_http_methods(["POST"])
def lideres_upload_excel(request):
    """Step 1: Upload Excel → save temp file → redirect to mapping."""
    import os
    from django.core.files.storage import default_storage

    archivo = request.FILES.get('archivo')
    if not archivo:
        messages.error(request, 'No se seleccionó ningún archivo.')
        return redirect('panel:lideres_list')

    # Save temp file
    temp_path = default_storage.save(f'temp/lideres_{uuid.uuid4().hex[:8]}.xlsx', archivo)
    full_path = default_storage.path(temp_path)

    # Analyze headers
    analysis = analyze_excel_file(full_path)
    if not analysis['success']:
        default_storage.delete(temp_path)
        messages.error(request, f"Error leyendo Excel: {analysis.get('error')}")
        return redirect('panel:lideres_list')

    # Store temp path in session for step 2
    request.session['lideres_temp_file'] = temp_path

    return render(request, 'panel/lideres/mapping.html', {
        'columns': analysis['columns'],
        'suggestions': analysis['suggestions'],
        'preview': analysis['preview'],
    })


@login_required
@user_passes_test(_is_admin)
@require_http_methods(["POST"])
def lideres_process_mapping(request):
    """Step 2: Process Excel with user-selected mapping."""
    import pandas as pd
    from django.core.files.storage import default_storage
    from core.validators import sanitize_text

    temp_path = request.session.pop('lideres_temp_file', None)
    if not temp_path:
        messages.error(request, 'Sesión expirada. Sube el Excel de nuevo.')
        return redirect('panel:lideres_list')

    full_path = default_storage.path(temp_path)

    # Get mapping from form
    name_strategy = request.POST.get('name_strategy', 'single')
    col_cedula = request.POST.get('col_cedula')
    col_email = request.POST.get('col_email')
    col_celular = request.POST.get('col_celular')

    if name_strategy == 'split':
        col_nombres = request.POST.get('col_nombres_split')
        col_apellidos = request.POST.get('col_apellidos')
    else:
        col_nombres = request.POST.get('col_nombres')
        col_apellidos = None

    try:
        df = pd.read_excel(full_path, dtype=str)
        df.columns = [str(c).strip() for c in df.columns]

        nuevos = 0
        actualizados = 0

        for _, row in df.iterrows():
            # Extract with mapping
            cedula = sanitize_text(str(row.get(col_cedula, '') or '')) if col_cedula and col_cedula in df.columns else ''
            email = sanitize_text(str(row.get(col_email, '') or '')).lower() if col_email and col_email in df.columns else ''
            nombre_raw = sanitize_text(str(row.get(col_nombres, '') or '')) if col_nombres and col_nombres in df.columns else ''
            apellido_raw = sanitize_text(str(row.get(col_apellidos, '') or '')) if col_apellidos and col_apellidos in df.columns else ''
            celular = sanitize_text(str(row.get(col_celular, '') or '')) if col_celular and col_celular in df.columns else ''

            # Clean NaN
            if cedula.lower() == 'nan': cedula = ''
            if email.lower() == 'nan': email = ''
            if nombre_raw.lower() == 'nan': nombre_raw = ''
            if apellido_raw.lower() == 'nan': apellido_raw = ''
            if celular.lower() == 'nan': celular = ''

            # Cedula cleanup
            if cedula.endswith('.0'): cedula = cedula[:-2]

            if not cedula and not email:
                continue

            # Name parsing (same logic as batch import)
            final_nombres = 'LÍDER'
            final_apellidos = 'ACADÉMICO'
            if apellido_raw:
                final_nombres = nombre_raw.upper()
                final_apellidos = apellido_raw.upper()
            elif nombre_raw:
                parts = nombre_raw.split()
                if len(parts) >= 2:
                    if len(parts) == 2:
                        final_nombres = parts[0].upper()
                        final_apellidos = parts[1].upper()
                    elif len(parts) == 3:
                        final_nombres = parts[0].upper()
                        final_apellidos = f"{parts[1]} {parts[2]}".upper()
                    else:
                        mid = len(parts) // 2
                        final_nombres = " ".join(parts[:mid]).upper()
                        final_apellidos = " ".join(parts[mid:]).upper()
                else:
                    final_nombres = nombre_raw.upper()

            # Find or create participante
            participante = None
            if cedula:
                participante = Participante.objects.filter(cedula=cedula).first()
            if not participante and email:
                participante = Participante.objects.filter(email__iexact=email).first()

            if participante:
                changed = False
                if not participante.es_lider:
                    participante.es_lider = True
                    changed = True
                if cedula and not participante.cedula:
                    participante.cedula = cedula
                    changed = True
                if email and not participante.email:
                    participante.email = email
                    changed = True
                if final_nombres != 'LÍDER' and participante.nombres in ('', 'LÍDER', 'PARTICIPANTE'):
                    participante.nombres = final_nombres
                    changed = True
                if final_apellidos != 'ACADÉMICO' and participante.apellidos in ('', 'ACADÉMICO', 'S/N'):
                    participante.apellidos = final_apellidos
                    changed = True
                if celular and not participante.celular:
                    participante.celular = celular
                    changed = True
                if changed:
                    participante.save()
                    actualizados += 1
            else:
                Participante.objects.create(
                    cedula=cedula, nombres=final_nombres, apellidos=final_apellidos,
                    email=email, celular=celular, es_lider=True,
                )
                nuevos += 1

        _log_audit(request.user, 'SUBIR_LIDERES_EXCEL', f'{nuevos} nuevos, {actualizados} actualizados')
        messages.success(request, f'Excel procesado: {nuevos} líderes nuevos, {actualizados} actualizados.')

    except Exception as e:
        messages.error(request, f'Error procesando: {str(e)}')
    finally:
        # Cleanup temp file
        try:
            default_storage.delete(temp_path)
        except Exception:
            pass

    return redirect('panel:lideres_list')


@login_required
@user_passes_test(_is_admin)
@require_http_methods(["POST"])
def lideres_remove(request, id):
    """Quitar marca de líder a un participante."""
    p = get_object_or_404(Participante, id=id)
    p.es_lider = False
    p.save(update_fields=['es_lider'])
    messages.success(request, f'{p.nombres} {p.apellidos} ya no es líder académico.')
    return redirect('panel:lideres_list')


# ---------------------------------------------------------------------------
# Gestión de Usuarios (solo superadmin)
# ---------------------------------------------------------------------------

def _is_superadmin(user):
    return user.is_authenticated and user.rol == 'superadmin'


@login_required
@user_passes_test(_is_superadmin)
def usuarios_list(request):
    """Lista de usuarios administradores con opción de resetear clave."""
    q = request.GET.get('q', '').strip()
    usuarios = Usuario.objects.filter(rol__in=['admin', 'superadmin']).order_by('first_name', 'last_name')
    if q:
        usuarios = usuarios.filter(
            db_models.Q(first_name__icontains=q) |
            db_models.Q(last_name__icontains=q) |
            db_models.Q(email__icontains=q) |
            db_models.Q(username__icontains=q)
        )
    return render(request, 'panel/usuarios/list.html', {'usuarios': usuarios, 'q': q})


@login_required
@user_passes_test(_is_superadmin)
@require_http_methods(["POST"])
def usuario_reset_password(request, id):
    """Resetea la clave de un usuario a mucunemi25."""
    usuario = get_object_or_404(Usuario, id=id)
    usuario.set_password('mucunemi25')
    usuario.save()
    _log_audit(request.user, 'RESET_CLAVE', f'Clave reseteada para: {usuario.email}')
    messages.success(request, f'Clave de {usuario.get_full_name() or usuario.email} reseteada a la clave por defecto.')



@login_required
@user_passes_test(_is_admin)
def participantes_list(request):
    """Lista global de participantes con búsqueda y filtros."""
    q = request.GET.get('q', '').strip()
    participantes = Participante.objects.all().order_by('-created_at')

    if q:
        participantes = participantes.filter(
            db_models.Q(cedula__icontains=q) |
            db_models.Q(email__icontains=q) |
            db_models.Q(nombres__icontains=q) |
            db_models.Q(apellidos__icontains=q)
        )

    return render(request, 'panel/participantes/list.html', {
        'participantes': participantes,
        'q': q,
        'total': Participante.objects.count()
    })


@login_required
@user_passes_test(_is_admin)
@require_http_methods(["POST"])
def participante_delete(request, id):
    """Eliminar un participante."""
    participante = get_object_or_404(Participante, id=id)
    nombre = f"{participante.nombres} {participante.apellidos}"
    participante.delete()
    _log_audit(request.user, 'ELIMINAR_PARTICIPANTE', f'Eliminado: {nombre}')
    messages.success(request, f'Participante {nombre} eliminado correctamente.')
    return redirect('panel:participantes_list')

