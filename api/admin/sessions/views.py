import os
import uuid
from datetime import datetime
from io import BytesIO

from django.conf import settings as django_settings
from django.core.files import File
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import (
    SesionAsistencia, ConfirmacionAsistencia, RegistroAsistencia,
    LoteCertificados, Certificado, FirmaInstitucional,
)
from core.services.pdf_service import generate_certificate_pdf
from api.common.viewsets import AuditedModelViewSet

from .serializers import (
    SesionListSerializer,
    SesionDetailSerializer,
    SesionWriteSerializer,
    ConfirmacionSerializer,
)


class SesionViewSet(AuditedModelViewSet):
    """CRUD admin de sesiones/eventos."""
    queryset = SesionAsistencia.objects.all()
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['activa', 'modalidad', 'solo_lideres', 'fecha', 'lote']
    search_fields = ['titulo', 'descripcion', 'lugar']
    ordering_fields = ['fecha', 'hora_inicio', 'created_at']
    ordering = ['-fecha', '-hora_inicio']

    audit_verbose_name = 'sesion'

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return SesionWriteSerializer
        if self.action == 'retrieve':
            return SesionDetailSerializer
        return SesionListSerializer

    def audit_detail(self, instance, action):
        return f'Sesión #{instance.pk} ({instance.titulo or instance.dia_semana} - {instance.fecha})'

    def destroy(self, request, *args, **kwargs):
        sesion = self.get_object()
        if sesion.confirmaciones.exists() or sesion.registros.exists():
            return Response(
                {'error': 'No puedes eliminar una sesión que ya tiene participantes registrados o confirmados.'},
                status=status.HTTP_409_CONFLICT,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        sesion = self.get_object()
        sesion.activa = not sesion.activa
        sesion.save(update_fields=['activa'])
        self.log_audit('TOGGLE_SESION', f'Sesión #{sesion.pk} → activa={sesion.activa}')
        return Response({'id': sesion.id, 'activa': sesion.activa})

    @action(detail=True, methods=['get'])
    def confirmados(self, request, pk=None):
        sesion = self.get_object()
        qs = (
            ConfirmacionAsistencia.objects
            .filter(sesion=sesion, confirmado=True)
            .select_related('participante')
            .order_by('-fecha_confirmacion')
        )
        return Response(ConfirmacionSerializer(qs, many=True).data)

    @action(detail=True, methods=['get'])
    def attendees(self, request, pk=None):
        """GET ?since=... → feed de asistencias en tiempo real."""
        sesion = self.get_object()
        since_str = request.query_params.get('since', '')

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
            p = r.participante
            c = r.certificado
            attendees.append({
                'id': r.id,
                'nombre': f'{p.nombres} {p.apellidos}' if p else (f'{c.nombres} {c.apellidos}' if c else '?'),
                'cedula': p.cedula if p else (c.cedula if c else ''),
                'email': p.email if p else (c.email if c else ''),
                'hora': r.fecha_registro.strftime('%H:%M:%S'),
                'timestamp': r.fecha_registro.isoformat(),
            })

        return Response({
            'total': total,
            'attendees': attendees,
            'server_time': timezone.now().isoformat(),
        })

    @action(detail=True, methods=['get'], url_path='qr-info')
    def qr_info(self, request, pk=None):
        """GET → URL de check-in absoluta + totales para la pantalla QR."""
        sesion = self.get_object()
        checkin_url = request.build_absolute_uri(f'/checkin/{sesion.codigo_qr}/')
        return Response({
            'codigo_qr': sesion.codigo_qr,
            'checkin_url': checkin_url,
            'total_registros': RegistroAsistencia.objects.filter(sesion=sesion).count(),
            'titulo': sesion.titulo or sesion.dia_semana,
            'fecha': sesion.fecha.strftime('%d/%m/%Y'),
            'horario': sesion.label,
        })

    @action(detail=True, methods=['get'], url_path='bulk-pdf')
    def bulk_pdf(self, request, pk=None):
        """GET → merge PDF de todos los certificados de participantes confirmados."""
        from PyPDF2 import PdfMerger

        sesion = self.get_object()
        confirmaciones = ConfirmacionAsistencia.objects.filter(
            sesion=sesion, confirmado=True
        ).select_related('certificado', 'certificado__lote')

        if not confirmaciones.exists():
            return Response({'error': 'No hay participantes confirmados.'}, status=status.HTTP_404_NOT_FOUND)

        merger = PdfMerger()
        count = 0
        for conf in confirmaciones:
            try:
                cert = conf.certificado
                if not cert:
                    continue
                pdf_buffer = generate_certificate_pdf(cert)
                merger.append(pdf_buffer)
                count += 1
            except Exception:
                continue

        if count == 0:
            return Response({'error': 'No se pudo generar ningún certificado.'}, status=status.HTTP_404_NOT_FOUND)

        output_buffer = BytesIO()
        merger.write(output_buffer)
        merger.close()
        output_buffer.seek(0)

        safe_dia = sesion.dia_semana.replace('é', 'e').replace('á', 'a')
        filename = f'Certificados_{safe_dia}_{sesion.hora_inicio:%H%M}_{count}personas.pdf'

        self.log_audit('BULK_PDF_SESION', f'Sesión #{sesion.pk}: {count} PDFs merged')
        response = HttpResponse(output_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    @action(detail=True, methods=['post'], url_path='generate-batch')
    def generate_batch(self, request, pk=None):
        """POST {facultad} → crea LoteCertificados desde los confirmados de esta sesión."""
        sesion = self.get_object()

        if sesion.lote:
            return Response(
                {'error': 'Esta sesión ya tiene un lote asociado.', 'lote_id': sesion.lote_id},
                status=status.HTTP_409_CONFLICT,
            )

        confirmaciones = ConfirmacionAsistencia.objects.filter(
            sesion=sesion, confirmado=True, participante__isnull=False
        ).select_related('participante')

        if not confirmaciones.exists():
            return Response(
                {'error': 'No hay participantes confirmados para generar certificados.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        facultad = request.data.get('facultad', 'FACI')

        with transaction.atomic():
            sesion = SesionAsistencia.objects.select_for_update().get(pk=pk)
            if sesion.lote:
                return Response(
                    {'error': 'Esta sesión ya tiene un lote asociado.', 'lote_id': sesion.lote_id},
                    status=status.HTTP_409_CONFLICT,
                )

            lote = LoteCertificados.objects.create(
                nombre_lote=sesion.titulo or f'Sesión {sesion.fecha} {sesion.label}',
                administrador=request.user,
                facultad=facultad,
            )

            firmas_default = list(FirmaInstitucional.objects.filter(activa=True).order_by('orden')[:3])
            for i, firma in enumerate(firmas_default, start=1):
                setattr(lote, f'firma_inst_{i}', firma)

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

            sesion.lote = lote
            sesion.save(update_fields=['lote'])

        self.log_audit(
            'GENERAR_LOTE_SESION',
            f'Lote "{lote.nombre_lote}" generado desde sesión {sesion.id} con {len(certs)} certificados',
        )
        return Response({
            'ok': True,
            'lote_id': lote.id,
            'lote_nombre': lote.nombre_lote,
            'certificados_creados': len(certs),
        })
