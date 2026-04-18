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
from .._signatures import draw_signatures_bottom
from .._logos import draw_smart_logos

def draw_modern_wow(c, certificado, width, height, pri, sec, ter, txt):
    """
    Modern Design 'Juliana' Style 
    """
    lote = certificado.lote
    register_fonts()
    
    # Fonts
    TITLE_FONT = "Times-Bold"      
    SUBTITLE_FONT = "Helvetica"    
    BODY_FONT = "Helvetica"
    SCRIPT_FONT = "Times-Italic" 
    try:
        pdfmetrics.getFont('GreatVibes')
        SCRIPT_FONT = 'GreatVibes'
    except: pass

    # --- SIDEBAR DECORATION ---
    c.saveState()
    # 1. Base Sidebar
    c.setFillColor(pri)
    c.rect(0, 0, 3.5*cm, height, fill=1, stroke=0)
    
    # 2. Rotated Squares (Patterns)
    c.setFillColor(pri) 
    c.saveState()
    c.translate(0, height)
    c.rotate(-45)
    c.roundRect(-2*cm, -5*cm, 10*cm, 10*cm, 1*cm, fill=1, stroke=0)
    c.restoreState()
    
    c.setFillColor(pri, alpha=0.7) 
    c.saveState()
    c.translate(0, height * 0.55)
    c.rotate(-45)
    c.roundRect(-4*cm, -5*cm, 11*cm, 11*cm, 1.5*cm, fill=1, stroke=0)
    c.restoreState()
    
    c.setFillColor(pri)
    c.saveState()
    c.translate(0, 0)
    c.rotate(-45)
    c.roundRect(-2*cm, -3*cm, 12*cm, 12*cm, 1*cm, fill=1, stroke=0)
    c.restoreState()
    c.restoreState()

    # --- GOLD SEAL ---
    seal_x = 4.5*cm
    seal_y = height - 4.5*cm
    seal_radius = 1.6*cm
    
    c.saveState()
    c.translate(seal_x, seal_y)
    
    # Ribbons
    c.setFillColor(sec)
    path_ribbon = c.beginPath()
    path_ribbon.moveTo(-0.8*cm, -1*cm); path_ribbon.lineTo(-1.2*cm, -3.5*cm); path_ribbon.lineTo(-0.6*cm, -2.8*cm); path_ribbon.lineTo(0, -3.5*cm); path_ribbon.lineTo(0, -1*cm); path_ribbon.close()
    
    path_ribbon2 = c.beginPath()
    path_ribbon2.moveTo(0.8*cm, -1*cm); path_ribbon2.lineTo(1.2*cm, -3.5*cm); path_ribbon2.lineTo(0.6*cm, -2.8*cm); path_ribbon2.lineTo(0, -3.5*cm); path_ribbon2.lineTo(0, -1*cm); path_ribbon2.close()
    
    c.drawPath(path_ribbon, fill=1, stroke=0)
    c.drawPath(path_ribbon2, fill=1, stroke=0)

    # Rosette
    c.setFillColor(sec) 
    import math
    points = 24
    outer_r = seal_radius; inner_r = seal_radius * 0.85
    p = c.beginPath()
    for i in range(2 * points + 1):
        angle = math.pi * i / points
        r = outer_r if i % 2 == 0 else inner_r
        x = r * math.cos(angle)
        y = r * math.sin(angle)
        if i == 0: p.moveTo(x, y)
        else: p.lineTo(x, y)
    p.close()
    c.drawPath(p, fill=1, stroke=0)
    
    c.setFillColor(white, alpha=0.3)
    c.circle(0,0, seal_radius*0.7, fill=1, stroke=0)
    c.setStrokeColor(white); c.setLineWidth(2)
    c.circle(0,0, seal_radius*0.6, fill=0, stroke=1)
    c.restoreState()


    # --- MAIN CONTENT ---
    margin_left = 6.5*cm 
    content_width = width - margin_left - 1.5*cm
    center_x = margin_left + (content_width / 2)
    
    # --- LOGOS (Smart Placement) ---
    # Top of content area
    logo_area_h = 2.5*cm
    # Draw logos centered in the content area top
    draw_smart_logos(c, lote, margin_left, height - 3*cm, content_width, 2.2*cm, align='center')
    
    y_cursor = height - 5*cm 

    # 1. Main Title
    c.setFont("Times-Bold", 42)
    c.setFillColor(HexColor('#111111'))
    c.drawCentredString(center_x, y_cursor, "CERTIFICADO")
    y_cursor -= 1.2*cm
    
    # 2. Subtitle
    c.setFont("Helvetica", 14)
    c.setFillColor(sec)
    c.drawCentredString(center_x, y_cursor, "DE RECONOCIMIENTO")
    y_cursor -= 1.5*cm
    
    # 3. Otorgado a
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(HexColor('#555555'))
    c.drawCentredString(center_x, y_cursor, "Otorgado a:")
    y_cursor -= 1.8*cm
    
    # 4. Name
    name_size = 52 if SCRIPT_FONT == 'GreatVibes' else 36
    c.setFont(SCRIPT_FONT, name_size)
    c.setFillColor(HexColor('#111111'))
    nombre = f"{certificado.nombres} {certificado.apellidos}".title()
    c.drawCentredString(center_x, y_cursor, nombre)
    
    c.setStrokeColor(sec); c.setLineWidth(1.5)
    name_width = c.stringWidth(nombre, SCRIPT_FONT, name_size)
    line_w = max(name_width * 1.2, 12*cm)
    c.line(center_x - line_w/2, y_cursor - 2, center_x + line_w/2, y_cursor - 2)
    y_cursor -= 2.2*cm
    
    # 5. Body
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor('#555555'))
    
    curso_name = certificado.lote.nombre_lote.upper()
    body = certificado.lote.cuerpo_certificado.replace("{curso}", curso_name).replace("{horas}", str(certificado.horas))
    from textwrap import wrap
    lines = wrap(body, width=75)
    
    for line in lines:
        c.drawCentredString(center_x, y_cursor, line)
        y_cursor -= 6*mm
    y_cursor -= 8*mm
    
    # 6. Date (bottom-right corner)
    c.setFont("Times-Italic", 13)
    c.setFillColor(HexColor('#777777'))
    c.drawRightString(width - 2.5*cm, 2.0*cm, get_current_date_text(certificado.fecha_curso))

    
    # 7. Signatures (desplazadas a la derecha del sidebar)
    draw_signatures_bottom(c, lote, width, name_color='#333333', cargo_color='#777777',
                           margin_left=margin_left, margin_right=1.5*cm)


