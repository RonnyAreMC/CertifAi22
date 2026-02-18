from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from django.http import FileResponse, HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from core.models import Certificado
from core.services.pdf_service import generate_certificate_pdf
import zipfile
import io


def home(request):
    """Public homepage."""
    return render(request, 'public/home.html')


def search(request):
    """Search certificates by ID, email, or name."""
    query = request.GET.get('q', '').strip()
    certificados = []

    if query and len(query) >= 3:
        certificados = list(
            Certificado.objects.filter(
                Q(cedula__icontains=query)
                | Q(email__icontains=query)
                | Q(nombres__icontains=query)
                | Q(apellidos__icontains=query)
            )
            .select_related('lote')
            .order_by('-created_at')
        )

        # Update search metrics
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
    certificado = get_object_or_404(Certificado, hash_verificacion=hash)

    try:
        pdf_buffer = generate_certificate_pdf(certificado)
        response = FileResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = (
            f'inline; filename="Certificado_{certificado.cedula}.pdf"'
        )

        # Increment download count
        certificado.descargas_count += 1
        certificado.save(update_fields=['descargas_count'])

        return response
    except Exception as e:
        return HttpResponse(f"Error generando PDF: {str(e)}", status=500)


def download_zip(request):
    """Bulk download all certificates matching a search query as ZIP."""
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
                filename = f"{cert.curso}_{cert.cedula}.pdf".replace("/", "-")
                zip_file.writestr(filename, pdf_buffer.getvalue())
            except Exception:
                continue

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="Certificados_{query}.zip"'
    return response
