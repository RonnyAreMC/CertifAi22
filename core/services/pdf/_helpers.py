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


