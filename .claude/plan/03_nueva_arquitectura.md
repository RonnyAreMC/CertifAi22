# Nueva Arquitectura Objetivo

## Principio: Monolito modular + API REST

No vamos a hacer microservicios fisicos (con Docker, mensajeria, etc). La complejidad no lo justifica y el usuario lo descarto.

En su lugar: **arquitectura hexagonal** con separacion clara de capas. Cada "microservicio logico" es un app Django o un modulo de services/.

## Diagrama de capas

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENTES (consumidores)                   │
│  Web Admin Panel (HTML)  │  Web Public  │  Expo Mobile (futuro) │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACION                      │
│  admin_panel/views/*    public/views/*   api/endpoints/*    │
│       (Django MVC)         (Django MVC)      (DRF)          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     CAPA DE SERVICIOS                        │
│  pdf/        excel/      email/      recommender/    ai/    │
│  (strategy)  (process)   (notif)     (embeddings)   (llm)   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAPA DE DOMINIO                           │
│  models/     managers/     querysets/     validators/       │
│  (entities)  (bus. logic)  (queries)      (rules)           │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  CAPA DE INFRAESTRUCTURA                     │
│       PostgreSQL     Claude API    OpenAI API               │
│       (data)         (LLM)         (embeddings)             │
└─────────────────────────────────────────────────────────────┘
```

## Estructura de carpetas objetivo

```
certify/
├── config/                         # Django settings
│   ├── settings/
│   │   ├── base.py                 # comun
│   │   ├── development.py          # DEBUG=True, SQLite
│   │   └── production.py           # PostgreSQL, cache
│   └── urls.py
│
├── core/                           # App central (dominio)
│   ├── models.py                   # Entidades
│   ├── base/                       # NUEVO: clases base
│   │   ├── models.py               # TimestampedModel, SingletonModel
│   │   ├── views.py                # AdminRequiredMixin, etc
│   │   ├── decorators.py           # @admin_required, @ajax_only
│   │   ├── mixins.py               # AuditLogMixin
│   │   └── querysets.py            # BaseSearchQuerySet
│   │
│   ├── managers/                   # NUEVO: managers custom
│   │   ├── certificado.py
│   │   ├── participante.py
│   │   ├── lote.py
│   │   └── session.py
│   │
│   ├── helpers/                    # NUEVO: utilities puras
│   │   ├── text.py                 # sanitize, normalize, slugify
│   │   ├── files.py                # safe filenames, image validation
│   │   ├── excel.py                # column detection, phone normalization
│   │   └── http.py                 # get_client_ip, is_ajax
│   │
│   ├── validators.py               # Ya existe, se expande
│   │
│   ├── services/                   # Logica de negocio
│   │   ├── pdf/                    # NUEVO: Strategy pattern
│   │   │   ├── __init__.py         # generate_certificate_pdf()
│   │   │   ├── base.py             # BasePDFDesign (ABC)
│   │   │   ├── fonts.py
│   │   │   ├── colors.py
│   │   │   ├── designs/
│   │   │   │   ├── classic.py
│   │   │   │   ├── modern.py
│   │   │   │   └── geometric.py
│   │   │   ├── components/
│   │   │   │   ├── signatures.py
│   │   │   │   ├── logos.py
│   │   │   │   ├── seals.py
│   │   │   │   └── qr_page.py
│   │   │   └── generator.py        # Orchestrator
│   │   │
│   │   ├── excel/                  # NUEVO: subdividido
│   │   │   ├── __init__.py
│   │   │   ├── analyzer.py         # analisis de columnas
│   │   │   ├── processor.py        # procesamiento
│   │   │   └── mapper.py           # mapeo de columnas (+ IA en fase 9)
│   │   │
│   │   ├── email/
│   │   │   ├── __init__.py
│   │   │   ├── templates.py
│   │   │   └── sender.py
│   │   │
│   │   ├── recommender/            # NUEVO: IA recomendaciones
│   │   │   ├── __init__.py
│   │   │   ├── embeddings.py
│   │   │   ├── storage.py          # pgvector
│   │   │   ├── engine.py           # similaridad coseno
│   │   │   └── cold_start.py
│   │   │
│   │   └── ai/                     # NUEVO: integracion LLM
│   │       ├── __init__.py
│   │       ├── client.py           # wrapper Claude API
│   │       ├── copilot.py          # asistente cuerpo certificado
│   │       ├── insights.py         # narrativa de metricas
│   │       ├── voice.py            # transcripcion + entity extraction
│   │       └── excel_mapper.py     # clasificacion de columnas
│   │
│   └── management/commands/
│       ├── rebuild_embeddings.py   # NUEVO: recalcula embeddings
│       ├── cleanup_duplicates.py   # NUEVO: mantenimiento
│       └── create_default_superuser.py
│
├── admin_panel/                    # Panel admin web (Django MVC)
│   ├── views/                      # NUEVO: split por dominio
│   │   ├── __init__.py             # re-exporta todo
│   │   ├── auth.py
│   │   ├── dashboard.py
│   │   ├── batch.py
│   │   ├── certificate.py
│   │   ├── session.py
│   │   ├── design.py
│   │   ├── landing.py
│   │   ├── leaders.py
│   │   ├── participants.py
│   │   ├── users.py
│   │   └── ai.py                   # NUEVO: endpoints IA
│   ├── urls.py                     # sin cambios
│   ├── forms.py
│   └── templates/
│
├── public/                         # Web publica
│   ├── views/
│   │   ├── __init__.py
│   │   ├── landing.py
│   │   ├── search.py
│   │   ├── attendance.py
│   │   ├── session.py
│   │   └── verify.py
│   └── ...
│
├── api/                            # NUEVO: API REST (DRF)
│   ├── __init__.py
│   ├── apps.py
│   ├── urls.py                     # /api/v1/...
│   ├── auth/
│   │   ├── serializers.py
│   │   ├── views.py                # login, refresh, logout
│   │   └── permissions.py          # custom perms
│   ├── participants/
│   │   ├── serializers.py
│   │   ├── views.py                # ViewSets DRF
│   │   └── filters.py
│   ├── certificates/
│   ├── sessions/
│   ├── recommendations/            # endpoint que consume recommender service
│   ├── ai/                         # endpoints para IA (copilot, voice, etc)
│   └── common/
│       ├── pagination.py
│       ├── exceptions.py
│       └── schemas.py              # OpenAPI schemas
│
├── tests/                          # NUEVO
│   ├── conftest.py
│   ├── fixtures/
│   ├── test_pdf_designs/
│   ├── test_excel_processing/
│   ├── test_ai_services/
│   └── test_api_endpoints/
│
└── docs/                           # NUEVO: documentacion tecnica
    ├── api.md                      # OpenAPI / Swagger
    ├── architecture.md
    ├── ai_features.md
    └── deployment.md
```

## "Microservicios logicos" (Bounded Contexts)

Cada uno tiene responsabilidad unica y bajo acoplamiento:

| Contexto | Apps/Modulos | Responsabilidad |
|----------|--------------|-----------------|
| **Auth & Users** | core (Usuario, SolicitudAcceso) + api/auth | Acceso al sistema |
| **Certificates** | core + services/pdf + api/certificates | Generacion y distribucion de PDFs |
| **Participants** | core + api/participants | Gestion unificada de personas |
| **Batches** | core + services/excel + api/batches | Procesamiento masivo |
| **Sessions & Attendance** | core + api/sessions | QR, check-in, confirmaciones |
| **Design System** | core + services/pdf/designs | Plantillas y personalizacion |
| **AI Services** | services/ai + api/ai | Copilot, mapeo, insights, voz |
| **Recommendations** | services/recommender + api/recommendations | Embeddings y similaridad |
| **Analytics** | services/ai/insights + admin dashboard | Metricas + narrativa IA |
| **Content Management** | core (LandingBloque) + admin_panel/landing | Landing dinamico |

## Ventajas de esta arquitectura

1. **Escalable sin over-engineering** — no necesitas Kubernetes para 440 usuarios
2. **API-first compatible con Expo** — misma API para web y movil
3. **Testeable** — cada capa se testea en aislamiento
4. **Extensible** — agregar un diseño PDF nuevo = crear un archivo en `designs/`
5. **Tesis-friendly** — cada capa mapea a un concepto academico (SOLID, strategy, repository, etc.)

## Trade-offs aceptados

- NO Docker: Railway lo maneja. Menos complejidad.
- NO celery/redis para tareas: threading basico es suficiente (email, etc).
- NO GraphQL: REST es mas simple para tu caso y tu nivel.
- NO event bus: acoplamiento directo entre servicios, aceptable en monolito modular.
