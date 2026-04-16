# Fases 8-12: Features de IA

## Stack de IA elegido

| Componente | Proveedor | Uso | Costo aprox |
|------------|-----------|-----|-------------|
| LLM principal | Anthropic Claude | Copilot, Insights, Mapeo Excel, Voz | Haiku 4.5 ($1/M input, $5/M output) |
| Embeddings | OpenAI `text-embedding-3-small` | Recomendaciones | $0.02/M tokens |
| Transcripcion voz (fallback) | OpenAI Whisper | Si Web Speech API falla | $0.006/min |
| Vector storage | pgvector (PostgreSQL) | Embeddings persistentes | $0 (PostgreSQL) |

### Por que Claude Haiku 4.5

- Excelente en español
- Tool use confiable (importante para voz)
- 10x mas barato que Sonnet/Opus
- Suficiente para clasificacion, extraccion y generacion simple

### Configuracion base

```python
# core/services/ai/client.py
import os
from anthropic import Anthropic
from functools import lru_cache

@lru_cache
def get_claude_client():
    return Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

def call_claude(
    system: str,
    user: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 1024,
    response_format: str = "text"
):
    """Wrapper estandar para calls a Claude con prompt caching."""
    client = get_claude_client()
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[{
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"}  # cachea el system prompt
        }],
        messages=[{"role": "user", "content": user}]
    )
    return response.content[0].text
```

---

## Fase 8: Copilot del cuerpo del certificado (2-3 horas)

### Caso de uso

Admin esta creando un lote. El textarea del `cuerpo_certificado` tiene un boton ✨. Al clickearlo, se abre un modal con:
- Acciones rapidas: "Formal", "Amigable", "Inspiracional", "Corto", "Expandido"
- Campo libre: "Ayudame a escribir uno para un seminario de IA en salud"
- Preview del texto generado con botones: Aceptar / Regenerar / Editar

### Implementacion

#### 8.1 Servicio

```python
# core/services/ai/copilot.py
from .client import call_claude

COPILOT_SYSTEM_PROMPT = """Eres un asistente experto en redaccion de textos institucionales para certificados academicos ecuatorianos.

REGLAS ESTRICTAS:
1. El texto DEBE incluir las variables {curso} y {horas} exactamente asi (con llaves).
2. El tono debe ser profesional pero no acartonado.
3. Entre 40 y 120 palabras.
4. Sin emojis, sin markdown.
5. Respeta el español ecuatoriano (no usa "vosotros", usa "ustedes").
6. Menciona el compromiso academico/profesional.
7. NUNCA menciones el nombre del participante (solo la institucion usa la plantilla para todos).

Devuelve SOLO el texto del cuerpo, sin explicaciones ni encabezados."""

def generate_body_text(
    tipo_evento: str = "seminario",
    contexto: str = "",
    tono: str = "formal",
    accion: str = "create"
) -> dict:
    """
    Genera un cuerpo de certificado.

    tipo_evento: seminario, taller, curso, capacitacion, conferencia
    contexto: descripcion libre del tema
    tono: formal, amigable, inspirador, corto, expandido
    accion: create, rewrite, shorten, expand
    """
    user_msg = f"""Genera un cuerpo de certificado con estas caracteristicas:
- Tipo de evento: {tipo_evento}
- Contexto: {contexto or 'general'}
- Tono: {tono}
- Accion: {accion}

Recuerda usar {{curso}} y {{horas}} como variables."""

    text = call_claude(
        system=COPILOT_SYSTEM_PROMPT,
        user=user_msg,
        max_tokens=500
    )

    # Validacion defensiva
    if "{curso}" not in text or "{horas}" not in text:
        # Retry con prompt mas enfatico
        text = call_claude(
            system=COPILOT_SYSTEM_PROMPT + "\n\nIMPORTANTE: TIENES que incluir {curso} y {horas} literalmente.",
            user=user_msg,
            max_tokens=500
        )

    return {
        "texto": text.strip(),
        "tipo": tipo_evento,
        "tono": tono,
    }
```

#### 8.2 Endpoint API

```python
# api/ai/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from core.services.ai.copilot import generate_body_text

class CopilotBodyView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        tipo_evento = request.data.get('tipo_evento', 'seminario')
        contexto = request.data.get('contexto', '')
        tono = request.data.get('tono', 'formal')
        accion = request.data.get('accion', 'create')

        result = generate_body_text(tipo_evento, contexto, tono, accion)
        return Response(result)
```

#### 8.3 UI (Django template + JS)

En `admin_panel/templates/panel/diseno/global.html`:

```html
<div class="relative">
    <textarea name="cuerpo_certificado" id="cuerpoCert">{{ diseno.cuerpo_certificado }}</textarea>

    <button type="button" onclick="openCopilot()" class="absolute top-2 right-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-3 py-1 rounded-lg text-xs font-bold">
        ✨ Asistente IA
    </button>
</div>

<!-- Modal -->
<div id="copilotModal" class="fixed inset-0 bg-black/50 hidden z-50">
    <div class="max-w-2xl mx-auto mt-20 bg-white dark:bg-[#162054] rounded-2xl p-6">
        <h3>Asistente IA para cuerpo del certificado</h3>

        <label>Tipo de evento</label>
        <select id="aiTipo">
            <option>seminario</option>
            <option>taller</option>
            <option>curso</option>
            <option>conferencia</option>
        </select>

        <label>Contexto (opcional)</label>
        <input id="aiContexto" placeholder="Ej: sobre IA aplicada a salud">

        <label>Tono</label>
        <div class="flex gap-2">
            <button onclick="setTono('formal')">Formal</button>
            <button onclick="setTono('amigable')">Amigable</button>
            <button onclick="setTono('inspirador')">Inspirador</button>
            <button onclick="setTono('corto')">Corto</button>
        </div>

        <button onclick="generate()">Generar</button>

        <div id="aiPreview" class="mt-4 p-4 bg-gray-50 rounded-lg hidden">
            <p id="aiTexto"></p>
            <button onclick="acceptAI()">Usar este texto</button>
            <button onclick="generate()">Regenerar</button>
        </div>
    </div>
</div>

<script>
async function generate() {
    const res = await fetch('/api/v1/ai/copilot/body/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({
            tipo_evento: document.getElementById('aiTipo').value,
            contexto: document.getElementById('aiContexto').value,
            tono: currentTono,
            accion: 'create'
        })
    });
    const data = await res.json();
    document.getElementById('aiTexto').textContent = data.texto;
    document.getElementById('aiPreview').classList.remove('hidden');
}

function acceptAI() {
    document.getElementById('cuerpoCert').value = document.getElementById('aiTexto').textContent;
    document.getElementById('copilotModal').classList.add('hidden');
}
</script>
```

### Entregable
- Endpoint funcional
- Modal con UI completa
- Usado tanto en diseño global como en configuracion de lote
- Documentado en Swagger
- Commit: `feat: AI copilot for certificate body text`

---

## Fase 9: Mapeo inteligente de Excel (1-2 dias)

### Caso de uso

Admin sube un Excel con columnas raras. El sistema hoy hace keyword matching (`"nombre" in column_name`), lo cual fallo hoy en produccion (el curso tenia correos por mal mapeo). Con IA analizamos los **datos reales**, no solo los nombres.

### Implementacion

#### 9.1 Servicio

```python
# core/services/ai/excel_mapper.py
import json
from .client import call_claude

MAPPER_SYSTEM_PROMPT = """Eres un experto en limpieza de datos. Analiza filas de un Excel de registros de estudiantes y clasifica cada columna en UNA de estas categorias:

- cedula: documento de identidad ecuatoriano (10 digitos)
- email: correos electronicos
- nombres: primer y segundo nombre de personas
- apellidos: apellidos paterno y materno
- nombre_completo: nombres y apellidos juntos en una sola columna
- curso: nombre del seminario/taller/curso
- celular: telefono celular (10 digitos, empieza con 09)
- facultad: facultad o carrera universitaria
- fecha: fecha de evento
- otro: no clasificable

REGLAS:
1. Clasifica por el CONTENIDO, no solo el nombre de la columna.
2. Si hay duda, preferir "otro" a clasificar mal.
3. Responde SOLO JSON valido.

Formato de respuesta:
{
  "mapping": {
    "ColA": "cedula",
    "ColB": "email"
  },
  "confidence": 0.95,
  "warnings": ["ColX parece tener datos mezclados"]
}"""

def map_excel_columns(sample_data: dict) -> dict:
    """
    sample_data: {
        "ColA": ["0912345678", "0998765432", ...],
        "ColB": ["ana@unemi.edu.ec", ...],
    }
    """
    user_msg = f"Datos de las primeras filas:\n\n{json.dumps(sample_data, indent=2, ensure_ascii=False)}"

    response = call_claude(
        system=MAPPER_SYSTEM_PROMPT,
        user=user_msg,
        max_tokens=1024
    )

    try:
        result = json.loads(response)
    except json.JSONDecodeError:
        # fallback: busca el primer bloque JSON
        import re
        match = re.search(r'\{.*\}', response, re.DOTALL)
        result = json.loads(match.group()) if match else {"mapping": {}, "confidence": 0.0}

    return result
```

#### 9.2 Integracion con flujo Excel existente

```python
# core/services/excel/analyzer.py (refactor de excel_service.py)
from core.services.ai.excel_mapper import map_excel_columns

def analyze_excel_file(file_path, use_ai=True):
    df = pd.read_excel(file_path, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]

    # Extraer muestras de datos (primeras 5 filas)
    sample_data = {
        col: df[col].dropna().head(5).tolist()
        for col in df.columns
    }

    if use_ai:
        ai_mapping = map_excel_columns(sample_data)
        auto_mapping = ai_mapping['mapping']
        confidence = ai_mapping['confidence']
        warnings = ai_mapping.get('warnings', [])
    else:
        # Fallback al metodo antiguo (keyword matching)
        auto_mapping = legacy_keyword_mapping(df.columns)
        confidence = None
        warnings = []

    return {
        'columns': list(df.columns),
        'suggestions': auto_mapping,
        'preview': df.head(5).to_dict('records'),
        'ai_confidence': confidence,
        'warnings': warnings,
    }
```

#### 9.3 Fallback al metodo legacy

Si la API falla o tiene baja confidence (<0.6), cae al keyword matching. Esto garantiza que el sistema siga funcionando incluso sin IA.

### Entregable
- IA integrada en flujo Excel actual
- Metrica comparativa: % aciertos con keyword vs IA (para tesis)
- UI muestra "🤖 Mapeado automaticamente con IA (confianza: 95%)"
- Commit: `feat: AI-powered Excel column mapping`

---

## Fase 10: Insights narrativos del dashboard (1 dia)

### Caso de uso

Dashboard admin ya tiene metricas (certificados, descargas, etc). Agregar un panel "💡 Insights IA" que genera narrativa ejecutiva.

### Implementacion

```python
# core/services/ai/insights.py
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count, Avg
from core.models import Certificado, SesionAsistencia, ConfirmacionAsistencia, RegistroAsistencia
from .client import call_claude

INSIGHTS_SYSTEM_PROMPT = """Eres un analista de datos ejecutivo para una universidad. Recibes metricas del sistema de certificados y generas 3-5 insights accionables en español.

REGLAS:
1. Cada insight es 1-2 oraciones concretas.
2. Menciona numeros especificos.
3. Identifica tendencias (↑, ↓, estable).
4. Sugiere acciones donde aplique.
5. Formato: lista de objetos con campos tipo, titulo, texto, prioridad.
6. Tipos: tendencia, anomalia, oportunidad, alerta.
7. Prioridades: alta, media, baja.
8. Responde SOLO JSON valido."""

def get_dashboard_metrics():
    """Recolecta metricas brutas para analizar."""
    now = timezone.now()
    last_30 = now - timedelta(days=30)
    prev_30 = now - timedelta(days=60)

    certs_this_month = Certificado.objects.filter(created_at__gte=last_30).count()
    certs_prev_month = Certificado.objects.filter(created_at__gte=prev_30, created_at__lt=last_30).count()

    sesiones_recientes = SesionAsistencia.objects.filter(fecha__gte=last_30.date())
    confirmados = ConfirmacionAsistencia.objects.filter(sesion__in=sesiones_recientes).count()
    asistieron = RegistroAsistencia.objects.filter(sesion__in=sesiones_recientes).count()

    top_lotes = list(
        Certificado.objects.values('lote__nombre_lote')
        .annotate(total_descargas=Count('descargas_count'))
        .order_by('-total_descargas')[:3]
    )

    return {
        "mes_actual": {
            "certificados_emitidos": certs_this_month,
            "cambio_vs_anterior_pct": round((certs_this_month - certs_prev_month) / max(certs_prev_month, 1) * 100, 1),
        },
        "sesiones_mes": sesiones_recientes.count(),
        "confirmados_vs_asistieron": {
            "confirmados": confirmados,
            "asistieron": asistieron,
            "tasa_asistencia_pct": round(asistieron / max(confirmados, 1) * 100, 1),
        },
        "top_lotes_descargados": top_lotes,
    }

def generate_insights():
    metrics = get_dashboard_metrics()
    response = call_claude(
        system=INSIGHTS_SYSTEM_PROMPT,
        user=f"Metricas actuales:\n{json.dumps(metrics, indent=2)}",
        max_tokens=1500,
    )
    return json.loads(response)
```

### Cache

Los insights se regeneran una vez por dia (no en cada request):

```python
from django.core.cache import cache

def get_cached_insights():
    cached = cache.get('dashboard_insights')
    if cached:
        return cached
    insights = generate_insights()
    cache.set('dashboard_insights', insights, 60 * 60 * 12)  # 12h
    return insights
```

### UI

Panel en dashboard con cards tipo:

```
┌─────────────────────────────────────────────┐
│ 📈 TENDENCIA (alta)                         │
│ Emision de certificados subio 23% este mes │
│ Pasaste de 380 a 467 certificados emitidos.│
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ ⚠️ ALERTA (media)                           │
│ 35% de confirmados no asistieron            │
│ Considera implementar recordatorios 24h    │
│ antes del evento para subir la asistencia. │
└─────────────────────────────────────────────┘
```

### Entregable
- Endpoint `/api/v1/ai/insights/dashboard/`
- UI en dashboard admin con cards
- Cache de 12h
- Commit: `feat: AI-generated dashboard insights`

---

## Fase 11: Recomendaciones con embeddings (2-3 dias)

### Caso de uso

Participante abre la landing o sus detalles. Ve una seccion "Eventos recomendados para ti" basada en seminarios a los que asistio antes (content-based filtering).

### Arquitectura

```
Al crear un LoteCertificados:
  1. Se extrae: nombre_lote + cuerpo_certificado + facultad
  2. Se genera embedding via OpenAI (1536 dim)
  3. Se guarda en SeminarioEmbedding (pgvector o JSON)

Al querer recomendaciones:
  1. Se obtienen todos los lotes asistidos por el participante
  2. Se promedia sus embeddings → perfil del participante
  3. Se calcula similaridad coseno con eventos futuros
  4. Top 3 con mayor similaridad
```

### Implementacion

#### 11.1 Modelo nuevo

```python
# core/models.py
class SeminarioEmbedding(TimestampedModel):
    lote = models.OneToOneField(LoteCertificados, on_delete=models.CASCADE, related_name='embedding')
    vector = models.JSONField()  # lista de 1536 floats
    texto_indexado = models.TextField()
    modelo = models.CharField(max_length=50, default='text-embedding-3-small')

    class Meta:
        indexes = [
            models.Index(fields=['-updated_at']),
        ]
```

#### 11.2 Servicio de embeddings

```python
# core/services/recommender/embeddings.py
import os
from openai import OpenAI
from functools import lru_cache

@lru_cache
def get_openai_client():
    return OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def get_embedding(text: str, model: str = "text-embedding-3-small") -> list:
    client = get_openai_client()
    text = text.replace("\n", " ")
    response = client.embeddings.create(input=[text], model=model)
    return response.data[0].embedding

def build_text_from_lote(lote) -> str:
    parts = [
        lote.nombre_lote,
        lote.get_facultad_display() or '',
        (lote.cuerpo_certificado or '')[:500],
    ]
    return ' — '.join(filter(None, parts))
```

#### 11.3 Engine de recomendaciones

```python
# core/services/recommender/engine.py
import numpy as np

def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def get_user_profile_vector(participante):
    """Promedio de embeddings de eventos asistidos."""
    lotes_asistidos = LoteCertificados.objects.filter(
        certificados__participante=participante,
        embedding__isnull=False
    ).distinct()

    vectors = [np.array(l.embedding.vector) for l in lotes_asistidos]
    if not vectors:
        return None
    return np.mean(vectors, axis=0).tolist()

def recommend_for_participante(participante, top_n=3):
    profile = get_user_profile_vector(participante)
    if not profile:
        # Cold start: mostrar mas populares
        return get_most_popular_upcoming(top_n)

    upcoming_sesiones = SesionAsistencia.objects.filter(
        fecha__gte=timezone.now().date(),
        activa=True,
        lote__embedding__isnull=False
    ).select_related('lote__embedding')

    scored = []
    for sesion in upcoming_sesiones:
        score = cosine_similarity(profile, sesion.lote.embedding.vector)
        scored.append((sesion, score))

    scored.sort(key=lambda x: -x[1])
    return scored[:top_n]
```

#### 11.4 "Razon" de la recomendacion (LLM)

```python
# core/services/recommender/reason.py
def generate_reason(participante, recommended_lote):
    historial = [c.lote.nombre_lote for c in participante.certificados.all()[:5]]
    user_msg = f"""Un participante asistio a: {', '.join(historial)}.
Le vamos a recomendar: {recommended_lote.nombre_lote}.
Genera una razon breve (max 20 palabras) de por que le interesaria."""

    return call_claude(
        system="Genera razones de recomendacion de eventos academicos. Tono cercano y breve.",
        user=user_msg,
        max_tokens=60,
    )
```

#### 11.5 Comando para rebuild

```python
# core/management/commands/rebuild_embeddings.py
from django.core.management.base import BaseCommand
from core.models import LoteCertificados, SeminarioEmbedding
from core.services.recommender.embeddings import get_embedding, build_text_from_lote

class Command(BaseCommand):
    help = 'Regenera embeddings de todos los lotes'

    def handle(self, *args, **options):
        lotes = LoteCertificados.objects.all()
        for lote in lotes:
            text = build_text_from_lote(lote)
            vector = get_embedding(text)
            SeminarioEmbedding.objects.update_or_create(
                lote=lote,
                defaults={'vector': vector, 'texto_indexado': text}
            )
            self.stdout.write(f'OK: {lote.nombre_lote}')
```

#### 11.6 Endpoint

```python
# api/recommendations/views.py
class RecommendationsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, email):
        try:
            participante = Participante.objects.get(email__iexact=email)
        except Participante.DoesNotExist:
            return Response({'recommendations': get_most_popular_upcoming()})

        scored = recommend_for_participante(participante)
        results = [
            {
                'sesion_id': s.id,
                'lote': s.lote.nombre_lote,
                'fecha': s.fecha.isoformat(),
                'similarity_score': score,
                'razon': generate_reason(participante, s.lote),
            }
            for s, score in scored
        ]
        return Response({'recommendations': results})
```

### Entregable
- Sistema de embeddings funcional
- `python manage.py rebuild_embeddings` procesa todos los lotes
- Endpoint publico de recomendaciones
- UI en public landing con "Para ti" cards
- Commit: `feat: content-based event recommendations with embeddings`

---

## Fase 12: Comandos de voz para crear eventos (3-5 dias)

### Caso de uso

Admin presiona 🎤, dice: *"Crear sesion seminario de IA aplicada a salud el viernes 20 de junio de 3 a 6 pm para 50 personas"*. La IA extrae entidades y llena el formulario automaticamente. Si falta algo, pregunta.

### Arquitectura

```
Browser (Web Speech API) → Transcripcion texto
          ↓
POST /api/v1/ai/voice/extract
          ↓
Claude extrae entidades (JSON estructurado)
          ↓
Frontend llena el form
          ↓
Si faltan campos criticos, los lista y pide completar
          ↓
Admin confirma → POST al endpoint de crear sesion
```

### Implementacion

#### 12.1 Servicio de extraccion

```python
# core/services/ai/voice.py
import json
from datetime import datetime
from .client import call_claude

VOICE_SYSTEM_PROMPT = """Eres un asistente que extrae informacion estructurada de comandos de voz en español para crear sesiones/eventos academicos.

ENTIDADES A EXTRAER:
- titulo: nombre del evento
- descripcion: detalle opcional
- fecha: formato YYYY-MM-DD
- hora_inicio: formato HH:MM 24h
- hora_fin: formato HH:MM 24h
- capacidad: numero entero o null (ilimitada)
- lugar: descripcion del lugar
- solo_lideres: boolean (true si menciona "solo para lideres")

CONTEXTO:
- Fecha actual: {fecha_actual}
- Dia semana: {dia_semana}

REGLAS:
1. Si la persona dice "el viernes", calcula la fecha del proximo viernes.
2. Si dice "de 3 a 6 pm", interpreta como 15:00 y 18:00.
3. Si dice "para X personas", es la capacidad.
4. Si NO menciona un campo, devuelvelo como null.
5. Identifica cuales son CRITICOS que faltan para crear la sesion:
   - Criticos obligatorios: titulo, fecha, hora_inicio

Formato respuesta (SOLO JSON):
{
  "entidades": {
    "titulo": "string o null",
    "descripcion": "string o null",
    "fecha": "YYYY-MM-DD o null",
    ...
  },
  "faltantes_criticos": ["campo1", "campo2"],
  "faltantes_opcionales": ["lugar"],
  "preguntas_sugeridas": ["¿Hasta que hora?", "¿Cual es la capacidad?"]
}"""

def extract_entities_from_voice(transcripcion: str) -> dict:
    hoy = datetime.now()
    system = VOICE_SYSTEM_PROMPT.format(
        fecha_actual=hoy.strftime('%Y-%m-%d'),
        dia_semana=hoy.strftime('%A')
    )

    response = call_claude(
        system=system,
        user=f"Transcripcion del usuario: \"{transcripcion}\"",
        max_tokens=1024
    )

    return json.loads(response)
```

#### 12.2 Endpoint

```python
# api/ai/views.py
class VoiceExtractView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        transcripcion = request.data.get('transcripcion', '').strip()
        if not transcripcion:
            return Response({'error': 'Transcripcion vacia'}, status=400)

        result = extract_entities_from_voice(transcripcion)
        return Response(result)
```

#### 12.3 UI en crear sesion

```html
<!-- admin_panel/templates/panel/sessions/create.html -->
<button type="button" onclick="startVoice()" class="bg-gradient-to-r from-red-500 to-pink-500 text-white px-4 py-2 rounded-xl">
    🎤 Crear por voz
</button>

<div id="voiceStatus" class="hidden">
    <p>🎙️ Escuchando... habla claramente</p>
    <p id="transcriptionLive"></p>
</div>

<script>
let recognition;

function startVoice() {
    if (!('webkitSpeechRecognition' in window)) {
        alert('Tu navegador no soporta reconocimiento de voz');
        return;
    }

    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'es-EC';

    recognition.onresult = (event) => {
        const transcript = Array.from(event.results).map(r => r[0].transcript).join('');
        document.getElementById('transcriptionLive').textContent = transcript;

        if (event.results[event.results.length - 1].isFinal) {
            processTranscription(transcript);
        }
    };

    recognition.start();
    document.getElementById('voiceStatus').classList.remove('hidden');
}

async function processTranscription(transcript) {
    const res = await fetch('/api/v1/ai/voice/extract/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
            'Authorization': 'Bearer ' + getJwtToken(),
        },
        body: JSON.stringify({ transcripcion: transcript })
    });
    const data = await res.json();

    // Llenar form con entidades
    Object.keys(data.entidades).forEach(key => {
        const input = document.querySelector(`[name="${key}"]`);
        if (input && data.entidades[key]) {
            input.value = data.entidades[key];
            input.classList.add('ring-2', 'ring-green-500');  // highlight
        }
    });

    // Si faltan criticos, pedirlos
    if (data.faltantes_criticos.length > 0) {
        alert(`Faltan: ${data.faltantes_criticos.join(', ')}`);
        // Opcional: TTS
        const msg = new SpeechSynthesisUtterance(`Falta ${data.faltantes_criticos[0]}, por favor completalo`);
        msg.lang = 'es-EC';
        speechSynthesis.speak(msg);
    }
}
</script>
```

### Fallback a Whisper

Si Web Speech API no funciona (Firefox, Safari, ambientes ruidosos):

```python
# core/services/ai/voice.py
def transcribe_with_whisper(audio_file):
    from openai import OpenAI
    client = OpenAI()
    with open(audio_file, 'rb') as f:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            language="es"
        )
    return response.text
```

### Entregable
- Creacion de sesion por voz end-to-end
- Extraccion de entidades con Claude
- UI con highlight de campos llenados por IA
- Opcional: TTS para preguntar lo faltante
- Documentacion con ejemplos de frases soportadas
- Commit: `feat: voice-controlled session creation with AI entity extraction`
