import io
import zipfile

from django.db.models import Q
from django.http import FileResponse, Http404, HttpResponse
from django.utils import timezone
from django.utils.text import slugify
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.models import Certificado, Participante
from core.services.pdf_service import generate_certificate_pdf

from .serializers import CertificadoListSerializer


class PublicCertificadoViewSet(viewsets.ReadOnlyModelViewSet):
    """Acceso público a certificados: búsqueda, verificación y descarga por hash."""
    queryset = Certificado.objects.with_relations()
    serializer_class = CertificadoListSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'hash_verificacion'

    def list(self, request, *args, **kwargs):
        q = request.query_params.get('q', '').strip()
        if len(q) < 3:
            return Response({'count': 0, 'results': []})
        # Search con AND entre tokens + dedupe por (cedula, curso)
        ids = list(self.get_queryset().search(q).deduped_by_person_course().values_list('id', flat=True)[:50])
        qs = self.get_queryset().filter(id__in=ids)
        return Response({
            'count': len(ids),
            'results': self.get_serializer(qs, many=True).data,
        })

    @action(detail=False, methods=['get'])
    def autocomplete(self, request):
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response({'results': []})

        tokens = [t for t in query.split() if t]
        if not tokens:
            return Response({'results': []})

        q = Q()
        for t in tokens:
            q &= (Q(cedula__icontains=t) | Q(email__icontains=t) |
                  Q(nombres__icontains=t) | Q(apellidos__icontains=t))

        seen, results = set(), []
        for p in Participante.objects.filter(q)[:20]:
            name = f'{p.nombres.strip()} {p.apellidos.strip()}'.strip()
            key = name.lower()
            if name and key not in seen:
                seen.add(key)
                results.append({'name': name})
                if len(results) >= 12:
                    break

        if len(results) < 12:
            cert_q = Q()
            for t in tokens:
                cert_q &= (Q(cedula__icontains=t) | Q(email__icontains=t) |
                           Q(nombres__icontains=t) | Q(apellidos__icontains=t))
            orphans = (
                Certificado.objects.filter(cert_q, participante__isnull=True)
                .values('nombres', 'apellidos').distinct()[:20]
            )
            for o in orphans:
                name = f'{(o["nombres"] or "").strip()} {(o["apellidos"] or "").strip()}'.strip()
                key = name.lower()
                if name and key not in seen:
                    seen.add(key)
                    results.append({'name': name})
                    if len(results) >= 12:
                        break

        return Response({'results': results})

    @action(detail=True, methods=['get'])
    def verify(self, request, hash_verificacion=None):
        try:
            cert = self.get_queryset().get(hash_verificacion=hash_verificacion)
        except Certificado.DoesNotExist:
            return Response({'valid': False, 'message': 'Certificado no encontrado'},
                            status=status.HTTP_404_NOT_FOUND)

        Certificado.objects.filter(pk=cert.pk).update(veces_buscado=cert.veces_buscado + 1)

        return Response({
            'valid': True,
            'nombres': cert.nombres,
            'apellidos': cert.apellidos,
            'cedula': cert.cedula,
            'curso': cert.curso,
            'fecha_curso': cert.fecha_curso,
            'horas': cert.horas,
            'lote': cert.lote.nombre_lote if cert.lote else None,
            'hash': cert.hash_verificacion,
        })

    @action(detail=False, methods=['get'], url_path='bulk-download')
    def bulk_download(self, request):
        """Descarga en ZIP todos los certificados que coincidan con ?q=X."""
        query = request.query_params.get('q', '').strip()
        if not query:
            return HttpResponse('No query provided', status=status.HTTP_400_BAD_REQUEST)

        qs = self.get_queryset().search(query)
        if not qs.exists():
            return HttpResponse('No certificates found', status=status.HTTP_404_NOT_FOUND)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            seen_names = {}
            for cert in qs:
                try:
                    pdf_buffer = generate_certificate_pdf(cert)
                    safe_curso = slugify(cert.curso) or 'certificado'
                    base = f'{safe_curso}_{cert.cedula}'
                    count = seen_names.get(base, 0)
                    seen_names[base] = count + 1
                    filename = f'{base}.pdf' if count == 0 else f'{base}_{count + 1}.pdf'
                    zf.writestr(filename, pdf_buffer.getvalue())
                except Exception:
                    continue

        zip_buffer.seek(0)
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        zip_name = f'certificados_{slugify(query)}.zip'
        response['Content-Disposition'] = f'attachment; filename="{zip_name}"'
        response['Cache-Control'] = 'no-store'
        return response

    @action(detail=True, methods=['get'])
    def download(self, request, hash_verificacion=None):
        try:
            cert = self.get_queryset().get(hash_verificacion=hash_verificacion)
        except Certificado.DoesNotExist:
            raise Http404('Certificado no encontrado')

        buffer = generate_certificate_pdf(cert)

        Certificado.objects.filter(pk=cert.pk).update(
            descargas_count=cert.descargas_count + 1,
            fecha_ultima_descarga=timezone.now(),
        )

        filename = f'Certificado_{cert.cedula}_{cert.hash_verificacion[:8]}.pdf'
        response = FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')
        response['Cache-Control'] = 'no-store'
        return response
