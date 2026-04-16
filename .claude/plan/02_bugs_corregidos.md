# Bugs Corregidos Antes del Refactor

Estos bugs estaban activos en produccion y se corrigieron como pre-requisito del refactor.

## Bug 1: Solo la plantilla geometrica funciona

### Sintoma

Todos los certificados salian con diseño geometrico, sin importar que plantilla tuviera el lote.

### Causa raiz

En `core/services/pdf_service.py`, la funcion `_apply_diseno_global(lote)` sobrescribe los campos de diseño del lote con los del singleton `DisenoGlobal` cuando `lote.personalizar_diseno = False`.

```python
# En DisenoGlobal: plantilla = 'geometrico'
# En cada Lote: personalizar_diseno = False (default)
# Resultado: todos usan geometrico
```

El toggle `personalizar_diseno` nunca se activa automaticamente, y los admins no saben que deben activarlo manualmente para que sus cambios tengan efecto.

### Fix aplicado

En `admin_panel/views.py -> configure_batch()`:

- Si el admin elige una plantilla distinta al diseño global -> `personalizar_diseno = True` automaticamente
- Si cambia un color que difiere del global -> `personalizar_diseno = True` automaticamente

Asi la UX es intuitiva: si el admin toca algo del diseño del lote, el lote queda personalizado sin necesidad de un toggle manual.

---

## Bug 2: No se pueden cambiar colores en plantilla clasica

### Sintoma

Al cambiar colores en un lote con plantilla clasica, los cambios no se reflejaban en el PDF.

### Causa raiz

En `pdf_service.py -> generate_certificate_pdf()`:

```python
if plantilla != 'clasico':
    # aplicar colors custom
```

El comentario decia "Classic must be standard" (version legacy), pero esto impide cambiar colores incluso cuando el admin personaliza el lote.

### Fix aplicado

Eliminada la restriccion. Todas las plantillas ahora respetan los colores custom del lote (`color_primario`, `color_secundario`, `color_terciario`, `color_texto`).

---

## Bug 3 (previamente corregido): Certificado muestra correo en vez de nombre del seminario

### Sintoma

Usuarios reportaban que en el cuerpo del certificado aparecia su correo o nombre, no el nombre del seminario. Ejemplo: *"Por su participacion en el seminario 'AMOROCHOE2@UNEMI.EDU.EC'"*.

### Causa raiz

El campo `Certificado.curso` tenia datos corruptos por mal mapeo de columnas en uploads previos de Excel.

### Fix aplicado

En las 5 plantillas PDF, el placeholder `{curso}` ahora se reemplaza con `certificado.lote.nombre_lote.upper()` (fuente confiable) en vez de `certificado.curso` (campo potencialmente corrupto).

Los PDFs se generan dinamicamente, por lo que el fix aplica a todos los certificados existentes sin necesidad de migracion de datos.

---

## Bug 4 (previamente corregido): Participantes duplicados

### Sintoma

Misma persona aparecia 2+ veces en busquedas, con mismo correo y cedula.

### Causa raiz

La funcion `add_certificate` del admin panel creaba `Certificado` sin crear/vincular un `Participante`. Cuando la misma persona se agregaba por Excel, el flujo Excel creaba un nuevo Participante.

### Fix aplicado

1. `add_certificate` ahora busca/crea Participante con deduplicacion (cedula primero, email despues).
2. Nuevo `UniqueConstraint` en email de Participante (condicional a no-vacio).
3. Migracion 0037 fusiona duplicados existentes y vincula certificados huerfanos.
4. Migracion 0038 aplica el constraint unico.

---

## Bug 5 (previamente corregido): Descarga PDF muestra siempre el mismo archivo

### Sintoma

Al descargar varios certificados del mismo usuario, el navegador mostraba siempre el mismo archivo.

### Causa raiz

- Filename `Certificado_{cedula}.pdf` identico para todos los certificados del mismo usuario
- Sin headers `Cache-Control`, el navegador cacheaba el primero

### Fix aplicado

- Filename ahora incluye curso + hash: `Certificado_{cedula}_{curso}_{hash8}.pdf`
- Headers `Cache-Control: no-store`, `Pragma: no-cache`, `Expires: 0`
- En ZIP bulk, sufijo numerico si dos certs producen el mismo nombre base

---

## Verificacion post-fix

Despues de aplicar los fixes, el sistema fue verificado con:

```bash
python manage.py check
# System check identified no issues (0 silenced).
```

Los fixes NO requieren migraciones nuevas y NO rompen datos existentes.
