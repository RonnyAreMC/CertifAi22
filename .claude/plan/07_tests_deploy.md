# Fase 13: Tests + Deploy + Produccion

## Objetivos

- Cobertura de tests suficiente para defender la tesis (~40-50%)
- Deploy en Railway con PostgreSQL (para pgvector)
- Variables de entorno documentadas
- Monitoreo basico

---

## Fase 13.1: Tests basicos (2 dias)

### Estructura

```
tests/
├── conftest.py                    # fixtures compartidos (pytest)
├── fixtures/
│   ├── sample_excel.xlsx
│   ├── participants_clean.json
│   ├── participants_dirty.json   # con duplicados
│   └── lotes_sample.json
├── unit/
│   ├── test_helpers.py            # text, http, files
│   ├── test_managers.py           # querysets custom
│   └── test_pdf_designs/
│       ├── test_classic.py
│       ├── test_modern.py
│       └── test_geometric.py
├── integration/
│   ├── test_excel_processing.py
│   ├── test_certificate_generation.py
│   └── test_duplicate_merge.py
├── api/
│   ├── test_auth.py
│   ├── test_participants_api.py
│   ├── test_certificates_api.py
│   └── test_sessions_api.py
└── ai/
    ├── test_copilot.py            # mocks
    ├── test_excel_mapper.py
    ├── test_voice_extraction.py
    └── test_recommender.py
```

### Dependencias

```txt
# requirements-dev.txt
pytest==8.3.3
pytest-django==4.9.0
pytest-cov==5.0.0
factory-boy==3.3.1
responses==0.25.3           # mock HTTP (para mocks de Claude/OpenAI)
```

### Setup pytest

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.development
python_files = tests.py test_*.py *_tests.py
testpaths = tests
addopts = --reuse-db --cov=core --cov=admin_panel --cov=public --cov=api --cov-report=term --cov-report=html
```

### Ejemplos criticos

#### Tests de PDF

```python
# tests/unit/test_pdf_designs/test_classic.py
import pytest
from io import BytesIO
from reportlab.pdfgen import canvas
from core.services.pdf.designs.classic import ClassicDesign
from tests.factories import CertificadoFactory

@pytest.mark.django_db
def test_classic_design_renders_without_errors():
    cert = CertificadoFactory()
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    colors = {'pri': '#000000', 'sec': '#FFFFFF', 'ter': '#CCCCCC', 'txt': '#333333'}
    design = ClassicDesign(cert, c, colors)
    design.draw()
    c.save()
    assert buffer.tell() > 1000  # al menos algo se escribio

@pytest.mark.django_db
def test_classic_uses_lote_nombre_not_curso():
    cert = CertificadoFactory(curso="datos-corruptos@email.com", lote__nombre_lote="Seminario X")
    design = ClassicDesign(cert, Mock(), {})
    assert design.get_curso_name() == "SEMINARIO X"
```

#### Tests de Excel

```python
# tests/integration/test_excel_processing.py
import pytest
from pathlib import Path
from core.services.excel.processor import procesar_archivo_excel_lote_business
from tests.factories import LoteFactory

@pytest.mark.django_db
def test_excel_creates_unique_participantes():
    lote = LoteFactory(archivo_excel=Path('tests/fixtures/sample_excel.xlsx'))
    ok, msg = procesar_archivo_excel_lote_business(lote.id)
    assert ok
    # Verificar que no hay duplicados
    from core.models import Participante
    emails = Participante.objects.values_list('email', flat=True)
    assert len(emails) == len(set(emails))
```

#### Tests de IA (mocks)

```python
# tests/ai/test_copilot.py
from unittest.mock import patch, MagicMock
from core.services.ai.copilot import generate_body_text

@patch('core.services.ai.copilot.call_claude')
def test_copilot_generates_with_variables(mock_claude):
    mock_claude.return_value = "Por participar en {curso} con {horas} horas academicas."
    result = generate_body_text(tipo_evento="seminario", tono="formal")
    assert "{curso}" in result['texto']
    assert "{horas}" in result['texto']

@patch('core.services.ai.copilot.call_claude')
def test_copilot_retries_if_missing_variables(mock_claude):
    # primera call sin variables, segunda con ellas
    mock_claude.side_effect = [
        "Texto sin placeholders",
        "Texto con {curso} y {horas}"
    ]
    result = generate_body_text(tipo_evento="seminario")
    assert mock_claude.call_count == 2
    assert "{curso}" in result['texto']
```

### Metricas objetivo

- Coverage total: ~40-50%
- Coverage de servicios criticos (pdf/, excel/, ai/): ~70%
- Al menos 1 test por cada endpoint API
- Al menos 1 test de integracion por cada flujo completo (crear lote → procesar Excel → generar certs)

---

## Fase 13.2: Configuracion de produccion (medio dia)

### Settings split

```python
# config/settings/__init__.py
import os
env = os.environ.get('DJANGO_ENV', 'development')
if env == 'production':
    from .production import *
else:
    from .development import *
```

```python
# config/settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')

# DB: PostgreSQL con pgvector
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ['DATABASE_URL'],
        conn_max_age=600,
        ssl_require=True
    )
}

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cache (Railway Redis o simple local)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.environ.get('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'core.services.ai': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
```

### Variables de entorno requeridas

```bash
# .env.example
DJANGO_ENV=production
DJANGO_SECRET_KEY=cambiar_en_produccion
DEBUG=False
ALLOWED_HOSTS=muc-academy.up.railway.app,tudominio.com
DATABASE_URL=postgres://...

# IA
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...
DEFAULT_FROM_EMAIL=noreply@unemi.edu.ec

# Site
SITE_URL=https://muc-academy.up.railway.app
```

### railway.json actualizado

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py rebuild_embeddings --only-missing && gunicorn config.wsgi --bind 0.0.0.0:$PORT --log-file -",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

---

## Fase 13.3: Migracion a PostgreSQL con pgvector (medio dia)

### Pasos

1. **Crear DB PostgreSQL en Railway**
   - Agregar plugin PostgreSQL desde dashboard
   - Copiar `DATABASE_URL` a las env vars del servicio Django

2. **Instalar extension pgvector**
   ```sql
   -- en la DB de Railway
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **Migrar datos de SQLite a PostgreSQL**
   ```bash
   # Local
   python manage.py dumpdata --natural-foreign --natural-primary \
     -e contenttypes -e auth.Permission \
     --indent 2 > db_dump.json

   # Cambiar a config de prod temporalmente y:
   python manage.py migrate
   python manage.py loaddata db_dump.json
   ```

4. **Actualizar modelo de embeddings a usar pgvector**
   ```python
   # Con django-pgvector
   from pgvector.django import VectorField

   class SeminarioEmbedding(models.Model):
       lote = models.OneToOneField(LoteCertificados, on_delete=CASCADE)
       vector = VectorField(dimensions=1536)  # text-embedding-3-small
       # ...
   ```

5. **Regenerar embeddings** en produccion:
   ```bash
   python manage.py rebuild_embeddings
   ```

---

## Fase 13.4: Monitoreo basico (opcional, medio dia)

### Sentry para errores

```bash
pip install sentry-sdk
```

```python
# config/settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=os.environ.get('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,  # no PII por GDPR
)
```

### Logs de IA (para debugging de tesis)

Crear modelo simple:

```python
class AILog(models.Model):
    ACCIONES = [('copilot', 'Copilot'), ('excel_map', 'Excel Mapper'), ('voice', 'Voice'), ('insights', 'Insights'), ('reason', 'Reason')]
    accion = models.CharField(max_length=20, choices=ACCIONES)
    input_text = models.TextField()
    output_text = models.TextField()
    tokens_input = models.IntegerField(null=True)
    tokens_output = models.IntegerField(null=True)
    latencia_ms = models.IntegerField(null=True)
    exito = models.BooleanField(default=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

Para tesis: graficar uso de IA en el tiempo, tasa de exito, costo estimado.

---

## Checklist final pre-defensa

- [ ] Todos los tests pasan (`pytest`)
- [ ] Coverage > 40%
- [ ] `python manage.py check --deploy` sin warnings criticos
- [ ] Swagger UI accesible en `/api/v1/docs/`
- [ ] Embeddings regenerados para todos los lotes
- [ ] README.md con setup de dev, produccion y comandos utiles
- [ ] docs/architecture.md con diagramas
- [ ] docs/ai_features.md explicando cada feature
- [ ] Sentry capturando errores
- [ ] Ultimos 3 meses de logs IA respaldados para analisis
- [ ] Video demo de 5 min mostrando cada feature en vivo
