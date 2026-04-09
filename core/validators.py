import os
import filetype  # Pure-Python, sin dependencias del sistema
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

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
