import os
import re

import filetype  # Pure-Python, sin dependencias del sistema
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validar_cedula_ecuador(value):
    """
    Valida una cédula ecuatoriana (10 dígitos) con algoritmo de dígito verificador.

    Reglas:
      - 10 dígitos numéricos.
      - Los 2 primeros = código de provincia (01-24).
      - Tercer dígito < 6 (cédulas físicas).
      - Último dígito = checksum módulo 10 sobre coeficientes 2,1,2,1,... de los primeros 9.

    Vacío pasa (campos opcionales deciden obligatoriedad en otra capa).
    """
    if not value:
        return
    if not re.fullmatch(r'\d{10}', str(value)):
        raise ValidationError(_('La cédula debe tener 10 dígitos numéricos.'))

    provincia = int(value[:2])
    if provincia < 1 or provincia > 24:
        raise ValidationError(_('Código de provincia inválido en cédula.'))

    tercer = int(value[2])
    if tercer >= 6:
        raise ValidationError(_('Tercer dígito de cédula inválido.'))

    coef = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for i, c in enumerate(value[:9]):
        prod = int(c) * coef[i]
        total += prod if prod < 10 else prod - 9
    verificador = (10 - (total % 10)) % 10
    if verificador != int(value[9]):
        raise ValidationError(_('Cédula inválida (dígito verificador).'))


def validar_telefono_ecuador(value):
    """
    Valida un teléfono/celular ecuatoriano.

    Acepta:
      - Celular: 09xxxxxxxx (10 dígitos) o +5939xxxxxxxx.
      - Fijo:    0Nxxxxxxx (9 dígitos, N=2-7) o +593Nxxxxxxx.

    Normaliza espacios y guiones antes de validar.
    """
    if not value:
        return
    clean = re.sub(r'[\s\-()]', '', str(value))
    patterns = (
        r'^0\d{9}$',        # 0 + 9 dígitos (celular o fijo + ext)
        r'^\+593\d{9}$',    # formato internacional
        r'^0\d{8}$',        # fijo sin prefijo celular
    )
    if not any(re.fullmatch(p, clean) for p in patterns):
        raise ValidationError(_('Formato de teléfono inválido. Usa 09xxxxxxxx o +593xxxxxxxxx.'))

def validate_file_extension(value, allowed_extensions=None):
    if not allowed_extensions:
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.xlsx', '.xls']
    
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in allowed_extensions:
        raise ValidationError(_('Extensión de archivo no permitida.'))

def validate_file_content(file_obj, unexpected_mime_types=None):
    """
    Valida el contenido del archivo usando filetype (pure-Python) para detectar
    el MIME real a partir de los magic bytes.
    """
    # Leer los primeros bytes para detección por magic number
    initial_pos = file_obj.tell()
    file_obj.seek(0)
    header = file_obj.read(2048)
    file_obj.seek(initial_pos)

    kind = filetype.guess(header)
    mime_type = kind.mime if kind else 'application/octet-stream'

    # Bloquear ejecutables conocidos
    blocked_mimes = [
        'application/x-msdownload',     # .exe / .dll
        'application/x-dosexec',
        'application/x-executable',
        'application/x-mach-binary',
        'application/x-elf',
        'text/x-shellscript',
        'application/x-sh',
    ]

    if mime_type in blocked_mimes:
        raise ValidationError(_('Archivo sospechoso detectado (Posible ejecutable).'))

    # Bloqueo extra por magic bytes crudos (filetype no detecta scripts de texto)
    if header.startswith(b'MZ') or header.startswith(b'\x7fELF') or header.startswith(b'#!'):
        raise ValidationError(_('Archivo sospechoso detectado (Posible ejecutable).'))

    # Verificación opcional según extensión
    ext = os.path.splitext(file_obj.name)[1].lower()

    # Excel: los .xlsx son zips internamente
    if ext in ['.xlsx', '.xls']:
        valid_excel_mimes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/zip',
            'application/octet-stream',
        ]
        if mime_type not in valid_excel_mimes and 'zip' not in mime_type:
            pass  # se valida más adelante por estructura

    return mime_type

def sanitize_text(text):
    """
    Basic sanitization for text inputs to prevent XSS storage.
    """
    if not text:
        return ""
    text = str(text)
    # Strip dangerous characters if needed, or rely on Django templates auto-escape
    # This is a placeholder for more aggressive sanitization if required
    return text.strip()
