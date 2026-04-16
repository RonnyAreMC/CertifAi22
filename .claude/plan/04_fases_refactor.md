# Fases 0-4: Refactor Arquitectonico

Estas fases NO agregan features nuevos. Solo reorganizan codigo existente.

## Fase 0: Limpieza critica (2 horas)

### Objetivos
Eliminar codigo muerto y smells sin cambiar comportamiento.

### Tareas
- [ ] Eliminar funciones duplicadas en `pdf_service.py`:
  - `draw_modern_wow` (lineas 136 y 854 → mantener la mas reciente)
  - `draw_geometric_wow` (lineas 317 y 1014 → mantener la mas reciente)
- [ ] Remover imports no usados (usar `pyflakes` o `ruff`)
- [ ] En `email_service.py`, reemplazar `domain = "http://localhost:8000"` por `settings.SITE_URL`
- [ ] Consolidar `analyze_excel_headers` y `analyze_excel_file` (son equivalentes)
- [ ] Eliminar comentarios TODO/FIXME obsoletos

### Entregable
- `pdf_service.py` ~700 lineas menos
- `python manage.py check` pasa sin warnings
- Commit: `refactor: remove duplicate functions and dead code`

### Verificacion
```bash
python manage.py check
python manage.py test  # aun sin tests, pero no debe crashear
# Generar un certificado manualmente y verificar que sigue funcionando
```

---

## Fase 1: Estructura base (1 dia)

### Objetivos
Crear los fundamentos reutilizables antes de tocar lo demas.

### Tareas

#### 1.1 Crear `core/base/`

```python
# core/base/__init__.py
from .decorators import admin_required, superadmin_required, ajax_only
from .mixins import AdminRequiredMixin, SuperAdminRequiredMixin, AuditLogMixin
from .models import TimestampedModel, SingletonModel
```

```python
# core/base/decorators.py
from functools import wraps
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse

def _is_admin(u): return u.is_authenticated and u.is_staff
def _is_superadmin(u): return u.is_authenticated and u.is_superuser

def admin_required(view_func):
    return login_required(user_passes_test(_is_admin)(view_func))

def superadmin_required(view_func):
    return login_required(user_passes_test(_is_superadmin)(view_func))

def ajax_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX only'}, status=400)
        return view_func(request, *args, **kwargs)
    return wrapper
```

```python
# core/base/models.py
from django.db import models

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class SingletonModel(models.Model):
    """Base for singletons like DisenoGlobal."""
    class Meta:
        abstract = True

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
```

#### 1.2 Crear `core/helpers/`

```python
# core/helpers/text.py
import re
import unicodedata

def sanitize_text(text: str) -> str:
    """Remove dangerous chars but keep unicode."""
    if not text:
        return ''
    return re.sub(r'[\x00-\x1f\x7f]', '', text).strip()

def normalize_name(name: str) -> str:
    """Normalize name for comparison (remove accents, upper)."""
    name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode()
    return name.upper().strip()

def slugify_safe(text: str, max_len: int = 80) -> str:
    """Slugify with length limit and fallback."""
    from django.utils.text import slugify
    slug = slugify(text)[:max_len]
    return slug or 'sin-titulo'
```

```python
# core/helpers/http.py
def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    return xff.split(',')[0].strip() if xff else request.META.get('REMOTE_ADDR')

def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'
```

#### 1.3 Refactor gradual de decoradores

Reemplazar en `admin_panel/views.py`:
```python
# Antes
@login_required
@user_passes_test(_is_admin)
def mi_view(request): ...

# Despues
from core.base import admin_required

@admin_required
def mi_view(request): ...
```

**No tocar todo de una vez.** Hacerlo por dominio (todas las views de batch primero, luego session, etc.).

### Entregable
- `core/base/` funcional
- `core/helpers/` con utilities
- Al menos 10 views refactorizadas con `@admin_required`
- Commit: `feat: add core/base and core/helpers modules`

---

## Fase 2: Split pdf_service con Strategy pattern (2-3 dias)

### Objetivos
Separar 1,400 lineas en archivos manejables. Hacer que agregar una plantilla sea crear 1 archivo, no modificar el sistema.

### Tareas

#### 2.1 Crear base abstracta

```python
# core/services/pdf/base.py
from abc import ABC, abstractmethod
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm

class BasePDFDesign(ABC):
    """Interfaz comun para todas las plantillas de certificado."""

    # Metadatos de la plantilla (para registry)
    name: str = ''
    display_name: str = ''
    description: str = ''

    def __init__(self, certificado, canvas, colors):
        self.cert = certificado
        self.lote = certificado.lote
        self.c = canvas
        self.width, self.height = landscape(A4)
        self.colors = colors  # dict: pri, sec, ter, txt

    @abstractmethod
    def draw(self):
        """Render el certificado completo."""
        raise NotImplementedError

    def draw_verification_page(self):
        """Opcional: segunda pagina con QR."""
        pass

    # Metodos helper compartidos
    def get_curso_name(self) -> str:
        return self.lote.nombre_lote.upper()

    def get_body_text(self) -> str:
        curso = self.get_curso_name()
        horas = str(self.cert.horas or 0)
        return self.lote.cuerpo_certificado.replace("{curso}", curso).replace("{horas}", horas)

    def get_full_name(self) -> str:
        return f"{self.cert.nombres} {self.cert.apellidos}".title()
```

#### 2.2 Crear registry

```python
# core/services/pdf/designs/__init__.py
from .classic import ClassicDesign
from .modern import ModernDesign
from .geometric import GeometricDesign

DESIGN_REGISTRY = {
    'clasico': ClassicDesign,
    'moderno': ModernDesign,
    'geometrico': GeometricDesign,
}

def get_design_class(plantilla: str):
    return DESIGN_REGISTRY.get(plantilla, ClassicDesign)
```

#### 2.3 Migrar plantilla por plantilla

```python
# core/services/pdf/designs/classic.py
from ..base import BasePDFDesign

class ClassicDesign(BasePDFDesign):
    name = 'clasico'
    display_name = 'Clasico'
    description = 'Diseño elegante con marcos dorados'

    def draw(self):
        self._draw_background()
        self._draw_frames()
        self._draw_logos()
        self._draw_title()
        self._draw_name()
        self._draw_body()
        self._draw_date()
        self._draw_signatures()

    def _draw_frames(self):
        # codigo extraido de draw_classic_wow
        pass

    def _draw_logos(self):
        pass

    # ...etc, cada parte como metodo privado ordenado
```

#### 2.4 Componentes compartidos

```python
# core/services/pdf/components/signatures.py
def draw_signatures_bottom(canvas, lote, width, **opts):
    # Extraido del pdf_service.py original
    pass

def draw_geometric_signatures(canvas, lote, width, **opts):
    pass
```

#### 2.5 Orchestrator nuevo

```python
# core/services/pdf/generator.py
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from .designs import get_design_class
from .colors import build_colors_for_lote
from .fonts import register_fonts

def generate_certificate_pdf(certificado):
    # Aplicar diseño global (logica preservada)
    _apply_diseno_global(certificado.lote)
    register_fonts()

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    colors = build_colors_for_lote(certificado.lote)

    # Strategy dispatch
    DesignClass = get_design_class(certificado.lote.plantilla)
    design = DesignClass(certificado, c, colors)
    design.draw()

    # Segunda pagina si aplica
    if hasattr(design, 'draw_verification_page'):
        c.showPage()
        design.draw_verification_page()

    c.save()
    buffer.seek(0)
    return buffer
```

#### 2.6 Deprecar pdf_service.py

- Mantener como shim temporal que importa de `pdf/`:
```python
# core/services/pdf_service.py
"""DEPRECATED: usar core.services.pdf directamente."""
from .pdf.generator import generate_certificate_pdf
__all__ = ['generate_certificate_pdf']
```

- En un futuro release, eliminar este archivo.

### Entregable
- `core/services/pdf/` con diseños separados
- Tests manuales: generar 1 PDF de cada plantilla y visualizar
- Commit: `refactor: split pdf_service using strategy pattern`

---

## Fase 3: Split de views por dominio (1-2 dias)

### Objetivo
Convertir `admin_panel/views.py` (1,641 lineas) en `admin_panel/views/` con archivos por dominio.

### Tareas

```
admin_panel/
├── views.py          ← ELIMINAR al final
└── views/            ← NUEVO
    ├── __init__.py   # re-exporta todo (urls.py no cambia)
    ├── _shared.py    # helpers comunes de views (_log_audit, etc)
    ├── auth.py       # login, register, solicitudes
    ├── dashboard.py  # dashboard
    ├── batch.py      # CRUD lotes + Excel upload
    ├── certificate.py
    ├── session.py
    ├── design.py
    ├── landing.py
    ├── leaders.py
    ├── participants.py
    ├── users.py
    └── firmas.py     # merge de views_firmas.py
```

### Estrategia

1. Crear `admin_panel/views/__init__.py` vacio
2. Mover 1 grupo de views a la vez:
   - Mueves `batch.py`
   - Agregas `from .batch import *` en `__init__.py`
   - Corres tests y URLs, verificas
   - Repites para el siguiente grupo
3. Cuando todo este migrado, elimina `views.py`

### Para `public/views.py` (879 lineas) mismo approach:

```
public/views/
├── __init__.py
├── landing.py
├── search.py
├── attendance.py
├── session.py
└── verify.py
```

### Entregable
- Archivos de views de <400 lineas cada uno
- `urls.py` sin cambios
- Todos los tests pasan (los que haya)
- Commit: `refactor: split monolithic views into domain-specific modules`

---

## Fase 4: Managers y validaciones (1 dia)

### Objetivos
- Eliminar queries duplicadas
- Centralizar logica de busqueda/filtros
- Agregar validaciones en modelos

### Tareas

#### 4.1 Crear managers custom

```python
# core/managers/certificado.py
from django.db import models
from django.db.models import Q

class CertificadoQuerySet(models.QuerySet):
    def search(self, query: str):
        query = query.strip()
        if not query:
            return self.none()
        tokens = query.split()
        q = Q(cedula__icontains=query) | Q(email__icontains=query) | Q(hash_verificacion__iexact=query)
        for t in tokens:
            q |= Q(nombres__icontains=t) | Q(apellidos__icontains=t)
        return self.filter(q).distinct()

    def with_relations(self):
        return self.select_related('lote', 'participante')

    def downloaded(self):
        return self.filter(descargas_count__gt=0)

    def by_faculty(self, faculty_code: str):
        return self.filter(lote__facultad=faculty_code)

class CertificadoManager(models.Manager):
    def get_queryset(self):
        return CertificadoQuerySet(self.model, using=self._db)

    def search(self, q): return self.get_queryset().search(q)
    def downloaded(self): return self.get_queryset().downloaded()
```

#### 4.2 Registrar en modelo

```python
# core/models.py
from core.managers.certificado import CertificadoManager

class Certificado(models.Model):
    # ... campos ...
    objects = CertificadoManager()
```

#### 4.3 Uso en views

**Antes:**
```python
certs = Certificado.objects.filter(
    Q(cedula__icontains=q) | Q(email__icontains=q) | ...
).select_related('lote')
```

**Despues:**
```python
certs = Certificado.objects.search(q).with_relations()
```

#### 4.4 Hacer lo mismo para:
- ParticipanteManager (con fuzzy lookup helper)
- LoteManager (with_stats, active_only)
- SesionManager (upcoming, full, with_attendance)

#### 4.5 Validaciones en modelos

```python
# LoteCertificados.clean()
def clean(self):
    from django.core.exceptions import ValidationError
    # Si personalizar_diseno, verificar que tenga cuerpo
    if self.personalizar_diseno and not self.cuerpo_certificado:
        raise ValidationError('Un lote personalizado debe tener cuerpo de certificado.')
```

### Entregable
- 4 managers custom + querysets
- Views usando `Model.objects.search()` pattern
- Tests manuales de que las queries siguen devolviendo lo mismo
- Commit: `feat: add custom managers and querysets for domain logic`
