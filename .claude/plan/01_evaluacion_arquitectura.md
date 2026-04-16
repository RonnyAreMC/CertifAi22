# Evaluacion de la Arquitectura Actual

## Estadisticas del codebase

| Archivo | Lineas | Funciones | Diagnostico |
|---------|--------|-----------|-------------|
| core/services/pdf_service.py | **1,469** | 16 | GOD OBJECT con funciones duplicadas |
| admin_panel/views.py | **1,641** | 43 | Monolitico, sin separacion por dominio |
| public/views.py | 879 | 23 | Bloat moderado |
| core/models.py | 569 | - | Aceptable pero denso |
| core/services/excel_service.py | 302 | 4 | OK pero funciones redundantes |
| core/services/email_service.py | 73 | - | OK con smell (domain hardcoded) |

## Problemas criticos

### 1. pdf_service.py es un god object con codigo muerto

- **Funciones duplicadas:** `draw_modern_wow` definida en lineas 136 y 854. `draw_geometric_wow` en lineas 317 y 1014. La segunda definicion sobrescribe la primera, volviendo las primeras 700 lineas codigo muerto.
- **3 plantillas en un if/elif:** Para agregar un nuevo diseño hay que tocar este archivo gigante.
- **Mezcla de responsabilidades:** genera PDFs, consulta DB, aplica diseño global, renderiza QR, todo junto.

### 2. admin_panel/views.py: monolito sin dominio

- 43 funciones de 5 dominios distintos (auth, batch, session, design, leaders, users, participants) en un solo archivo.
- 79 instancias repetidas de `@login_required` + `@user_passes_test(_is_admin)`.
- 14 repeticiones del patron `get_object_or_404(Model, id=id)`.
- Logica de negocio (Excel processing, PDF generation) mezclada con handlers HTTP.

### 3. Sin capa de abstraccion

- **Sin base views/mixins:** cada view reimplementa auth.
- **Sin managers custom:** queries repetidas en 5+ lugares.
- **Sin querysets reusables:** la misma logica de busqueda de participantes esta duplicada en 4 archivos.
- **Sin helpers folder:** utilidades dispersas.

### 4. Modelos con deuda tecnica

- `LoteCertificados` y `DisenoGlobal` repiten campos `firma_1..4`, `nombre_firma_*`, `cargo_firma_*`, `imagen_firma_*` (16 campos duplicados entre modelos).
- `Participante.clean()` es la unica validacion del sistema.
- `DisenoGlobal.get_solo()` es un classmethod hack en lugar de Manager custom.
- Campos sin indice critico: `SesionAsistencia.lote_id`, `Usuario.facultad`.

### 5. Sin API REST

- Todo es server-side rendering con formularios.
- Imposible consumir desde otra plataforma (movil, otros sistemas).
- No hay contratos claros (serializers, schemas).

### 6. Sin tests

- `core/tests.py` tiene 3 lineas (vacio).
- **0% coverage.**
- Cualquier refactor es un salto al vacio.

### 7. Bugs activos detectados

Documentados y corregidos en [02_bugs_corregidos.md](02_bugs_corregidos.md):
- Solo la plantilla geometrica funciona
- No se pueden cambiar colores en el clasico
- Certificados muestran correo en vez de nombre del seminario (corregido previamente)
- Duplicados de Participante (corregido previamente)

## Puntos positivos (NO tocar)

- Buena separacion de apps: `core`, `admin_panel`, `public`
- Uso correcto de `transaction.atomic()` en Excel processing
- Sistema de auditoria ya implementado (`Auditoria` model)
- Uso de `.env` y `dj_database_url` para deploy
- Static files con WhiteNoise
- Migraciones limpias y versionadas

## Decisiones tomadas para el refactor

| Decision | Justificacion |
|----------|---------------|
| No dockerizar | Usuario lo pidio explicitamente; Railway maneja deploy sin Docker |
| API REST con DRF, no GraphQL | DRF es standard Django, menor curva de aprendizaje, compatible con Expo |
| JWT + Session auth | JWT para movil, Session para admin panel web |
| No microservicios fisicos | Monolito modular es suficiente para este proyecto; "microservicios logicos" mediante apps Django + services layer |
| PostgreSQL en produccion | Para embeddings + pgvector (recomendaciones IA) |
| Strategy pattern para PDF | Permite agregar diseños sin modificar codigo existente (Open/Closed) |
| Claude API como LLM principal | Mejor rendimiento en español, pricing razonable, tool use robusto |

## Metricas objetivo post-refactor

| Metrica | Antes | Despues |
|---------|-------|---------|
| pdf_service.py LOC | 1,469 | <200 (orchestrator) + diseños separados |
| admin_panel/views.py LOC | 1,641 | <300 por dominio (~8 archivos) |
| Funciones duplicadas | 2+ | 0 |
| `@login_required` hardcoded | 79 | 0 (usa decoradores custom) |
| Cobertura de tests | 0% | 40-50% |
| Endpoints API | 0 | 20+ |
| Features de IA | 0 | 5 |
