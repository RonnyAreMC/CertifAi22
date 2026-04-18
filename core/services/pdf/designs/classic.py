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

from .._helpers import register_fonts, hex2rgb, get_current_date_text
from .._signatures import draw_signatures
from .._logos import draw_smart_logos

def draw_classic_wow(c, certificado, width, height, pri, sec, ter, txt):
    """
    Ported Classic Design from Main App.
    Matches 'CertificateGenerator' layout but adapted for 'Certificado' model.
    """
    register_fonts()
    lote = certificado.lote # Fix: Define lote for subsequent usage
    
    # Fonts
    TITLE_FONT = "Times-Bold"
    BODY_FONT = "Times-Roman"
    SANS_FONT = "Helvetica"
    SANS_BOLD = "Helvetica-Bold"
    
    SCRIPT_FONT = "Times-BoldItalic" # Fallback
    try:
        pdfmetrics.getFont('GreatVibes')
        SCRIPT_FONT = 'GreatVibes'
    except:
        pass

    # === DECORATIVE ELEMENTS ===
    
    # 1. Ribbon Background (Top Right)
    c.saveState()
    c.translate(width - 60*mm, height - 40*mm) 
    c.rotate(18)
    c.setFillColor(pri, alpha=0.08) 
    c.roundRect(-110*mm, -60*mm, 220*mm, 120*mm, 30*mm, fill=1, stroke=0)
    c.setFillColor(sec, alpha=0.05) 
    c.roundRect(-110*mm, -60*mm, 220*mm, 120*mm, 30*mm, fill=1, stroke=0)
    c.restoreState()

    # 2. Frames (Refined)
    # Outer frame - primary color, more visible
    margin_frame = 10*mm
    frame_w = width - 2 * margin_frame
    frame_h = height - 2 * margin_frame
    
    c.saveState()
    c.setStrokeColor(pri, alpha=0.55)
    c.setLineWidth(3)
    c.roundRect(margin_frame, margin_frame, frame_w, frame_h, 3*mm, fill=0, stroke=1)
    
    # Inner frame - gold, elegant 
    margin_inner = 16*mm
    inner_w = width - 2 * margin_inner
    inner_h = height - 2 * margin_inner
    c.setStrokeColor(sec, alpha=0.7)
    c.setLineWidth(1.5)
    c.roundRect(margin_inner, margin_inner, inner_w, inner_h, 2.5*mm, fill=0, stroke=1)
    c.restoreState()
    
    # 3. Corner Diamond Ornaments
    c.saveState()
    diamond_size = 4*mm
    corners = [
        (margin_inner, margin_inner),
        (width - margin_inner, margin_inner),
        (margin_inner, height - margin_inner),
        (width - margin_inner, height - margin_inner),
    ]
    for cx_d, cy_d in corners:
        c.setFillColor(sec)
        p = c.beginPath()
        p.moveTo(cx_d, cy_d + diamond_size)
        p.lineTo(cx_d + diamond_size, cy_d)
        p.lineTo(cx_d, cy_d - diamond_size)
        p.lineTo(cx_d - diamond_size, cy_d)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        inner_d = diamond_size * 0.5
        c.setFillColor(pri)
        p2 = c.beginPath()
        p2.moveTo(cx_d, cy_d + inner_d)
        p2.lineTo(cx_d + inner_d, cy_d)
        p2.lineTo(cx_d, cy_d - inner_d)
        p2.lineTo(cx_d - inner_d, cy_d)
        p2.close()
        c.drawPath(p2, fill=1, stroke=0)
    c.restoreState()

    # === HEADER CONTENT (3 LOGOS) ===
    header_y_top = height - 16*mm 
    
    # Use existing logo logic (Lote fields are ImageFields, still paths)
    logo_w = 5*cm
    logo_h = 2.8*cm
    
    # helper to draw a single logo
    def draw_single_logo(img_field, x_pos):
        try:
            path = None
            if hasattr(img_field, 'path'): 
                path = img_field.path
            elif isinstance(img_field, str): 
                path = img_field 
            
            if path and os.path.exists(path):
                c.drawImage(path, x_pos, header_y_top - logo_h, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
                return True # Success
        except Exception as e:
            print(f"Error drawing logo at {x_pos}: {e}")
        return False # Failed

    # 1. Left Logo (Logo 1)
    x_left = 30*mm 
    drawn_1 = False
    if lote.logo_header_1:
         drawn_1 = draw_single_logo(lote.logo_header_1, x_left)
    
    if not drawn_1:
         # Default MUC
         default_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'muc.png')
         if os.path.exists(default_path):
             c.drawImage(default_path, x_left, header_y_top - logo_h, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
    
    # 2. Center Logo (Logo 2)
    x_center = width/2 - logo_w/2 
    drawn_2 = False
    if lote.logo_header_2:
        drawn_2 = draw_single_logo(lote.logo_header_2, x_center)
        
    if not drawn_2:
         # Default UNEMI (Requested)
         default_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-unemi-removebg-preview.png')
         if os.path.exists(default_path):
             c.drawImage(default_path, x_center, header_y_top - logo_h, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
        
    # 3. Right Logo (Logo 3)
    x_right = width - 30*mm - logo_w 
    drawn_3 = False
    if lote.logo_header_3:
        drawn_3 = draw_single_logo(lote.logo_header_3, x_right)

    if not drawn_3:
         # Default FEUE
         default_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'feue.png')
         if os.path.exists(default_path):
             c.drawImage(default_path, x_right, header_y_top - logo_h, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
    
    # === MAIN CONTENT ===
    main_y_start = height - 75*mm
    center_x = width / 2
    
    # TITLE (Using Lote Name or generic title?)
    # The 'certify' app uses 'Certificado de Reconocimiento' hardcoded or Lote name?
    # Let's use a standard title or config if available.
    # We'll use "CERTIFICADO" or "RECONOCIMIENTO" based on user preference, 
    # but sticking to the main app's "CERTIFICADO DE LIDERAZGO" equivalent style.
    
    c.setFont(TITLE_FONT, 38)
    c.setFillColor(HexColor('#D4AF37'))  # Gold - fixed, not affected by style colors
    c.drawCentredString(center_x, main_y_start, "CERTIFICADO")
    
    # SUBTITLE
    c.setFont(SANS_BOLD, 11)
    c.setFillColor(HexColor("#1c1c1cb8")) 
    c.drawCentredString(center_x, main_y_start - 10*mm, "DE ASISTENCIA Y APROBACIÓN")
    
    # PRESENTED TO
    c.setFont(BODY_FONT, 13)
    c.setFillColor(HexColor("#1c1c1cc7")) 
    c.drawCentredString(center_x, main_y_start - 22*mm, "Se otorga el presente certificado a:")
    
    # PERSON NAME
    name_font_size = 48 if SCRIPT_FONT == 'GreatVibes' else 32
    c.setFont(SCRIPT_FONT, name_font_size) 
    c.setFillColor(txt)
    name_y = main_y_start - 38*mm
    nombre = f"{certificado.nombres} {certificado.apellidos}".title()
    c.drawCentredString(center_x, name_y, nombre)
    
    # DESCRIPTION
    desc_y = name_y - 20*mm
    c.setFont(SANS_FONT, 14)
    c.setFillColor(HexColor('#000000'))  # Black - fixed, not affected by style colors
    
    # Body Text from Lote
    curso_name = certificado.lote.nombre_lote.upper()
    body = certificado.lote.cuerpo_certificado.replace("{curso}", curso_name).replace("{horas}", str(certificado.horas))

    # Simple Wrap
    from textwrap import wrap
    lines = wrap(body, width=75)
    
    y_text = desc_y
    for line in lines:
        c.drawCentredString(center_x, y_text, line)
        y_text -= 7*mm

    c.setFont("Times-Italic", 13); c.setFillColor(HexColor('#777777'))
    c.drawRightString(width - 2.5*cm, 2.0*cm, get_current_date_text(certificado.fecha_curso))
    
    # SIGNATURES
    draw_signatures(c, certificado, width, 35*mm + 10*mm)


