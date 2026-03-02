from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib import messages
from django.http import FileResponse, HttpResponse, JsonResponse
from django.db.models import Sum, Count, F
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta, datetime, date, time

from core.models import (
    LoteCertificados, Certificado, Auditoria,
    SesionAsistencia, RegistroAsistencia, ConfirmacionAsistencia,
)
from core.services.pdf_service import generate_certificate_pdf
from core.services.excel_service import process_excel_batch, analyze_headers
from .forms import BatchForm

import base64
import uuid
import random
import json
from io import BytesIO


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_admin(user):
    """Check if user has admin privileges."""
    return user.is_authenticated and user.rol in ['admin', 'superadmin']


def _log_audit(user, action, detail):
    """Create an audit log entry."""
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
    return render(request, 'panel/dashboard.html', context)


# ---------------------------------------------------------------------------
# Batch CRUD
# ---------------------------------------------------------------------------

@login_required
@user_passes_test(_is_admin)
def list_batches(request):
    """List all certificate batches."""
    lotes = LoteCertificados.objects.all().order_by('id')
    return render(request, 'panel/batch_list.html', {'lotes': lotes})


@login_required
@user_passes_test(_is_admin)
def create_batch(request):
    """Create a new batch and process its Excel file."""
    if request.method == 'POST':
        form = BatchForm(request.POST, request.FILES)
        if form.is_valid():
            lote = form.save(commit=False)
            lote.administrador = request.user
            lote.save()
            _log_audit(request.user, 'CREAR_LOTE', f'Lote creado: {lote.nombre_lote}')

            # Redirect to mapping page instead of immediate processing
            messages.info(request, "Lote creado. Por favor confirma las columnas del Excel.")
            return redirect('panel:batch_process_mapping', id=lote.id)
    else:
        form = BatchForm()
    return render(request, 'panel/batch_form.html', {'form': form})


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

    return render(request, 'panel/batch_mapping.html', {
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
    return render(request, 'panel/batch_detail.html', {
        'lote': lote,
        'certificados': certificados,
    })


@login_required
@user_passes_test(_is_admin)
def configure_batch(request, id):
    """Configure batch template, colors, signatures, and logos."""
    lote = get_object_or_404(LoteCertificados, id=id)

    if request.method == 'POST':
        lote.cuerpo_certificado = request.POST.get('cuerpo_certificado')
        lote.nombre_firma_1 = request.POST.get('nombre_firma_1')
        lote.cargo_firma_1 = request.POST.get('cargo_firma_1')
        lote.nombre_firma_2 = request.POST.get('nombre_firma_2')
        lote.cargo_firma_2 = request.POST.get('cargo_firma_2')
        lote.nombre_firma_3 = request.POST.get('nombre_firma_3')
        lote.cargo_firma_3 = request.POST.get('cargo_firma_3')
        lote.nombre_firma_4 = request.POST.get('nombre_firma_4')
        lote.cargo_firma_4 = request.POST.get('cargo_firma_4')

        # Template & Colors
        lote.plantilla = request.POST.get('plantilla', 'clasico')
        lote.color_primario = request.POST.get('color_primario', '#162054')
        lote.color_secundario = request.POST.get('color_secundario', '#D4AF37')
        lote.color_terciario = request.POST.get('color_terciario', '#F3F4F6')
        lote.color_texto = request.POST.get('color_texto', '#333333')

        # Handle Base64 signature images
        for i in range(1, 5):
            field_name = f'imagen_firma_{i}'
            if field_name in request.FILES:
                file_obj = request.FILES[field_name]
                encoded = base64.b64encode(file_obj.read()).decode('utf-8')
                setattr(lote, field_name, encoded)

        # Handle logos
        if 'logo_header_1' in request.FILES:
            lote.logo_header_1 = request.FILES['logo_header_1']
        if 'logo_header_2' in request.FILES:
            lote.logo_header_2 = request.FILES['logo_header_2']
        if 'logo_header_3' in request.FILES:
            lote.logo_header_3 = request.FILES['logo_header_3']

        lote.save()
        messages.success(request, 'Diseño guardado correctamente.')
        return redirect('panel:batch_configure', id=lote.id)

    return render(request, 'panel/batch_config.html', {'lote': lote})


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

            Certificado.objects.create(
                lote=lote,
                cedula=request.POST.get('cedula'),
                nombres=request.POST.get('nombres'),
                apellidos=request.POST.get('apellidos'),
                email=request.POST.get('email'),
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

    return render(request, 'panel/session_list.html', {
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
        fecha_str = request.POST.get('fecha')
        dia_semana = request.POST.get('dia_semana')
        hora_inicio_str = request.POST.get('hora_inicio')
        hora_fin_str = request.POST.get('hora_fin')
        titulo = request.POST.get('titulo', '')

        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
            hora_fin = datetime.strptime(hora_fin_str, '%H:%M').time()

            SesionAsistencia.objects.create(
                titulo=titulo,
                fecha=fecha,
                dia_semana=dia_semana,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
            )
            _log_audit(request.user, 'CREAR_SESION',
                       f'Sesión creada: {dia_semana} {fecha} {hora_inicio_str}-{hora_fin_str}')
            messages.success(request, 'Sesión creada exitosamente.')
        except Exception as e:
            messages.error(request, f'Error al crear sesión: {str(e)}')

        return redirect('panel:session_list')

    return redirect('panel:session_list')


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

    return render(request, 'panel/session_qr_display.html', {
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
    
    registros = RegistroAsistencia.objects.filter(sesion=sesion).select_related('certificado')
    
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
        attendees.append({
            'id': r.id,
            'nombre': f'{r.certificado.nombres} {r.certificado.apellidos}',
            'cedula': r.certificado.cedula,
            'email': r.certificado.email,
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

