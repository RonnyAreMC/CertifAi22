# Plan: Integración Google Meet + IA para resúmenes automáticos de eventos

**Estado**: Diseño aprobado. Pendiente implementación.
**Prioridad para tesis**: 🔥 Alta — feature diferenciadora de mayor impacto.
**Tiempo estimado**: 2 semanas de trabajo enfocado (semanas 6-8 del cronograma).
**Última actualización**: 2026-04-19

---

## 1. Contexto y motivación

El usuario tiene una cuenta **Google Workspace Education de UNEMI** con transcripción automática activa (confirmado visualmente en Meet: botones "Grabar" y "Transcribiendo Español (alfa)"). Los eventos de Mucacademy son mayoritariamente virtuales, con ponentes internacionales (cuentas Google variadas, no necesariamente UNEMI).

**Problema que resuelve**:
- El registro de asistencia en eventos virtuales genera poco valor.
- El contenido educativo se pierde al terminar la reunión.
- Docentes/ponentes no deben hacer pasos manuales post-reunión.

**Valor agregado**:
- Resumen ejecutivo automático del evento.
- Timeline con timestamps de momentos clave.
- 10-15 pares de preguntas/respuestas generadas por IA.
- Highlights (frases memorables).
- Todo publicado automáticamente en `/eventos/<id>/resumen/` — contenido reutilizable que vive para siempre.

---

## 2. Arquitectura general

### Decisión clave: **tu plataforma es el organizador de todos los Meets**

Esto resuelve 3 problemas de un tiro:
1. El usuario tiene solo 1 cuenta UNEMI → todo el contenido cae en 1 Drive.
2. Docentes/ponentes internacionales NO necesitan Workspace pago — solo se unen al link.
3. Automatización end-to-end: cero pasos manuales para el docente.

### Flujo completo

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Admin crea SesionAsistencia con modalidad='virtual'          │
│    ↓                                                            │
│ 2. Backend llama Google Calendar API con cuenta UNEMI           │
│    → conferenceData.createRequest                               │
│    → Google devuelve link Meet                                  │
│    → Se guarda en SesionAsistencia.enlace_virtual               │
│    ↓                                                            │
│ 3. Día del evento: ponentes/asistentes se unen con el link      │
│    ↓                                                            │
│ 4. Durante la reunión: alguien (admin/bot) activa               │
│    "Grabar" + "Transcribir" (botones ya existen en Meet)        │
│    ↓                                                            │
│ 5. Reunión termina → Google guarda automáticamente:             │
│    • My Drive/Meet Recordings/*.mp4                             │
│    • My Drive/Meet Transcripts/*.txt (o .docs)                  │
│    ↓                                                            │
│ 6. Backend detecta archivos nuevos:                             │
│    • Webhook de Drive API (preferido)                           │
│    • Cron job cada 10 min como fallback                         │
│    ↓                                                            │
│ 7. Pipeline de procesamiento:                                   │
│    a. Descargar transcript desde Drive                          │
│    b. Parsear formato (timestamps, hablantes)                   │
│    c. Enviar a Claude API con prompts específicos               │
│    d. Guardar en SesionResumen                                  │
│    ↓                                                            │
│ 8. Página pública muestra:                                      │
│    /eventos/<id>/resumen/                                       │
│    → Resumen + Timeline clickeable + Q&A + Highlights           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Modelo de datos

### Nuevo modelo: `SesionResumen`

Ubicación: `core/models/resumen.py` (nuevo archivo, registrarlo en `__init__.py`).

```python
"""Modelo de resumen automático de sesiones virtuales."""
from django.db import models

from core.base.models import TimestampedModel


class EstadoResumen(models.TextChoices):
    PENDIENTE = 'pendiente', 'Pendiente de procesar'
    PROCESANDO = 'procesando', 'Procesando con IA'
    LISTO = 'listo', 'Resumen disponible'
    ERROR = 'error', 'Error en procesamiento'


class SesionResumen(TimestampedModel):
    """Resumen generado por IA a partir del transcript de un Meet.

    Una sesión virtual tiene máximo un resumen (OneToOne).
    El resumen se crea automáticamente cuando Google deposita el
    transcript en el Drive del organizador (cuenta UNEMI).
    """
    sesion = models.OneToOneField(
        'core.SesionAsistencia', on_delete=models.CASCADE,
        related_name='resumen',
    )

    # Artefactos de Google
    transcript_file_id = models.CharField(max_length=100, blank=True, db_index=True)
    transcript_url = models.URLField(max_length=500, blank=True)
    recording_file_id = models.CharField(max_length=100, blank=True)
    recording_url = models.URLField(max_length=500, blank=True)
    meeting_id = models.CharField(max_length=100, blank=True, db_index=True)

    # Contenido generado por IA
    resumen_ejecutivo = models.TextField(blank=True)
    timeline_json = models.JSONField(default=list, blank=True)
    # Formato: [{"tiempo": "00:05:32", "titulo": "...", "contenido": "..."}]

    qa_json = models.JSONField(default=list, blank=True)
    # Formato: [{"pregunta": "...", "respuesta": "..."}]

    highlights_json = models.JSONField(default=list, blank=True)
    # Formato: [{"tiempo": "00:23:15", "texto": "...", "hablante": "..."}]

    temas_principales = models.JSONField(default=list, blank=True)
    # Formato: ["Machine Learning", "Ética de IA", "..."]

    # Meta
    estado = models.CharField(
        max_length=20, choices=EstadoResumen.choices,
        default=EstadoResumen.PENDIENTE, db_index=True,
    )
    error_mensaje = models.TextField(blank=True)
    duracion_minutos = models.IntegerField(null=True, blank=True)
    cantidad_participantes = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'Resumen de Sesión'
        verbose_name_plural = 'Resúmenes de Sesiones'
        ordering = ['-created_at']
```

### Extensión de `SesionAsistencia`

Agregar 2 campos opcionales:
- `google_calendar_event_id` (CharField) — ID del evento en Calendar para actualizarlo/eliminarlo si se edita.
- `transcripcion_habilitada` (BooleanField, default=True) — checkbox en el form para optar por no generar resumen.

### Nueva tabla: `GoogleCredential`

Ubicación: `core/models/integrations.py` (nuevo).

```python
class GoogleCredential(TimestampedModel):
    """Credenciales OAuth de Google (access + refresh token).

    Hay 1 sola fila: representa la cuenta UNEMI que organiza todos los Meets.
    El refresh_token se debe cifrar en producción (ver django-cryptography).
    """
    email = models.EmailField(unique=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_uri = models.URLField(default='https://oauth2.googleapis.com/token')
    client_id = models.CharField(max_length=200)
    client_secret = models.CharField(max_length=200)  # TODO: cifrar
    scopes = models.JSONField(default=list)
    expiry = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Credencial Google'
        verbose_name_plural = 'Credenciales Google'
```

---

## 4. Setup previo (antes de escribir código)

### 4.1 Google Cloud Console (~30 min, 1 sola vez)

1. Ir a https://console.cloud.google.com/
2. Crear proyecto: `mucacademy-meet-integration`
3. Habilitar APIs:
   - **Google Calendar API**
   - **Google Drive API**
   - **Google Docs API** (opcional — si el transcript viene como Google Doc y no .txt)
4. Crear credenciales OAuth 2.0:
   - Tipo: **Web application**
   - Authorized redirect URIs: `http://localhost:8000/admin/google/callback/` + producción
5. Configurar OAuth consent screen:
   - User type: **External** (si no tienes dominio UNEMI administrativo) o **Internal** (si puedes)
   - Scopes necesarios:
     - `https://www.googleapis.com/auth/calendar.events`
     - `https://www.googleapis.com/auth/drive.readonly`
     - `https://www.googleapis.com/auth/drive.file`
   - Test users: agregar la cuenta UNEMI (si modo External sin verificar)

### 4.2 Dependencias Python

Agregar a `requirements.txt`:
```
google-auth>=2.25.0
google-auth-oauthlib>=1.2.0
google-auth-httplib2>=0.2.0
google-api-python-client>=2.100.0
```

### 4.3 Variables de entorno (`.env`)

```bash
GOOGLE_CLIENT_ID=xxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=http://localhost:8000/admin/google/callback/
DRIVE_MEET_RECORDINGS_FOLDER_NAME=Meet Recordings
DRIVE_MEET_TRANSCRIPTS_FOLDER_NAME=Meet Transcripts
```

---

## 5. Estructura de carpetas

```
core/
├── models/
│   ├── resumen.py              (nuevo)
│   └── integrations.py         (nuevo)
├── services/
│   ├── meet/                   (nuevo módulo)
│   │   ├── __init__.py
│   │   ├── oauth.py            # Flow OAuth, guardar/refrescar tokens
│   │   ├── calendar_client.py  # Crear eventos con Meet link
│   │   ├── drive_client.py     # Listar/descargar archivos de Drive
│   │   ├── transcript_parser.py # Parsear formato .txt/.docs de Meet
│   │   ├── ai_pipeline.py      # Prompts Claude: resumen, Q&A, timeline
│   │   └── webhook_handler.py  # Procesar notificaciones push de Drive
│   └── ai/
│       └── client.py           # (ya existe) — reutilizar

api/
└── admin/
    └── meet/                   (nuevo módulo)
        ├── __init__.py
        ├── views.py            # Endpoints OAuth + retrigger resumen
        ├── urls.py

admin_panel/
└── views/
    └── google_oauth.py         # Shell de consent + callback

public/
└── templates/public/
    └── evento_resumen.html     # UI pública del resumen
```

---

## 6. Fases de implementación

### 🟢 Fase 1: OAuth y setup (2 días)

**Objetivo**: Conectar UNA vez la cuenta UNEMI al backend, guardar refresh_token.

**Tareas**:
1. Crear modelo `GoogleCredential` + migración.
2. Implementar `core/services/meet/oauth.py`:
   - `build_flow()` — construye el flow OAuth con scopes.
   - `save_credentials(flow)` — guarda access + refresh token en DB.
   - `get_credentials()` — recupera y auto-refresca si expiró.
3. Endpoint `admin_panel/views/google_oauth.py`:
   - `GET /admin/google/connect/` — redirige a consent de Google.
   - `GET /admin/google/callback/` — recibe code, cambia por tokens, guarda.
4. Botón en `panel/auth/mi_estado.html` o dashboard superadmin: "Conectar Google".

**Criterio de éxito**: Puedes hacer `GoogleCredential.objects.get()` y usar sus tokens para llamar a Drive API.

---

### 🟢 Fase 2: Crear eventos con Meet link automático (1 día)

**Objetivo**: Al crear una sesión virtual desde el admin panel, el backend genera el Meet link vía Calendar API.

**Tareas**:
1. Implementar `core/services/meet/calendar_client.py`:
   ```python
   def create_meet_event(summary, description, start, end, attendees_emails):
       """Crea evento en Calendar con conferenceData → devuelve meet_link + event_id."""
   ```
2. Hook en `api/admin/sessions/views.py` (SesionViewSet.perform_create):
   - Si `modalidad='virtual'` y no hay `enlace_virtual`, llamar a `create_meet_event()`.
   - Guardar `enlace_virtual` + `google_calendar_event_id`.
3. Hook en update: si cambió fecha/hora, actualizar el evento en Calendar.

**Criterio de éxito**: Al crear una sesión virtual desde la UI admin, aparece automáticamente un link meet.google.com/xxx en el form.

---

### 🟡 Fase 3: Descargar transcripts desde Drive (1 día)

**Objetivo**: Dado un `meeting_id`, encontrar y descargar el transcript correspondiente.

**Tareas**:
1. Implementar `core/services/meet/drive_client.py`:
   ```python
   def list_recent_transcripts(since_datetime):
       """Lista archivos en 'Meet Transcripts' creados después de X."""

   def download_transcript(file_id) -> str:
       """Descarga el contenido del archivo como texto."""

   def match_transcript_to_session(file_name, sesion) -> bool:
       """Heurística: matchea por fecha + título + meeting_id."""
   ```
2. Probar con un transcript real ya existente en tu Drive.

**Criterio de éxito**: `download_transcript(file_id)` devuelve el texto completo de una reunión de prueba.

---

### 🟡 Fase 4: Pipeline IA con Claude (2 días)

**Objetivo**: Transformar transcript crudo en resumen estructurado.

**Tareas**:
1. Reutilizar `core/services/ai/client.py` (ya configurado con Anthropic).
2. Implementar `core/services/meet/ai_pipeline.py` con 4 funciones:
   ```python
   def generar_resumen_ejecutivo(transcript) -> str
   def generar_timeline(transcript) -> list[dict]
   def generar_qa(transcript) -> list[dict]
   def detectar_highlights(transcript) -> list[dict]
   ```
3. Prompts cuidados (ver sección 8 abajo).
4. Usar **prompt caching** para economizar: el transcript es el mismo en 4 llamadas → cachear el system prompt + transcript.
5. Todo envuelto en `procesar_sesion_completa(sesion_resumen)` que orquesta las 4 llamadas y guarda resultados.

**Criterio de éxito**: Dado un transcript real, genera un `SesionResumen` completo en DB con los 4 campos llenos.

---

### 🟡 Fase 5: Detección automática (2 días)

**Objetivo**: Ejecutar el pipeline sin intervención humana cuando Google deposita un transcript.

**Opción A — Webhook de Drive (preferido)**:
1. Endpoint `POST /api/v1/webhooks/drive/` que recibe notificaciones push.
2. Usar `drive.files.watch()` para subscribirse a la carpeta "Meet Transcripts".
3. Al recibir notificación: buscar sesión correspondiente → crear SesionResumen → disparar pipeline async.

**Opción B — Cron job (fallback simple)**:
1. Instalar `django-q` o usar Celery.
2. Task: `scan_new_transcripts()` corre cada 10 min.
3. Lista archivos nuevos, matchea con sesiones virtuales recientes, dispara pipeline.

**Recomendación**: empezar con cron job (más simple, sin HTTPS obligatorio), migrar a webhook después.

**Criterio de éxito**: Haces una reunión de prueba, la terminas, en <30 min aparece el resumen publicado automáticamente.

---

### 🟡 Fase 6: UI pública del resumen (3 días)

**Objetivo**: Página bonita y navegable del resumen.

**Tareas**:
1. Nueva plantilla `public/templates/public/evento_resumen.html`.
2. Layout propuesto:
   - **Hero**: título de la sesión + fecha + duración + "ver en YouTube/Drive" si hay recording.
   - **Resumen ejecutivo**: párrafos, bien tipografiado.
   - **Timeline interactivo**: lista de bullets con timestamp (00:05:32 → título → contenido expandible). Click → scroll al video (si está embebido) o copia el timestamp.
   - **Q&A**: acordeón con 10-15 preguntas.
   - **Highlights**: cards con frases destacadas + hablante + timestamp.
   - **Temas**: tags/chips de temas principales.
3. Endpoint `GET /eventos/<int:sesion_id>/resumen/` en `public/urls.py`.
4. Manejar estados: "pendiente", "procesando" (spinner), "error" (mensaje), "listo" (contenido).

**Criterio de éxito**: En `/eventos/5/resumen/` ves el resumen completo con UI usable y comparable a Notion AI / Fathom.

---

### 🟢 Fase 7: Admin — retrigger manual (0.5 días)

**Objetivo**: Botón para volver a procesar una sesión si hubo error o si el transcript tardó.

**Tareas**:
1. Custom action en el viewset `SesionViewSet`:
   - `POST /api/v1/admin/sessions/<id>/generar-resumen/` → fuerza el pipeline.
2. Botón en la UI admin de sesiones: "Regenerar resumen".
3. Log de auditoría: "Resumen regenerado para sesión X por usuario Y".

---

### 🟡 Fase 8: Testing end-to-end (1-2 días)

**Tareas**:
1. Hacer una reunión real de prueba (10-15 min).
2. Verificar que aparece en `/eventos/<id>/resumen/` con contenido coherente.
3. Probar con reunión en inglés (ponente internacional) para validar Claude multi-idioma.
4. Tests unitarios:
   - `test_calendar_create_event_mocks_google`
   - `test_transcript_parser_con_formato_real`
   - `test_ai_pipeline_con_transcript_corto`

---

## 7. Riesgos y mitigaciones

| Riesgo | Impacto | Mitigación |
|---|:---:|---|
| Transcripción "Español (alfa)" tiene baja calidad | Medio | Probar primero con reunión corta. Si falla, documentar limitación en tesis. |
| Grabación MP4 tarda horas en estar lista | Bajo | El transcript (5-15 min) es suficiente para el pipeline; MP4 es bonus. |
| OAuth token expira si no se usa en 6 meses | Medio | Job semanal que hace `creds.refresh()` para mantenerlo vivo. |
| Quota de Calendar/Drive API se agota | Muy bajo | 1M req/día, suficiente para miles de sesiones. |
| Reunión se crea pero nadie activa "Grabar" | Alto | Agregar nota visual en la UI del organizador: "Recuerda activar grabación". Plan B: bot automático en fase 2. |
| Costo Claude API para sesiones largas (2h+) | Bajo | Con prompt caching: ~$0.05/sesión de 2h. Presupuesto mínimo. |
| Privacidad: ponentes deben consentir grabación | Alto | Agregar disclaimer visible en el landing del evento + email automático previo. |

---

## 8. Prompts de Claude (propuesta)

### System prompt común (cached)
```
Eres un asistente que analiza transcripciones de sesiones educativas universitarias.
Tu respuesta DEBE ser JSON válido según el schema que se te indica.
Respondes en el mismo idioma que el transcript original.
Eres conciso pero completo. No inventas información.
```

### Resumen ejecutivo
```
Analiza el siguiente transcript de una sesión educativa de {duracion} minutos.
Genera un resumen ejecutivo de 3 párrafos:
1. Contexto y objetivos de la sesión.
2. Puntos clave tratados (los 3-5 más importantes).
3. Conclusiones o takeaways principales.

Transcript:
{transcript}

Responde en JSON: {"resumen": "texto..."}
```

### Timeline
```
Identifica los 8-12 momentos más importantes del transcript. Para cada uno:
- tiempo: timestamp en formato HH:MM:SS
- titulo: 5-8 palabras que capturan el momento
- contenido: 1-2 frases explicativas

Responde en JSON: {"timeline": [{...}, ...]}
```

### Q&A
```
Genera 10 preguntas que un estudiante que NO asistió podría tener sobre el tema,
con sus respuestas basadas ÚNICAMENTE en el transcript. No inventes información.
Varía en dificultad (conceptual, aplicada, crítica).

Responde en JSON: {"qa": [{"pregunta": "...", "respuesta": "..."}, ...]}
```

### Highlights
```
Extrae las 5-8 frases MÁS memorables o citables del transcript.
Deben ser declaraciones originales del ponente, no explicaciones genéricas.

Responde en JSON: {"highlights": [{"tiempo": "HH:MM:SS", "texto": "...", "hablante": "..."}, ...]}
```

---

## 9. Preguntas abiertas para resolver antes de arrancar

1. ¿La cuenta UNEMI soporta webhooks push de Drive en producción (requiere HTTPS)? → Sí, Railway da HTTPS automático.
2. ¿Hay alguna política de UNEMI sobre grabar reuniones con ponentes externos? → Consultar con tutor de tesis.
3. ¿El dominio UNEMI permite modo "Internal" en OAuth consent screen? → Probablemente NO (requiere admin del Workspace). Usar modo External con test users.
4. ¿Guardamos el MP4 de la grabación o solo linkeamos al Drive? → Linkear al Drive (no duplicar storage).

---

## 10. Integración con el cronograma de tesis (14 semanas)

| Semana | Foco | Esta feature |
|---|---|---|
| 1-2 | Limpieza código (ya hecho) + models 10/10 (ya hecho) | — |
| 3 | Ajustes API para Expo | — |
| 4-5 | Expo base (login, sesiones, QR) | — |
| **6** | Expo + arrancar Fase 1-2 | **OAuth + Calendar API** |
| **7** | Expo certificados + Fase 3-4 | **Drive + pipeline IA** |
| **8** | Fase 5-6 | **Detección automática + UI** |
| 9-10 | Tests + coverage 70% | Fase 8 |
| 11 | CI/CD + deps pineadas | — |
| 12 | Deploy Railway + EAS | — |
| 13-14 | Tesis escrita + defensa | — |

---

## 11. Métricas para defensa de tesis

Al presentar la feature, tener estos números listos:
- **N reuniones procesadas** durante el desarrollo.
- **Precisión subjetiva** del resumen (eval manual de 3-5 reuniones, escala 1-5).
- **Tiempo ahorrado**: cuánto tardaría un humano en hacer lo mismo (30-60 min/reunión).
- **Costo operacional**: $X/reunión (Claude API) vs. $Y valor generado.
- **Screenshots** del resumen lado a lado con el transcript crudo.

---

## 12. Referencias técnicas

- Google Calendar API — `events.insert` con `conferenceData.createRequest`: https://developers.google.com/calendar/api/guides/create-events#meet
- Google Drive API v3 — `files.list` con query: https://developers.google.com/drive/api/guides/search-files
- Google Drive API — `files.watch` (push notifications): https://developers.google.com/drive/api/guides/push
- Anthropic API — prompt caching: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- Meet transcripts format: archivos `.txt` con líneas tipo `HH:MM:SS - Nombre: texto`

---

## 13. Nota sobre evolución futura

Este plan se centra en el **MVP**. Una vez funcionando, hay extensiones naturales para fase post-tesis:

- **Chat sobre el evento**: RAG sobre el transcript con Claude → "¿Qué dijo el ponente sobre X?".
- **Traducción automática**: transcripts en inglés → resumen en español + viceversa.
- **Búsqueda semántica cross-eventos**: embeddings de transcripts para encontrar "en qué evento se habló de redes neuronales".
- **Quizz generado**: transformar el Q&A en un test evaluable.
- **Certificado reforzado**: generar certificado solo si el participante respondió correctamente ≥70% del quizz.
