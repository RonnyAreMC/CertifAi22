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
from .._signatures import _draw_geometric_signatures
from .._logos import draw_smart_logos

def draw_geometric_wow(c, certificado, width, height, pri, sec, ter, txt):
    """
    Plantilla Geométrica Premium - Diseño Profesional UNEMI
    - Esquinas geométricas profesionales (chevron layers)
    - Marca de agua UNEMI de fondo
    - Tipografía refinada con GreatVibes para nombre
    - Firmas profesionales con línea DEBAJO del texto
    - Fecha entre logos y cuerpo del texto
    - Curso en NEGRITA en el cuerpo
    - Segunda página con QR de verificación
    """
    lote = certificado.lote
    register_fonts()
    
    # Fonts
    SCRIPT_FONT = "Times-Italic" 
    try:
        pdfmetrics.getFont('GreatVibes')
        SCRIPT_FONT = 'GreatVibes'
    except: pass
    
    # --- 1. WATERMARK (Background IMAGE - FULL WIDTH ZOOMED) ---
    c.saveState()
    c.setFillAlpha(0.08)
    c.setStrokeAlpha(0.08)
    
    logo_watermark_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-unemi-removebg-preview.png')
    
    if os.path.exists(logo_watermark_path):
        w_img = width * 1.18 
        h_img = w_img * 0.28
        x_img = (width - w_img) / 2
        y_img = -1.5*cm
        c.drawImage(logo_watermark_path, x_img, y_img, width=w_img, height=h_img, mask='auto', preserveAspectRatio=True, anchor='c')
    
    c.restoreState()

    # --- 2. GEOMETRIC CORNERS (Professional Layered Chevrons) ---
    def draw_corner_professional(origin_x, origin_y, rotation, main_col, acc_col):
        c.saveState()
        c.translate(origin_x, origin_y)
        c.rotate(rotation)
        
        # Base Layer (Large Dark Chevron)
        c.setFillColor(main_col)
        p1 = c.beginPath()
        p1.moveTo(0, 0)
        p1.lineTo(9.0*cm, 0)
        p1.lineTo(7.5*cm, 3.0*cm)
        p1.lineTo(3.0*cm, 3.0*cm)
        p1.lineTo(0, 9.0*cm)
        p1.close()
        c.drawPath(p1, fill=1, stroke=0)
        
        # Gold Accent Chevron (Nested)
        c.setFillColor(acc_col)
        c.setStrokeColor(white)
        c.setLineWidth(3)
        
        p2 = c.beginPath()
        p2.moveTo(0, 0)
        p2.lineTo(5.5*cm, 0)
        p2.lineTo(0, 5.5*cm)
        p2.close()
        c.drawPath(p2, fill=1, stroke=1) 
        
        # Floating Satellite Chevron
        c.setFillColor(main_col)
        p3 = c.beginPath()
        p3.moveTo(6.5*cm, 0.4*cm)
        p3.lineTo(9.0*cm, 0.4*cm)
        p3.lineTo(7.5*cm, 2.6*cm)
        p3.lineTo(5.5*cm, 2.6*cm)
        p3.close()
        c.drawPath(p3, fill=1, stroke=1)
        
        c.restoreState()

    # Apply Professional Corners
    draw_corner_professional(0, 0, 0, pri, sec)
    draw_corner_professional(width, height, 180, sec, pri)

    # --- 3. LOGOS (Order: FEUE - UNEMI - MUC) --- Always from static/img/
    logo_y = height - 4.8*cm
    logo_h = 3.5*cm
    logo_w = 5.5*cm
    gap = 0.8*cm    
    
    # Always use static logos (survive deploys)
    static_img = os.path.join(settings.BASE_DIR, 'static', 'img')
    logo_files = ['feue.png', 'logo-unemi-removebg-preview.png', 'muc.png']
    logos_ordered = []
    for lf in logo_files:
        p = os.path.join(static_img, lf)
        if os.path.exists(p):
            logos_ordered.append(p)
    
    total_w = (len(logos_ordered) * logo_w) + ((len(logos_ordered)-1) * gap)
    cx = (width - total_w) / 2
    
    for path in logos_ordered:
        try:
             c.drawImage(path, cx, logo_y, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
        except: pass
        cx += (logo_w + gap)
    
    # --- 4. CONTENT ---
    center_x = width / 2
    
    # Content starts below logos
    y_cursor = logo_y - 0.8*cm
    
    # A. Title (Script - Gold)
    script_font_use = "Times-Italic"
    if "GreatVibes" in pdfmetrics.getRegisteredFontNames():
        script_font_use = "GreatVibes"
        
    c.setFont(script_font_use, 44) 
    c.setFillColor(sec)  # Gold
    c.drawCentredString(center_x, y_cursor, "Otorga el presente Reconocimiento")
    y_cursor -= 1.8*cm
    
    # C. "a:" small text
    c.setFont("Times-Italic", 12)
    c.setFillColor(HexColor('#888888'))
    c.drawCentredString(center_x, y_cursor, "a:")
    y_cursor -= 1.4*cm
    
    # D. Name (Script/GreatVibes - Large)
    name_font_size = 50 if script_font_use == 'GreatVibes' else 36
    c.setFont(script_font_use, name_font_size)
    c.setFillColor(HexColor('#1a1a1a'))
    nombre = f"{certificado.nombres} {certificado.apellidos}".title()
    c.drawCentredString(center_x, y_cursor, nombre)
    y_cursor -= 2.0*cm
    
    # E. Body Text with BOLD course name
    body_raw = certificado.lote.cuerpo_certificado
    curso_upper = certificado.lote.nombre_lote.upper()
    horas_str = str(certificado.horas)
    
    # Split body at {curso} to render course in bold
    body_parts = body_raw.replace("{horas}", horas_str).split("{curso}")
    
    from textwrap import wrap
    
    # Calculate available space
    sig_area_top = 5.8*cm  # Where signatures start
    available_height = y_cursor - sig_area_top
    
    # Auto-size based on space
    body_font_size = 14
    line_spacing = 0.65*cm
    wrap_width = 75
    
    # Build full body for wrapping (with marker for bold)
    BOLD_MARKER = "<<<BOLD>>>"
    full_body = BOLD_MARKER.join(body_parts) if len(body_parts) > 1 else body_raw.replace("{curso}", curso_upper).replace("{horas}", horas_str)
    
    if BOLD_MARKER in full_body:
        # Render with mixed bold - line by line approach
        # First, create the plain text for wrapping
        plain_body = full_body.replace(BOLD_MARKER, curso_upper)
        lines = wrap(plain_body, width=wrap_width)
        
        # Check if fits
        needed_height = len(lines) * line_spacing
        if needed_height > available_height:
            body_font_size = 12
            line_spacing = 0.55*cm
            wrap_width = 90
            lines = wrap(plain_body, width=wrap_width)
        
        # Render each line with bold detection for the course name
        for line in lines:
            if curso_upper in line:
                # Split this line at the course name and draw segments
                parts = line.split(curso_upper)
                # Calculate total line width to center it
                regular_widths = sum(c.stringWidth(p, "Times-Roman", body_font_size) for p in parts)
                bold_width = c.stringWidth(curso_upper, "Times-Bold", body_font_size)
                total_line_width = regular_widths + bold_width
                
                draw_x = center_x - total_line_width / 2
                
                for idx, part in enumerate(parts):
                    if part:
                        c.setFont("Times-Roman", body_font_size)
                        c.setFillColor(HexColor('#333333'))
                        c.drawString(draw_x, y_cursor, part)
                        draw_x += c.stringWidth(part, "Times-Roman", body_font_size)
                    
                    if idx < len(parts) - 1:
                        c.setFont("Times-Bold", body_font_size)
                        c.setFillColor(HexColor('#111111'))
                        c.drawString(draw_x, y_cursor, curso_upper)
                        draw_x += c.stringWidth(curso_upper, "Times-Bold", body_font_size)
            else:
                c.setFont("Times-Roman", body_font_size)
                c.setFillColor(HexColor('#333333'))
                c.drawCentredString(center_x, y_cursor, line)
            
            y_cursor -= line_spacing
    else:
        # No marker - simple render
        body_text = full_body
        lines = wrap(body_text, width=wrap_width)
        
        needed_height = len(lines) * line_spacing
        if needed_height > available_height:
            body_font_size = 12
            line_spacing = 0.55*cm
            wrap_width = 90
            lines = wrap(body_text, width=wrap_width)
        
        c.setFont("Times-Roman", body_font_size)
        c.setFillColor(HexColor('#333333'))
        
        for line in lines:
            c.drawCentredString(center_x, y_cursor, line)
            y_cursor -= line_spacing
    
    # --- 5. SIGNATURES (Professional Layout) ---
    sig_y_cm = getattr(lote, 'posicion_firmas', 4.2)
    _draw_geometric_signatures(c, lote, width, pri, sec, sig_y=sig_y_cm * cm)
    
    # --- 6. DATE (below signatures) ---
    date_y = (sig_y_cm * cm) - 2.0*cm
    c.setFont("Times-Roman", 10)
    c.setFillColor(HexColor('#555555'))
    date_text = get_current_date_text(certificado.fecha_curso)
    c.drawRightString(width - 3.5*cm, date_y, date_text)


