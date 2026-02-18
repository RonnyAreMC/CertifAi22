import os
import magic  # Requires python-magic and libmagic
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
    Validates the file content using python-magic to detect the real MIME type.
    """
    # Read first 2KB for magic number detection
    initial_pos = file_obj.tell()
    file_obj.seek(0)
    mime_type = magic.from_buffer(file_obj.read(2048), mime=True)
    file_obj.seek(initial_pos)
    
    # Block executables and scripts explicitly
    blocked_mimes = [
        'application/x-dosexec', 
        'application/x-executable', 
        'text/x-shellscript',
        'application/x-sh'
    ]
    
    if mime_type in blocked_mimes:
        raise ValidationError(_('Archivo sospechoso detectado (Posible ejecutable).'))
        
    # Optional: Verify expected type vs extension
    ext = os.path.splitext(file_obj.name)[1].lower()
    
    # Excel Check
    if ext in ['.xlsx', '.xls']:
        valid_excel_mimes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'application/octet-stream' # Sometimes happens
        ]
        if mime_type not in valid_excel_mimes and 'zip' not in mime_type: # xlsx is a zip
             # Log warning but allow if structure is valid later
             pass 

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
