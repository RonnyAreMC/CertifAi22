import pandas as pd
from django.db import transaction
from core.models import LoteCertificados, Certificado
import uuid
from core.validators import validate_file_content, sanitize_text

def procesar_archivo_excel_lote_business(lote_id):
    """
    Business logic to process an Excel file for a Lote.
    Uses atomic transactions to ensure data integrity: either all certificates are created, or none.
    """
    try:
        with transaction.atomic():
            lote = LoteCertificados.objects.select_for_update().get(id=lote_id)
            file_path = lote.archivo_excel.path
            
            # Read Excel (Force all to string to avoid auto-formatting issues)
            df = pd.read_excel(file_path, dtype=str)
            
            # Normalize headers
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            created_count = 0
            nombre_lote_upper = lote.nombre_lote.upper().strip()
            curso_context = f"POR ASISTIR AL SEMINARIO {nombre_lote_upper}"
            
            # ---------------------------------------------------------
            # Column Mapping Logic (Robust)
            # ---------------------------------------------------------
            col_cedula = None
            col_nombres = None
            col_email = None
            
            for c in df.columns:
                # Name
                if not col_nombres and ('nombre' in c and 'completo' in c): col_nombres = c
                elif not col_nombres and 'participante' in c: col_nombres = c
                elif not col_nombres and 'nombres' in c: col_nombres = c
                
                # Email
                if not col_email and ('correo' in c or 'email' in c): col_email = c
                
                # ID
                if not col_cedula and 'cedula' in c: col_cedula = c
                elif not col_cedula and 'identidad' in c: col_cedula = c
                elif not col_cedula and 'dni' in c: col_cedula = c
                
            # Fallback for ID (Phone/Cell if no ID)
            if not col_cedula:
                for c in df.columns:
                    if 'celular' in c or 'movil' in c or 'telf' in c or 'telefono' in c:
                        col_cedula = c
                        break
            
            # ---------------------------------------------------------
            # Row Processing
            # ---------------------------------------------------------
            certificates_to_create = []
            
            for index, row in df.iterrows():
                # Extract and Sanitize
                nombre_raw = sanitize_text(str(row.get(col_nombres, ''))) if col_nombres else ""
                email_raw = sanitize_text(str(row.get(col_email, ''))) if col_email else ""
                cedula_raw = sanitize_text(str(row.get(col_cedula, ''))) if col_cedula else ""
                
                # Handle Pandas NaNs converted to string
                if nombre_raw.lower() == 'nan': nombre_raw = ""
                if email_raw.lower() == 'nan': email_raw = ""
                if cedula_raw.lower() == 'nan': cedula_raw = ""
                
                # Skip empty rows
                if not nombre_raw and not email_raw and not cedula_raw:
                    continue
                
                # Clean ID
                cedula = cedula_raw
                if cedula.endswith('.0'): cedula = cedula[:-2]
                
                if not cedula:
                     # Generate fallback ID if missing
                    cedula = f"GEN-{uuid.uuid4().hex[:8].upper()}"

                # Name Parsing
                nombres = "PARTICIPANTE"
                apellidos = "S/N"
                
                if nombre_raw:
                    parts = nombre_raw.split()
                    if len(parts) >= 2:
                        if len(parts) == 2:
                            nombres = parts[0]
                            apellidos = parts[1]
                        elif len(parts) == 3:
                            nombres = parts[0]
                            apellidos = f"{parts[1]} {parts[2]}"
                        else: # 4+
                            mid = len(parts) // 2
                            nombres = " ".join(parts[:mid])
                            apellidos = " ".join(parts[mid:])
                    else:
                        nombres = nombre_raw

                # Email Fallback
                final_email = email_raw if email_raw else f"sin_correo_{uuid.uuid4().hex[:6]}@unemi.edu.ec"
                
                # Add to bulk list
                certificates_to_create.append(Certificado(
                    lote=lote,
                    cedula=cedula,
                    nombres=nombres.upper(),
                    apellidos=apellidos.upper(),
                    email=final_email,
                    curso=curso_context,
                    hash_verificacion=uuid.uuid4()
                ))
                created_count += 1
            
            # Bulk Create for performance
            if certificates_to_create:
                Certificado.objects.bulk_create(certificates_to_create)
                
            return True, f"Se procesaron {created_count} participantes exitosamente."

    except Exception as e:
        # Atomic block will auto-rollback here
        print(f"Error processing Excel in business layer: {e}")
        return False, str(e)


# English alias for clean imports
process_excel_batch = procesar_archivo_excel_lote_business
