from django.db.models import Q
from core.models import Certificado, LoteCertificados

def search_certificates(query):
    """
    Search certificates by various fields.
    Optimized with select_related.
    """
    if not query:
        return []
        
    query = query.strip()
    
    # Validation constraint: Minimum 3 chars to search?
    if len(query) < 3:
        return []

    return Certificado.objects.filter(
        Q(cedula__icontains=query) | 
        Q(email__icontains=query) |
        Q(nombres__icontains=query) |
        Q(apellidos__icontains=query)
    ).select_related('lote').order_by('-created_at')

def get_certificate_by_hash(hash_verificacion):
    return Certificado.objects.filter(hash_verificacion=hash_verificacion).first()
