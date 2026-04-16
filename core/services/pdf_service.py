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

def register_fonts():
    global _fonts_registered
    # if _fonts_registered:
    #     return
    try:
        # Strict path for self-contained app
        font_dir = os.path.join(settings.BASE_DIR, 'static', 'fonts')
        greatvibes_path = os.path.join(font_dir, 'GreatVibes-Regular.ttf')
        
        if os.path.exists(greatvibes_path):
            # print("DEBUG: Font file FOUND. Registering 'GreatVibes'...")
            pdfmetrics.registerFont(TTFont('GreatVibes', greatvibes_path))
            # print("DEBUG: Font 'GreatVibes' registered successfully.")
        
        _fonts_registered = True
    except Exception as e:
        # print(f"DEBUG: Error registering font: {e}")
        _fonts_registered = True

# --- HELPERS ---
def hex2rgb(hex_code):
    try:
        if not hex_code.startswith('#'):
            hex_code = '#' + hex_code
        return HexColor(hex_code)
    except:
        return HexColor('#000000')

def get_current_date_text(fecha_curso=None):
    fecha = fecha_curso if fecha_curso else datetime.now()
    meses_es = {1:'Enero', 2:'Febrero', 3:'Marzo', 4:'Abril', 5:'Mayo', 6:'Junio', 7:'Julio', 8:'Agosto', 9:'Septiembre', 10:'Octubre', 11:'Noviembre', 12:'Diciembre'}
    return f"Milagro, {fecha.day} de {meses_es.get(fecha.month, '')} del {fecha.year}"


def get_signatures_for_lote(lote):
    signatures = []
    for i in range(1, 5):
        firma_inst = getattr(lote, f'firma_inst_{i}')
        if firma_inst:
            signatures.append({
                'name': firma_inst.nombre,
                'cargo': firma_inst.cargo,
                'img': firma_inst.imagen
            })
        else:
            nombre = getattr(lote, f'nombre_firma_{i}')
            if nombre:
                signatures.append({
                    'name': nombre,
                    'cargo': getattr(lote, f'cargo_firma_{i}'),
                    'img': getattr(lote, f'imagen_firma_{i}')
                })
    return signatures


def draw_signatures_bottom(c, lote, width, line_color='#000000', name_color='#222222', cargo_color='#666666', margin_left=None, margin_right=None, sig_y=None):
    """
    Dibuja firmas en la zona inferior del certificado.
    Soporta 1, 2, 3 o 4 firmas distribuidas uniformemente.
    """
    signatures = get_signatures_for_lote(lote)
    num = len(signatures)
    if num == 0:
        return

    SIG_LINE_Y = sig_y if sig_y is not None else 3.8 * cm
    IMG_H = 1.8 * cm            # Alto de imagen de firma
    IMG_W = 3.5 * cm            # Ancho de imagen de firma
    LINE_HALF = 2.8 * cm        # Mitad de la línea de firma
    default_margin = 2.5 * cm
    left = margin_left if margin_left is not None else default_margin
    right = margin_right if margin_right is not None else default_margin

    usable = width - left - right
    spacing = usable / num

    for i, sig in enumerate(signatures):
        cx = left + spacing * i + spacing / 2

        # Imagen de firma (arriba de la línea)
        if sig.get('img'):
            try:
                img_b64 = sig['img']
                missing = len(img_b64) % 4
                if missing:
                    img_b64 += '=' * (4 - missing)
                img_data = base64.b64decode(img_b64)
                img_reader = ImageReader(BytesIO(img_data))
                c.drawImage(img_reader, cx - IMG_W / 2, SIG_LINE_Y + 0.15 * cm,
                            width=IMG_W, height=IMG_H, mask='auto', preserveAspectRatio=True)
            except:
                pass

        # Línea
        c.setStrokeColor(hex2rgb(line_color))
        c.setLineWidth(0.8)
        c.line(cx - LINE_HALF, SIG_LINE_Y, cx + LINE_HALF, SIG_LINE_Y)

        # Nombre
        name_size = 9 if num <= 3 else 7.5
        c.setFont("Times-Bold", name_size)
        c.setFillColor(hex2rgb(name_color))
        c.drawCentredString(cx, SIG_LINE_Y - 0.45 * cm, sig['name'].upper())

        # Cargo
        cargo_size = 7.5 if num <= 3 else 6.5
        c.setFont("Helvetica-Bold", cargo_size)
        c.setFillColor(hex2rgb(cargo_color))
        c.drawCentredString(cx, SIG_LINE_Y - 0.85 * cm, sig['cargo'].upper())


def draw_signatures(c, certificado, width, y_position, color='#000000'):
    """Legacy wrapper - redirige a draw_signatures_bottom."""
    draw_signatures_bottom(c, certificado.lote, width)

# --- STRATEGIES ---

def draw_modern_wow(c, certificado, width, height, pri, sec, ter, txt):
    """
    Modern Design 'Juliana' Style 
    - Geometric Sidebar (Rotated Rounded Squares)
    - Gold Accents & Seal
    - Serif Title, Gold Subtitle
    """
    lote = certificado.lote
    register_fonts()
    
    # Fonts
    TITLE_FONT = "Times-Bold"      # "CERTIFICADO"
    SUBTITLE_FONT = "Helvetica"    # "DE RECONOCIMIENTO"
    BODY_FONT = "Helvetica"
    SCRIPT_FONT = "Times-Italic" 
    try:
        pdfmetrics.getFont('GreatVibes')
        SCRIPT_FONT = 'GreatVibes'
    except: pass

    # --- SIDEBAR DECORATION (Geometric Shapes) ---
    # Clipped: no baja de 11cm para dejar firmas completamente libres

    c.saveState()
    clip_path = c.beginPath()
    clip_path.rect(0, 11*cm, 8*cm, height)
    c.clipPath(clip_path, stroke=0)

    # 1. Base Sidebar Color
    c.setFillColor(pri)
    c.rect(0, 0, 3.5*cm, height, fill=1, stroke=0)

    # Shape 1 (Top Left - Dark)
    c.setFillColor(pri)
    c.saveState()
    c.translate(0, height)
    c.rotate(-45)
    c.roundRect(-2*cm, -5*cm, 10*cm, 10*cm, 1*cm, fill=1, stroke=0)
    c.restoreState()

    # Shape 2 (Middle - Lighter)
    c.setFillColor(pri, alpha=0.7)
    c.saveState()
    c.translate(0, height * 0.55)
    c.rotate(-45)
    c.roundRect(-4*cm, -5*cm, 11*cm, 11*cm, 1.5*cm, fill=1, stroke=0)
    c.restoreState()

    c.restoreState()

    # --- GOLD SEAL (Top Left Intersection) ---
    # Vector simulation of the gold rosette
    seal_x = 4.5*cm
    seal_y = height - 4.5*cm
    seal_radius = 1.6*cm
    
    c.saveState()
    c.translate(seal_x, seal_y)
    
    # Golden Ribbons (Hanging down)
    c.setFillColor(sec) # Gold
    path_ribbon = c.beginPath()
    path_ribbon.moveTo(-0.8*cm, -1*cm)
    path_ribbon.lineTo(-1.2*cm, -3.5*cm)
    path_ribbon.lineTo(-0.6*cm, -2.8*cm) # Notch
    path_ribbon.lineTo(0, -3.5*cm)
    path_ribbon.lineTo(0, -1*cm)
    path_ribbon.close()
    
    # Mirror ribbon
    path_ribbon2 = c.beginPath()
    path_ribbon2.moveTo(0.8*cm, -1*cm)
    path_ribbon2.lineTo(1.2*cm, -3.5*cm)
    path_ribbon2.lineTo(0.6*cm, -2.8*cm)
    path_ribbon2.lineTo(0, -3.5*cm)
    path_ribbon2.lineTo(0, -1*cm)
    path_ribbon2.close()
    
    c.drawPath(path_ribbon, fill=1, stroke=0)
    c.drawPath(path_ribbon2, fill=1, stroke=0)

    # Rosette (Star/Flower shape)
    c.setFillColor(sec) 
    # Draw simple circle for now as base, maybe star later if needed. 
    # Reference shows a multi-pointed star/scalloped edge.
    import math
    points = 24
    outer_r = seal_radius
    inner_r = seal_radius * 0.85
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
    
    # Inner Circle (Lighter gold/Shiny)
    c.setFillColor(white, alpha=0.3)
    c.circle(0,0, seal_radius*0.7, fill=1, stroke=0)
    
    # Inner Ring
    c.setStrokeColor(white)
    c.setLineWidth(2)
    c.circle(0,0, seal_radius*0.6, fill=0, stroke=1)
    
    c.restoreState()


    # --- MAIN CONTENT ---
    margin_left = 6.5*cm # Clear the sidebar/seal
    content_width = width - margin_left - 1.5*cm
    center_x = margin_left + (content_width / 2)
    y_cursor = height - 5*cm # Start below top margin

    # 1. Main Title: "CERTIFICADO"
    c.setFont("Times-Bold", 42)
    c.setFillColor(HexColor('#111111')) # Almost Black
    c.drawCentredString(center_x, y_cursor, "CERTIFICADO")
    y_cursor -= 1.2*cm
    
    # 2. Subtitle: "DE RECONOCIMIENTO" (Gold)
    c.setFont("Helvetica", 14)
    c.setFillColor(sec) # Use Gold Color
    # c.setCharSpace(2) # Removed causing error
    c.drawCentredString(center_x, y_cursor, "DE RECONOCIMIENTO")
    # c.setCharSpace(0)
    y_cursor -= 1.5*cm
    
    # 3. Otorgado a
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(HexColor('#555555'))
    c.drawCentredString(center_x, y_cursor, "Otorgado a:")
    y_cursor -= 1.8*cm
    
    # 4. Name (Big Script)
    name_size = 52 if SCRIPT_FONT == 'GreatVibes' else 36
    c.setFont(SCRIPT_FONT, name_size)
    c.setFillColor(HexColor('#111111'))
    nombre = f"{certificado.nombres} {certificado.apellidos}".title()
    c.drawCentredString(center_x, y_cursor, nombre)
    
    # Underline (Gold)
    c.setStrokeColor(sec)
    c.setLineWidth(1.5)
    name_width = c.stringWidth(nombre, SCRIPT_FONT, name_size)
    line_w = max(name_width * 1.2, 12*cm)
    c.line(center_x - line_w/2, y_cursor - 2, center_x + line_w/2, y_cursor - 2)
    
    y_cursor -= 2.2*cm
    
    # 5. Body Text
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

    # 6. Date
    c.setFont("Times-Italic", 13)
    c.setFillColor(HexColor('#777777'))
    c.drawCentredString(center_x, y_cursor, get_current_date_text(certificado.fecha_curso))

    y_cursor -= 2.5*cm

    # 7. Signatures (fixed at bottom, desplazadas a la derecha del sidebar)
    draw_signatures_bottom(c, lote, width, name_color='#333333', cargo_color='#777777',
                           margin_left=margin_left)


def draw_geometric_wow(c, certificado, width, height, pri, sec, ter, txt):
    """
    Hybrid Design: Professional UNEMI Structure + Modern Geometric (Hexagons)
    """
    lote = certificado.lote
    register_fonts()
    
    # Fonts
    TITLE_FONT = "Helvetica-Bold"
    BODY_FONT = "Helvetica"
    
    # --- DECORATION: Hexagons & Gradient-ish Bars ---
    
    # helper for hexagon
    def draw_hexagon(x, y, radius, color, alpha=1.0, stroke=False):
        c.saveState()
        c.translate(x, y)
        c.setFillColor(color, alpha=alpha)
        c.setStrokeColor(color)
        import math
        p = c.beginPath()
        for i in range(6):
            angle = math.radians(60 * i)
            px = radius * math.cos(angle)
            py = radius * math.sin(angle)
            if i == 0: p.moveTo(px, py)
            else: p.lineTo(px, py)
        p.close()
        if stroke:
            c.setLineWidth(2)
            c.drawPath(p, fill=0, stroke=1)
        else:
            c.drawPath(p, fill=1, stroke=0)
        c.restoreState()

    # 1. Top Left Decoration (Hexagons)
    # Cluster of designs
    draw_hexagon(0, height, 4*cm, pri, alpha=1.0) # Big Dark Corner
    draw_hexagon(3.5*cm, height - 2*cm, 1.5*cm, sec, alpha=0.8) # Gold accent
    draw_hexagon(1*cm, height - 4.5*cm, 0.8*cm, pri, alpha=0.4) # Small echo
    
    # 2. Bottom Right Decoration (pequeño, no invade firmas)
    draw_hexagon(width + 1*cm, -1*cm, 3*cm, pri, alpha=0.8)
    draw_hexagon(width - 3*cm, 0.8*cm, 1.2*cm, sec, stroke=True) # Outline

    # 3. Bottom Bar (delgada, debajo de las firmas)
    c.setFillColor(pri)
    c.rect(0, 0, width * 0.4, 0.4*cm, fill=1, stroke=0)
    c.setFillColor(sec)
    c.rect(width * 0.4, 0, width * 0.6, 0.4*cm, fill=1, stroke=0)
    
    # --- HEADER ---
    # Top Left is busy with Hexagons, so let's push Header content slightly right or center.
    # UNEMI reference has Logo Top Left. Overlapping with shapes? 
    # Let's put Logos Top Right or Center to balance. 
    # Or floating white box if top left.
    
    header_y = height - 3*cm
    
    # Let's place logos top right to balance the top-left decoration
    logo_w = 4*cm
    logo_h = 2.2*cm
    
    # Helper to draw logo
    def draw_logo_img(field, x, y):
        try:
            path = field.path if hasattr(field, 'path') else str(field)
            if os.path.exists(path):
                c.drawImage(path, x, y, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
        except: pass

    # Draw Logos (Right Aligned)
    current_x = width - 2*cm - logo_w
    if lote.logo_header_3:
        draw_logo_img(lote.logo_header_3, current_x, header_y)
        current_x -= (logo_w + 1*cm)
        
    if lote.logo_header_2: # UNEMI usually
        draw_logo_img(lote.logo_header_2, current_x, header_y)
        current_x -= (logo_w + 1*cm)
        
    if lote.logo_header_1:
        draw_logo_img(lote.logo_header_1, current_x, header_y)

    # --- CONTENT ---
    # UNEMI Style: Left/Center aligned text hierarchy
    margin_left = 3*cm
    content_width = width - 2*margin_left
    
    y_cursor = height - 7*cm
    
    # 1. Main Org Title (Optional)
    # c.setFont("Helvetica-Bold", 16)
    # c.setFillColor(HexColor('#000000'))
    # c.drawString(margin_left, y_cursor, "VICERRECTORADO DE VINCULACIÓN")
    # y_cursor -= 1*cm
    
    # 2. "Confieres el presente"
    # c.setFont("Helvetica", 12)
    # c.setFillColor(HexColor('#555555'))
    # c.drawString(margin_left, y_cursor, "Confiere el presente")
    # y_cursor -= 1.5*cm
    
    # 3. "CERTIFICADO DE APROBACIÓN"
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(pri)
    c.drawCentredString(width/2, y_cursor, "CERTIFICADO")
    y_cursor -= 1*cm
    c.setFont("Helvetica", 14)
    c.setFillColor(sec)
    c.drawCentredString(width/2, y_cursor, "DE APROBACIÓN")
    y_cursor -= 2*cm
    
    # 4. "Otorgado a:"
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor('#666666'))
    c.drawCentredString(width/2, y_cursor, "Otorgado a:")
    y_cursor -= 1.5*cm
    
    # 5. Name
    c.setFont("Helvetica-Bold", 28)
    c.setFillColor(HexColor('#111111'))
    nombre = f"{certificado.nombres} {certificado.apellidos}".upper()
    c.drawCentredString(width/2, y_cursor, nombre)
    y_cursor -= 2*cm
    
    # 6. Body
    # "Por su aprobación al curso de..."
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor('#333333'))
    
    curso_name = certificado.lote.nombre_lote.upper()
    body = certificado.lote.cuerpo_certificado.replace("{curso}", curso_name).replace("{horas}", str(certificado.horas))

    # Center block
    from textwrap import wrap
    lines = wrap(body, width=80)
    for line in lines:
        c.drawCentredString(width/2, y_cursor, line)
        y_cursor -= 0.6*cm
        
    y_cursor -= 1.5*cm
    
    # 7. Date
    c.setFont("Times-Italic", 13)
    c.setFillColor(HexColor('#777777'))
    c.drawCentredString(width/2, y_cursor, get_current_date_text(certificado.fecha_curso))
    
    # --- SIGNATURES (fixed at bottom) ---
    draw_signatures_bottom(c, lote, width)

    # QR Code (Hybrid: UNEMI has it bottom right)
    # We'll put a placeholder box if we don't have QR logic here yet, or use the hash
    # Drawing a small box bottom right
    c.saveState()
    qr_size = 2.5*cm
    qr_x = width - qr_size - 1*cm
    qr_y = 2*cm
    # Placeholder for QR
    # c.setStrokeColor(HexColor('#000000'))
    # c.rect(qr_x, qr_y, qr_size, qr_size)
    # c.setFont("Helvetica", 6)
    # c.drawCentredString(qr_x + qr_size/2, qr_y - 0.3*cm, f"ID: {certificado.hash_verificacion}")
    c.restoreState()


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


def generate_certificate_pdf(certificado):
    # Aplicar diseño global (sobrescribe los campos del lote en memoria)
    _apply_diseno_global(certificado.lote)

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    plantilla = certificado.lote.plantilla
    
    # Default Colors (Classic Blue/Gold) - STRICT FOR CLASSIC
    PR_DEF = HexColor('#0B3D91')
    SC_DEF = HexColor('#D4AF37')
    TR_DEF = HexColor('#F3F4F6')
    TX_DEF = HexColor('#1c1c1c')

    # Assign Defaults initially
    pri, sec, ter, txt = PR_DEF, SC_DEF, TR_DEF, TX_DEF

    # ONLY Apply Custom Colors if NOT Classic (Classic must be standard)
    if plantilla != 'clasico': 
        try: 
            if certificado.lote.color_primario: pri = hex2rgb(certificado.lote.color_primario)
            if certificado.lote.color_secundario: sec = hex2rgb(certificado.lote.color_secundario)
            if certificado.lote.color_texto: txt = hex2rgb(certificado.lote.color_texto)
        except: pass
    
    # Dispatch Strategy
    if plantilla == 'moderno':
        draw_modern_wow(c, certificado, width, height, pri, sec, ter, txt)
    elif plantilla == 'geometrico':
        draw_geometric_wow(c, certificado, width, height, pri, sec, ter, txt)
        
        # --- SECOND PAGE: QR Verification ---
        c.showPage()
        _draw_geometric_verification_page(c, certificado, width, height, pri, sec)
    else:
        # Default / Clasico -> Always Standard Colors (as requested)
        draw_classic_wow(c, certificado, width, height, PR_DEF, SC_DEF, TR_DEF, TX_DEF)
    
    # Footer (only on first page for geometric since we handle 2nd page separately)
    if plantilla != 'geometrico':
        c.setFont("Helvetica", 6); c.setFillColor(HexColor('#999999'))
        validation_text = f"ID: {certificado.hash_verificacion} - Documento generado electrónicamente"
        c.drawCentredString(width/2, 0.8*cm, validation_text)
    
    c.save()
    buffer.seek(0)
    return buffer

# --- HELPER: SMART LOGOS ---
def draw_smart_logos(c, lote, x_start, y_start, max_w, max_h, align='center'):
    """
    Draws up to 3 logos (Lote or Defaults) in the given area.
    Smartly distributes them based on count and alignment.
    """
    # 1. Identify Sources
    # We want to force defaults if custom ones are missing, to ensure standard look
    # (Unless user specifically wants NO logo, but typically certificates need them)
    
    logos = []
    
    # helper to check and get path
    def get_path(field, default_name):
        path = None
        # Check custom
        if field:
             if hasattr(field, 'path'): path = field.path
             elif isinstance(field, str): path = field
        
        # Check default if no custom
        if not path or not os.path.exists(path):
            path = os.path.join(settings.BASE_DIR, 'static', 'img', default_name)
        
        if path and os.path.exists(path):
            return path
        return None

    # Load 3 slots
    l1 = get_path(lote.logo_header_1, 'muc.png')
    l2 = get_path(lote.logo_header_2, 'logo-unemi-removebg-preview.png')
    l3 = get_path(lote.logo_header_3, 'feue.png')
    
    # Filter valid ones
    active_logos = [l for l in [l1, l2, l3] if l]
    count = len(active_logos)
    
    if count == 0: return # Nothing to draw
    
    # 2. Calculate Positions
    logo_w = max_h * 1.8 # aspect ratio roughly
    # If logos are squarish, this might be too wide, but standard headers are usually wide.
    # Let's verify per image aspect ratio? For now fixed box is safer.
    
    # Spacing
    # If Center: Start from center of max_w
    # If Right: Start from right edge
    
    # Effective width needed
    gap = 1*cm
    total_w = (count * logo_w) + ((count - 1) * gap)
    
    start_x = x_start
    
    if align == 'center':
        start_x = x_start + (max_w - total_w) / 2
    elif align == 'right':
        start_x = x_start + max_w - total_w
    elif align == 'left':
        start_x = x_start
        
    # Draw
    current_x = start_x
    for path in active_logos:
        try:
            c.drawImage(path, current_x, y_start, width=logo_w, height=max_h, mask='auto', preserveAspectRatio=True)
        except: pass
        current_x += (logo_w + gap)


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


def _draw_geometric_signatures(c, lote, width, pri, sec, sig_y=None):
    """
    Firmas profesionales para la plantilla geométrica.
    - Imagen de firma centrada
    - Línea DEBAJO de la imagen (nunca cruza texto)
    - Nombre en Times-Bold (serif profesional)
    - Cargo en Times-Roman italic
    - Ordenado: imagen → línea → nombre → cargo
    """
    signatures = get_signatures_for_lote(lote)
    num = len(signatures)
    if num == 0:
        return

    BASE_LINE_Y = sig_y if sig_y is not None else 4.2*cm
    BASE_IMG_H = 2.0*cm
    BASE_IMG_W = 3.8*cm
    LINE_HALF = 3.2*cm

    margin_left = 3.0*cm
    margin_right = 3.0*cm
    usable = width - margin_left - margin_right
    spacing = usable / num

    for i, sig in enumerate(signatures):
        cx = margin_left + spacing * i + spacing / 2
        
        # Per-signature adjustments — ONLY affect the image, NOT the line/text
        sig_num = i + 1
        img_offset_y = getattr(lote, f'firma_{sig_num}_offset_y', 0) * cm
        escala = getattr(lote, f'firma_{sig_num}_escala', 100) / 100.0
        
        # Scale image dimensions
        img_h = BASE_IMG_H * escala
        img_w = BASE_IMG_W * escala

        # 1. Signature Image (above the line, position/size adjustable)
        if sig.get('img'):
            try:
                img_b64 = sig['img']
                missing = len(img_b64) % 4
                if missing:
                    img_b64 += '=' * (4 - missing)
                img_data = base64.b64decode(img_b64)
                img_reader = ImageReader(BytesIO(img_data))
                # Image Y = line + small gap + user offset
                img_y = BASE_LINE_Y + 0.15*cm + img_offset_y
                c.drawImage(img_reader, cx - img_w / 2, img_y,
                            width=img_w, height=img_h, mask='auto', preserveAspectRatio=True)
            except:
                pass

        # 2. Signature Line — FIXED position (gold accent with decorative ends)
        c.saveState()
        c.setStrokeColor(sec)
        c.setLineWidth(1.0)
        c.line(cx - LINE_HALF, BASE_LINE_Y, cx + LINE_HALF, BASE_LINE_Y)
        c.setFillColor(sec)
        c.circle(cx - LINE_HALF, BASE_LINE_Y, 1.5, fill=1, stroke=0)
        c.circle(cx + LINE_HALF, BASE_LINE_Y, 1.5, fill=1, stroke=0)
        c.restoreState()

        # 3. Name — FIXED below line
        name_text = sig['name'].strip()
        if name_text:
            name_size = 9.5 if num <= 3 else 8
            c.setFont("Times-Bold", name_size)
            c.setFillColor(HexColor('#1a1a1a'))
            c.drawCentredString(cx, BASE_LINE_Y - 0.5*cm, name_text)

        # 4. Cargo — FIXED below name
        cargo_text = sig.get('cargo', '').strip()
        if cargo_text:
            cargo_size = 8 if num <= 3 else 7
            c.setFont("Times-Italic", cargo_size)
            c.setFillColor(HexColor('#555555'))
            if len(cargo_text) > 30 and num >= 3:
                words = cargo_text.upper().split()
                mid = len(words) // 2
                line1 = ' '.join(words[:mid])
                line2 = ' '.join(words[mid:])
                c.drawCentredString(cx, BASE_LINE_Y - 0.9*cm, line1)
                c.drawCentredString(cx, BASE_LINE_Y - 1.25*cm, line2)
            else:
                c.drawCentredString(cx, BASE_LINE_Y - 0.9*cm, cargo_text.upper())


def _draw_geometric_verification_page(c, certificado, width, height, pri, sec):
    """
    Segunda página: Solo verificación con QR.
    Sin logos, sin nombre. Minimalista para que un empleador escanee.
    """
    lote = certificado.lote
    
    # --- GEOMETRIC CORNERS (smaller version) ---
    def draw_corner_mini(origin_x, origin_y, rotation, main_col, acc_col):
        c.saveState()
        c.translate(origin_x, origin_y)
        c.rotate(rotation)
        
        c.setFillColor(main_col)
        p1 = c.beginPath()
        p1.moveTo(0, 0)
        p1.lineTo(5.0*cm, 0)
        p1.lineTo(4.0*cm, 1.8*cm)
        p1.lineTo(1.8*cm, 1.8*cm)
        p1.lineTo(0, 5.0*cm)
        p1.close()
        c.drawPath(p1, fill=1, stroke=0)
        
        c.setFillColor(acc_col)
        c.setStrokeColor(white)
        c.setLineWidth(2)
        p2 = c.beginPath()
        p2.moveTo(0, 0)
        p2.lineTo(3.0*cm, 0)
        p2.lineTo(0, 3.0*cm)
        p2.close()
        c.drawPath(p2, fill=1, stroke=1)
        
        c.restoreState()

    draw_corner_mini(0, 0, 0, pri, sec)
    draw_corner_mini(width, height, 180, sec, pri)
    
    # --- Top/Bottom bars ---
    c.setFillColor(pri)
    c.rect(0, 0, width * 0.4, 0.3*cm, fill=1, stroke=0)
    c.setFillColor(sec)
    c.rect(width * 0.4, 0, width * 0.6, 0.3*cm, fill=1, stroke=0)
    c.setFillColor(sec)
    c.rect(0, height - 0.3*cm, width * 0.6, 0.3*cm, fill=1, stroke=0)
    c.setFillColor(pri)
    c.rect(width * 0.6, height - 0.3*cm, width * 0.4, 0.3*cm, fill=1, stroke=0)
    
    center_x = width / 2
    center_y = height / 2
    
    # --- QR CODE (centered, large) ---
    qr_size = 7.0*cm
    qr_drawn = False
    
    try:
        import qrcode
        from io import BytesIO as QRBytesIO
        
        base_url = getattr(settings, 'SITE_URL', 'https://muc-academy.up.railway.app')
        verify_url = f"{base_url}/verificar/{certificado.hash_verificacion}/"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=12,
            border=2,
        )
        qr.add_data(verify_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="#162054", back_color="white")
        
        qr_buffer = QRBytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        
        qr_reader = ImageReader(qr_buffer)
        qr_x = center_x - qr_size / 2
        qr_y = center_y - qr_size / 2 - 0.5*cm
        
        # QR background box with gold border
        c.saveState()
        c.setFillColor(HexColor('#FFFFFF'))
        c.setStrokeColor(sec)
        c.setLineWidth(2.5)
        padding = 0.5*cm
        c.roundRect(qr_x - padding, qr_y - padding, 
                    qr_size + 2*padding, qr_size + 2*padding, 
                    0.4*cm, fill=1, stroke=1)
        c.restoreState()
        
        c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size, mask='auto')
        qr_drawn = True
        
    except Exception:
        pass
    
    # --- Title above QR ---
    title_y = center_y + qr_size / 2 + 1.5*cm
    
    c.setFont("Times-Bold", 24)
    c.setFillColor(pri)
    c.drawCentredString(center_x, title_y + 1.2*cm, "VERIFICACIÓN DE CERTIFICADO")
    
    # Gold underline
    c.setStrokeColor(sec)
    c.setLineWidth(2)
    line_w = 12*cm
    c.line(center_x - line_w/2, title_y + 0.8*cm, center_x + line_w/2, title_y + 0.8*cm)
    
    # Subtitle
    c.setFont("Times-Roman", 12)
    c.setFillColor(HexColor('#555555'))
    c.drawCentredString(center_x, title_y, "Escanee el código QR para verificar la autenticidad de este certificado")
    
    # --- Text below QR ---
    info_y = center_y - qr_size / 2 - 1.8*cm
    
    c.setFont("Times-Roman", 11)
    c.setFillColor(HexColor('#444444'))
    c.drawCentredString(center_x, info_y, "Este código le redirigirá a una página segura donde podrá confirmar")
    c.drawCentredString(center_x, info_y - 0.5*cm, "que el titular participó en el evento o seminario certificado.")
    
    # Verification ID
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#999999'))
    c.drawCentredString(center_x, info_y - 1.5*cm, f"ID: {certificado.hash_verificacion}")
    
    # Footer text
    c.setFont("Times-Italic", 9)
    c.setFillColor(HexColor('#888888'))
    c.drawCentredString(center_x, 1.5*cm, "Documento generado electrónicamente — MUC Academy / Universidad Estatal de Milagro")


