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


def draw_signatures(c, certificado, width, y_position, color='#000000'):
    signatures = []
    lote = certificado.lote
    if lote.nombre_firma_1: signatures.append({'name': lote.nombre_firma_1, 'cargo': lote.cargo_firma_1, 'img': lote.imagen_firma_1})
    if lote.nombre_firma_2: signatures.append({'name': lote.nombre_firma_2, 'cargo': lote.cargo_firma_2, 'img': lote.imagen_firma_2})
    if lote.nombre_firma_3: signatures.append({'name': lote.nombre_firma_3, 'cargo': lote.cargo_firma_3, 'img': lote.imagen_firma_3})
    if lote.nombre_firma_4: signatures.append({'name': lote.nombre_firma_4, 'cargo': lote.cargo_firma_4, 'img': lote.imagen_firma_4})
    
    count = len(signatures) or 1
    # Distribute broadly
    section_width = (width - 4*cm) / count 
    margin_left = 2*cm

    for i, sig in enumerate(signatures):
        center_x = margin_left + (i * section_width) + (section_width / 2)
        
        # Line
        c.setStrokeColor(hex2rgb(color))
        c.setLineWidth(0.5)
        c.line(center_x - 3*cm, y_position, center_x + 3*cm, y_position)
        
        # Signature Image (Base64)
        if sig['img']:
            try:
                img_base64 = sig['img']
                # Fix padding if necessary
                missing_padding = len(img_base64) % 4
                if missing_padding:
                    img_base64 += '=' * (4 - missing_padding)
                    
                image_data = base64.b64decode(img_base64)
                image_stream = BytesIO(image_data)
                img_reader = ImageReader(image_stream)
                
                # Draw above line
                c.drawImage(img_reader, center_x - 2*cm, y_position + 0.2*cm, width=4*cm, height=2*cm, mask='auto', preserveAspectRatio=True)
            except Exception as e:
                print(f"Error drawing signature: {e}")
                pass

        # Name & Cargo
        c.setFont("Helvetica", 10) # Name Normal
        c.setFillColor(HexColor('#000000'))
        c.drawCentredString(center_x, y_position - 0.5*cm, sig['name'].upper())
        c.setFont("Helvetica-Bold", 8) # Cargo Bold
        c.drawCentredString(center_x, y_position - 0.9*cm, sig['cargo'].upper())

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
    # The reference shows overlapping rotated rounded rectangles in shades of blue/teal
    
    c.saveState()
    # Clipping to left side to avoid shapes spilling too far right
    # But the reference implies they are the sidebar.
    
    # 1. Base Sidebar Color (Deepest)
    c.setFillColor(pri)
    c.rect(0, 0, 3.5*cm, height, fill=1, stroke=0)
    
    # 2. Rotated Squares Pattern
    # We'll use 2-3 large rotated rounded rects to create the "wave" look
    
    # Shape 1 (Top Left - Dark)
    c.setFillColor(pri) 
    c.saveState()
    c.translate(0, height)
    c.rotate(-45)
    c.roundRect(-2*cm, -5*cm, 10*cm, 10*cm, 1*cm, fill=1, stroke=0)
    c.restoreState()
    
    # Shape 2 (Middle - Lighter opacity/tint)
    # We need a lighter version of Pri or just opacity
    c.setFillColor(pri, alpha=0.7) 
    c.saveState()
    c.translate(0, height * 0.55)
    c.rotate(-45)
    c.roundRect(-4*cm, -5*cm, 11*cm, 11*cm, 1.5*cm, fill=1, stroke=0)
    c.restoreState()
    
    # Shape 3 (Bottom - Dark again)
    c.setFillColor(pri)
    c.saveState()
    c.translate(0, 0)
    c.rotate(-45)
    c.roundRect(-2*cm, -3*cm, 12*cm, 12*cm, 1*cm, fill=1, stroke=0)
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
    
    body = certificado.lote.cuerpo_certificado.replace("{curso}", certificado.curso.upper()).replace("{horas}", str(certificado.horas))
    from textwrap import wrap
    lines = wrap(body, width=75)
    
    for line in lines:
        c.drawCentredString(center_x, y_cursor, line)
        y_cursor -= 6*mm
        
    y_cursor -= 8*mm
    
    # 6. Date (Gold)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(sec)
    c.drawCentredString(center_x, y_cursor, get_current_date_text(certificado.fecha_curso))
    
    y_cursor -= 2.5*cm
    
    # 7. Signatures & Footer
    # Reference shows signatures at bottom with central element
    
    # Draw Signatures
    # We'll use custom positioning here
    sig_y = y_cursor
    
    signatures = []
    if lote.nombre_firma_1: signatures.append({'name': lote.nombre_firma_1, 'cargo': lote.cargo_firma_1, 'img': lote.imagen_firma_1})
    if lote.nombre_firma_2: signatures.append({'name': lote.nombre_firma_2, 'cargo': lote.cargo_firma_2, 'img': lote.imagen_firma_2})
    
    # We can handle more, but reference implies 2 with central divider/icon
    
    if len(signatures) > 0:
        # Calculate positions
        # If 2, left and right. 
        # Center decoration (Gold Wreath)
        
        # Draw Central Wreath/Icon
        c.saveState()
        c.translate(center_x, sig_y + 1*cm)
        c.setFillColor(sec, alpha=0.2)
        c.circle(0,0, 1.2*cm, fill=1, stroke=0)
        c.setFont("Times-Bold", 24)
        c.setFillColor(sec)
        # Maybe a unicode laurel or just a circle
        c.restoreState()
        
        # Left Sig
        if len(signatures) >= 1:
            sig = signatures[0]
            sx = center_x - 5*cm
            c.setStrokeColor(sec); c.setLineWidth(1)
            c.line(sx - 2.5*cm, sig_y, sx + 2.5*cm, sig_y) # Gold Line
            c.setFont("Helvetica", 9); c.setFillColor(HexColor('#333333'))
            c.drawCentredString(sx, sig_y - 0.5*cm, sig['name'].upper())
            c.setFont("Helvetica-Bold", 7); c.setFillColor(HexColor('#777777'))
            c.drawCentredString(sx, sig_y - 0.9*cm, sig['cargo'].upper())
            # Img
            if sig['img']:
                try:
                    import base64; from io import BytesIO; from reportlab.lib.utils import ImageReader
                    d = base64.b64decode(sig['img'] + "===")
                    img = ImageReader(BytesIO(d))
                    c.drawImage(img, sx - 2*cm, sig_y + 0.2*cm, width=4*cm, height=2*cm, mask='auto', preserveAspectRatio=True)
                except: pass

        # Right Sig
        if len(signatures) >= 2:
            sig = signatures[1]
            sx = center_x + 5*cm
            c.setStrokeColor(sec); c.setLineWidth(1)
            c.line(sx - 2.5*cm, sig_y, sx + 2.5*cm, sig_y) # Gold Line
            c.setFont("Helvetica", 9); c.setFillColor(HexColor('#333333'))
            c.drawCentredString(sx, sig_y - 0.5*cm, sig['name'].upper())
            c.setFont("Helvetica-Bold", 7); c.setFillColor(HexColor('#777777'))
            c.drawCentredString(sx, sig_y - 0.9*cm, sig['cargo'].upper())
            # Img
            if sig['img']:
                try:
                    import base64; from io import BytesIO; from reportlab.lib.utils import ImageReader
                    d = base64.b64decode(sig['img'] + "===")
                    img = ImageReader(BytesIO(d))
                    c.drawImage(img, sx - 2*cm, sig_y + 0.2*cm, width=4*cm, height=2*cm, mask='auto', preserveAspectRatio=True)
                except: pass

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
    
    # 2. Bottom Right Decoration
    draw_hexagon(width, 0, 5*cm, pri, alpha=1.0)
    draw_hexagon(width - 4*cm, 1.5*cm, 2*cm, sec, stroke=True) # Outline
    
    # 3. Bottom Bar (UNEMI Style)
    # A thick bar at the very bottom
    bar_h = 1.2*cm
    c.setFillColor(pri)
    c.rect(0, 0, width * 0.4, bar_h/2, fill=1, stroke=0)
    c.setFillColor(sec)
    c.rect(width * 0.4, 0, width * 0.6, bar_h/2, fill=1, stroke=0)
    
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
    
    body = certificado.lote.cuerpo_certificado.replace("{curso}", certificado.curso.upper()).replace("{horas}", str(certificado.horas))
    
    # Center block
    from textwrap import wrap
    lines = wrap(body, width=80)
    for line in lines:
        c.drawCentredString(width/2, y_cursor, line)
        y_cursor -= 0.6*cm
        
    y_cursor -= 1.5*cm
    
    # 7. Date
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor('#555555'))
    c.drawCentredString(width/2, y_cursor, get_current_date_text(certificado.fecha_curso))
    
    # --- SIGNATURES ---
    # Bottom area, above the colored bar
    sig_y = 4*cm
    
    signatures = []
    if lote.nombre_firma_1: signatures.append({'name': lote.nombre_firma_1, 'cargo': lote.cargo_firma_1, 'img': lote.imagen_firma_1})
    if lote.nombre_firma_2: signatures.append({'name': lote.nombre_firma_2, 'cargo': lote.cargo_firma_2, 'img': lote.imagen_firma_2})
    if lote.nombre_firma_3: signatures.append({'name': lote.nombre_firma_3, 'cargo': lote.cargo_firma_3, 'img': lote.imagen_firma_3})
    
    num_sigs = len(signatures)
    if num_sigs > 0:
        spacing = width / (num_sigs + 1)
        for i, sig in enumerate(signatures):
            x_pos = spacing * (i + 1)
            
            # Img
            if sig['img']:
                try:
                    import base64; from io import BytesIO; from reportlab.lib.utils import ImageReader
                    d = base64.b64decode(sig['img'] + "===")
                    img = ImageReader(BytesIO(d))
                    c.drawImage(img, x_pos - 2*cm, sig_y + 0.5*cm, width=4*cm, height=2*cm, mask='auto', preserveAspectRatio=True)
                except: pass
                
            # Line
            c.setStrokeColor(HexColor('#444444'))
            c.line(x_pos - 2.5*cm, sig_y, x_pos + 2.5*cm, sig_y)
            
            # Text
            # Text
            c.setFont("Helvetica", 8) 
            c.setFillColor(HexColor('#000000'))
            c.drawCentredString(x_pos, sig_y - 0.4*cm, sig['name'].upper())
            c.setFont("Helvetica-Bold", 6)
            c.drawCentredString(x_pos, sig_y - 0.7*cm, sig['cargo'].upper())

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
    body = certificado.lote.cuerpo_certificado.replace("{curso}", certificado.curso.upper()).replace("{horas}", str(certificado.horas))
    
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


def generate_certificate_pdf(certificado):
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
            # if certificado.lote.color_terciario: ter = hex2rgb(certificado.lote.color_terciario) # Optional
            if certificado.lote.color_texto: txt = hex2rgb(certificado.lote.color_texto)
        except: pass
    
    # Dispatch Strategy
    if plantilla == 'moderno':
        draw_modern_wow(c, certificado, width, height, pri, sec, ter, txt)
    elif plantilla == 'geometrico':
        draw_geometric_wow(c, certificado, width, height, pri, sec, ter, txt)
    else:
        # Default / Clasico -> Always Standard Colors (as requested)
        draw_classic_wow(c, certificado, width, height, PR_DEF, SC_DEF, TR_DEF, TX_DEF)
    
    # Footer
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
    
    body = certificado.lote.cuerpo_certificado.replace("{curso}", certificado.curso.upper()).replace("{horas}", str(certificado.horas))
    from textwrap import wrap
    lines = wrap(body, width=75)
    
    for line in lines:
        c.drawCentredString(center_x, y_cursor, line)
        y_cursor -= 6*mm
    y_cursor -= 8*mm
    
    # 6. Date (bottom-right corner)
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(sec)
    c.drawRightString(width - 2.5*cm, 2.0*cm, get_current_date_text(certificado.fecha_curso))

    
    # 7. Signatures
    sig_y = y_cursor
    signatures = []
    if lote.nombre_firma_1: signatures.append({'name': lote.nombre_firma_1, 'cargo': lote.cargo_firma_1, 'img': lote.imagen_firma_1})
    if lote.nombre_firma_2: signatures.append({'name': lote.nombre_firma_2, 'cargo': lote.cargo_firma_2, 'img': lote.imagen_firma_2})
    
    if len(signatures) > 0:
        # Center signatures within content area
        count = len(signatures)
        content_area_width = width - margin_left
        spacing = content_area_width / (count + 1)
        
        for i, sig in enumerate(signatures):
            sx = margin_left + spacing * (i + 1)
            
            # Line
            c.setStrokeColor(sec); c.setLineWidth(1)
            c.line(sx - 2.5*cm, sig_y, sx + 2.5*cm, sig_y) 
            
            # Text (Fixed Fonts: Name Normal, Cargo Bold)
            c.setFont("Helvetica", 9); c.setFillColor(HexColor('#333333'))
            c.drawCentredString(sx, sig_y - 0.5*cm, sig['name'].upper())
            
            c.setFont("Helvetica-Bold", 7); c.setFillColor(HexColor('#777777'))
            c.drawCentredString(sx, sig_y - 0.9*cm, sig['cargo'].upper())
            
            # Img
            if sig['img']:
                try:
                    import base64; from io import BytesIO; from reportlab.lib.utils import ImageReader
                    d = base64.b64decode(sig['img'] + "===")
                    img = ImageReader(BytesIO(d))
                    c.drawImage(img, sx - 2*cm, sig_y + 0.2*cm, width=4*cm, height=2*cm, mask='auto', preserveAspectRatio=True)
                except: pass
        
        # OLD LOGIC REMOVED (Placeholder to consume the rest via next delete)
        #
        




def draw_geometric_wow(c, certificado, width, height, pri, sec, ter, txt):
    """
    Replica of 'Zuñiga' Reference:
    - Large UNEMI Watermark
    - Big Logos Top
    - Script Title 'Otorga el presente Reconocimiento' (Gold)
    - Corner Geometrics (Blue/Gold)
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
    # Attempt to set transparency for the image
    c.setFillAlpha(0.10) # Faded ("desenfocado")
    c.setStrokeAlpha(0.10)
    
    # Load Logo
    logo_watermark_path = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo-unemi-removebg-preview.png')
    
    if os.path.exists(logo_watermark_path):
        # "Zoom como pegado desde borde a borde" 
        # 1.5 was too much ("solo sale unem"). 
        # Reducing to 1.18 to cut padding but keep text.
        w_img = width * 1.18 
        h_img = w_img * 0.28 # slightly adjust aspect ratio
        x_img = (width - w_img) / 2 # Center it so sides flow off page
        y_img = -1.5*cm # Start lower to center vertically better
        
        c.drawImage(logo_watermark_path, x_img, y_img, width=w_img, height=h_img, mask='auto', preserveAspectRatio=True, anchor='c')
    
    c.restoreState()

    # --- 2. GEOMETRIC CORNERS (Professional Layered Chevrons - Compact) ---
    # Reference Step 1047: Complex "Arrow/Chevron" layers.
    # Scaled DOWN to avoid signature overlap.
    
    def draw_corner_professional(origin_x, origin_y, rotation, main_col, acc_col):
        c.saveState()
        c.translate(origin_x, origin_y)
        c.rotate(rotation)
        
        # 1. Base Layer (Large Dark Chevron)
        c.setFillColor(main_col)
        p1 = c.beginPath()
        p1.moveTo(0, 0)
        p1.lineTo(9.0*cm, 0)     # Reduced from 12
        p1.lineTo(7.5*cm, 3.0*cm) # Reduced/Tightened
        p1.lineTo(3.0*cm, 3.0*cm)
        p1.lineTo(0, 9.0*cm)     # Reduced from 12
        p1.close()
        c.drawPath(p1, fill=1, stroke=0)
        
        # 2. Gold Accent Chevron (Nested)
        c.setFillColor(acc_col)
        c.setStrokeColor(white)
        c.setLineWidth(3) # Thinner stroke for smaller shape
        
        p2 = c.beginPath()
        # Coordinates relative to rotation origin (corner)
        p2.moveTo(0, 0)
        p2.lineTo(5.5*cm, 0) # Reduced from 7
        p2.lineTo(0, 5.5*cm)
        p2.close()
        c.drawPath(p2, fill=1, stroke=1) 
        
        # 3. Floating "Satellite" Chevron (The "Cut" look)
        c.setFillColor(main_col)
        p3 = c.beginPath()
        # Adjusted positions for compact layout
        p3.moveTo(6.5*cm, 0.4*cm)
        p3.lineTo(9.0*cm, 0.4*cm)
        p3.lineTo(7.5*cm, 2.6*cm)
        p3.lineTo(5.5*cm, 2.6*cm)
        p3.close()
        c.drawPath(p3, fill=1, stroke=1)
        
        c.restoreState()

    # Apply Professional Corners
    # Bottom Left: Blue Base, Gold Accent
    draw_corner_professional(0, 0, 0, pri, sec)
    
    # Top Right: Gold Base, Blue Accent? Or Keep Symmetric Style with color swap?
    # Reference implies symmetry in shape, possibly assymetry in color.
    # Let's do Gold Base, Blue Accent for Top Right to maintain the accepted color scheme.
    draw_corner_professional(width, height, 180, sec, pri)

    # --- 3. LOGOS (Strict Order: UNEMI - MUC - FEUE) ---
    logo_y = height - 5.2*cm
    logo_h = 4.0*cm
    logo_w = 6.0*cm
    gap = 0.8*cm    
    
    # Helper
    def get_l_path(f, d):
         p = f.path if (f and hasattr(f,'path')) else (f if isinstance(f, str) else None)
         if not p: p = os.path.join(settings.BASE_DIR, 'static', 'img', d)
         if not os.path.exists(p): p = os.path.join(settings.BASE_DIR, 'certify', 'static', 'img', d)
         return p if os.path.exists(p) else None

    logos_ordered = []
    logos_ordered.append(get_l_path(lote.logo_header_2, 'logo-unemi-removebg-preview.png'))
    logos_ordered.append(get_l_path(lote.logo_header_1, 'muc.png'))
    logos_ordered.append(get_l_path(lote.logo_header_3, 'feue.png'))
    
    logos_ordered = [l for l in logos_ordered if l]
    
    total_w = (len(logos_ordered) * logo_w) + ((len(logos_ordered)-1) * gap)
    cx = (width - total_w) / 2
    
    for path in logos_ordered:
        try:
             c.drawImage(path, cx, logo_y, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
        except: pass
        cx += (logo_w + gap)
    
    # --- 4. CONTENT ---
    center_x = width / 2
    
    # Signature area reserved at bottom (fixed)
    SIG_AREA_BOTTOM = 1.8*cm  # Bottom margin for signature text
    SIG_LINE_Y = 4.5*cm       # Where signature lines go
    DATE_Y = SIG_LINE_Y + 3.2*cm  # Date above signatures
    
    # Content starts below logos
    y_cursor = height - 7.2*cm
    # Content must end above the date
    content_bottom = DATE_Y + 1.0*cm
    
    # A. Title (Script)
    script_font_use = "Times-Italic"
    if "GreatVibes" in pdfmetrics.getRegisteredFontNames():
        script_font_use = "GreatVibes"
        
    c.setFont(script_font_use, 48) 
    c.setFillColor(sec) # Gold
    c.drawCentredString(center_x, y_cursor, "Otorga el presente Reconocimiento")
    y_cursor -= 2.2*cm
    
    # B. Name (Script/GreatVibes)
    c.setFont(script_font_use, 54)
    c.setFillColor(HexColor('#222222'))
    nombre = f"{certificado.nombres} {certificado.apellidos}".title()
    c.drawCentredString(center_x, y_cursor, nombre)
    y_cursor -= 2.5*cm
    
    # C. Body Text (Dynamic sizing based on content length)
    body = certificado.lote.cuerpo_certificado.replace("{curso}", certificado.curso.upper()).replace("{horas}", str(certificado.horas))
    from textwrap import wrap
    
    # Calculate available space for body
    available_body_height = y_cursor - content_bottom
    
    # Try normal size first, reduce if too many lines
    body_font_size = 16
    line_spacing = 0.75*cm
    wrap_width = 70
    lines = wrap(body, width=wrap_width)
    
    # If text doesn't fit, reduce size
    needed_height = len(lines) * line_spacing
    if needed_height > available_body_height:
        body_font_size = 13
        line_spacing = 0.65*cm
        wrap_width = 85
        lines = wrap(body, width=wrap_width)
    
    c.setFont("Helvetica", body_font_size) 
    c.setFillColor(HexColor('#444444'))
    
    for line in lines:
        c.drawCentredString(center_x, y_cursor, line)
        y_cursor -= line_spacing
    
    # D. Date (bottom-right corner)
    c.setFont("Helvetica-Bold", 12) 
    c.setFillColor(HexColor('#555555'))
    date_text = get_current_date_text(certificado.fecha_curso).upper()
    c.drawRightString(width - 2.5*cm, 2.0*cm, date_text)
    
    # --- 5. SIGNATURES ---
    signatures = []
    if lote.nombre_firma_1: signatures.append({'name': lote.nombre_firma_1, 'cargo': lote.cargo_firma_1, 'img': lote.imagen_firma_1})
    if lote.nombre_firma_2: signatures.append({'name': lote.nombre_firma_2, 'cargo': lote.cargo_firma_2, 'img': lote.imagen_firma_2})
    if lote.nombre_firma_3: signatures.append({'name': lote.nombre_firma_3, 'cargo': lote.cargo_firma_3, 'img': lote.imagen_firma_3})
    if lote.nombre_firma_4: signatures.append({'name': lote.nombre_firma_4, 'cargo': lote.cargo_firma_4, 'img': lote.imagen_firma_4})
    
    num = len(signatures)
    
    # Helper to draw single signature
    def draw_single_sig(cx, cy, sig_data):
        # Img
        if sig_data['img']:
            try:
                import base64; from io import BytesIO; from reportlab.lib.utils import ImageReader
                d = base64.b64decode(sig_data['img'] + "===")
                img = ImageReader(BytesIO(d))
                c.drawImage(img, cx - 2*cm, cy + 0.2*cm, width=4*cm, height=1.8*cm, mask='auto', preserveAspectRatio=True)
            except: pass
        
        # Line
        c.setStrokeColor(HexColor('#000000'))
        c.setLineWidth(1)
        c.line(cx - 2.5*cm, cy, cx + 2.5*cm, cy)
        
        # Text
        c.setFont("Helvetica", 9) # Name Normal
        c.setFillColor(HexColor('#000000'))
        c.drawCentredString(cx, cy - 0.4*cm, sig_data['name'].upper())
        c.setFont("Helvetica-Bold", 8) # Cargo Bold
        c.drawCentredString(cx, cy - 0.8*cm, sig_data['cargo'].upper())

    if num == 4:
        # GRID LAYOUT (2x2)
        y_top = 4.8*cm
        draw_single_sig(width * 0.33, y_top, signatures[0])
        draw_single_sig(width * 0.66, y_top, signatures[1])
        y_bot = 2.0*cm
        draw_single_sig(width * 0.33, y_bot, signatures[2])
        draw_single_sig(width * 0.66, y_bot, signatures[3])
        
    elif num > 0:
        # SINGLE ROW LAYOUT (1, 2, or 3) - centered
        w_zone = width / (num + 1)
        for i, sig in enumerate(signatures):
            px = w_zone * (i + 1)
            draw_single_sig(px, SIG_LINE_Y, sig)
# FORCE RELOAD TRIGGER - Signature Fix Applied
