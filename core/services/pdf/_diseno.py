import os
# Force Reload Fix for Function Signature Update
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from django.conf import settings
from datetime import datetime
from io import BytesIO
import base64


# --- FONTS ---
_fonts_registered = False

def _apply_diseno_global(lote):
    """
    Sobrescribe los campos de diseño del lote (en memoria) con los del
    DisenoGlobal singleton, para que toda la generación de PDF use el
    diseño global sin tener que tocar cada función.

    Si el lote tiene `personalizar_diseno=True`, se usa el diseño propio del lote.
    """
    if getattr(lote, 'personalizar_diseno', False):
        return lote

    try:
        from core.models import DisenoGlobal
        diseno = DisenoGlobal.get_solo()
    except Exception:
        return lote

    lote.plantilla = diseno.plantilla
    lote.color_primario = diseno.color_primario
    lote.color_secundario = diseno.color_secundario
    lote.color_terciario = diseno.color_terciario
    lote.color_texto = diseno.color_texto
    lote.cuerpo_certificado = diseno.cuerpo_certificado

    lote.firma_inst_1 = diseno.firma_inst_1
    lote.firma_inst_2 = diseno.firma_inst_2
    lote.firma_inst_3 = diseno.firma_inst_3
    # Limpiar firmas custom (1-3) — el diseño global solo usa firmas institucionales 1-3
    for i in (1, 2, 3):
        setattr(lote, f'nombre_firma_{i}', '')
        setattr(lote, f'cargo_firma_{i}', '')
        setattr(lote, f'imagen_firma_{i}', '')

    # Firma 4 = la personalizada del diseño global
    lote.firma_inst_4 = None
    lote.nombre_firma_4 = diseno.nombre_firma_4 or ''
    lote.cargo_firma_4 = diseno.cargo_firma_4 or ''
    lote.imagen_firma_4 = diseno.imagen_firma_4 or ''

    lote.logo_header_1 = diseno.logo_header_1
    lote.logo_header_2 = diseno.logo_header_2
    lote.logo_header_3 = diseno.logo_header_3

    lote.posicion_firmas = diseno.posicion_firmas

    # Per-signature adjustments
    for i in range(1, 5):
        setattr(lote, f'firma_{i}_offset_y', getattr(diseno, f'firma_{i}_offset_y', 0))
        setattr(lote, f'firma_{i}_escala', getattr(diseno, f'firma_{i}_escala', 100))

    return lote


