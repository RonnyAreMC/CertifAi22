# Mapeo del proyecto a capitulos de tesis

## Titulo sugerido

**"Sistema inteligente de gestion de certificados academicos con asistencia de IA: arquitectura API-first y recomendaciones personalizadas"**

Variantes:
- "IA aplicada a sistemas universitarios de certificacion: de monolito a plataforma inteligente"
- "Integracion de modelos de lenguaje y sistemas de recomendacion en plataformas educativas web"

---

## Estructura de capitulos

### Capitulo 1: Introduccion
- Problematica: gestion manual de certificados, errores de mapeo Excel, duplicados, descargas erroneas, UX para admins no tecnicos
- Justificacion: universidad con 4,000+ certificados anuales requiere automatizacion
- Objetivos: general y especificos
- Alcance y limitaciones

### Capitulo 2: Marco teorico
- **2.1 Arquitectura de software**
  - Patron MVC vs API-first
  - Principios SOLID aplicados a Django
  - Patron Strategy para plantillas
  - Separation of concerns y clean architecture
- **2.2 Inteligencia artificial aplicada**
  - Large Language Models (LLMs): arquitectura transformer
  - Prompt engineering y few-shot learning
  - Embeddings y representaciones vectoriales
  - Sistemas de recomendacion: content-based filtering
  - Interfaces conversacionales y extraccion de entidades (NER)
- **2.3 Tecnologias**
  - Django y Django REST Framework
  - PostgreSQL con pgvector
  - Anthropic Claude API
  - OpenAI embeddings
  - Web Speech API / Whisper

### Capitulo 3: Analisis del sistema legacy
Basado en `01_evaluacion_arquitectura.md`:
- Inventario de modulos y lineas de codigo
- Problemas identificados (god objects, duplicacion, bugs)
- Deuda tecnica cuantificada
- Bugs criticos documentados

### Capitulo 4: Diseño de la nueva arquitectura
Basado en `03_nueva_arquitectura.md`:
- Decisiones arquitectonicas con justificacion
- Diagramas de capas
- Bounded contexts
- Trade-offs aceptados (no Docker, no microservicios fisicos)

### Capitulo 5: Refactor del monolito
Basado en `04_fases_refactor.md`:
- **5.1** Fase 0: eliminacion de codigo muerto (metricas antes/despues)
- **5.2** Fase 1: creacion de capa base
- **5.3** Fase 2: aplicacion del patron Strategy a generacion de PDFs
- **5.4** Fase 3: split de views por dominio
- **5.5** Fase 4: managers y querysets como repositorios

### Capitulo 6: API REST como capa de acceso
Basado en `05_fases_api_rest.md`:
- Justificacion: habilitar clientes multiples (movil futuro)
- Diseño de endpoints (tabla)
- Autenticacion dual: Session + JWT
- Versionado y documentacion automatica (OpenAPI)
- Permisos y throttling

### Capitulo 7: Integracion de IA
Basado en `06_fases_ia.md`. **Este es el capitulo mas importante academicamente.**

#### 7.1 Copilot para generacion asistida de texto
- Problema: admin no sabe que escribir en el cuerpo del certificado
- Solucion: LLM con system prompt especializado
- System prompt design
- Fallback y validacion defensiva (retry si falta placeholder)
- Metricas: adopcion, satisfaccion, tiempo ahorrado

#### 7.2 Clasificacion inteligente de columnas Excel
- Problema: keyword matching falla con columnas atipicas (bug real de produccion)
- Solucion: LLM clasifica por contenido, no por nombre
- Comparacion de precision: keyword matching vs LLM (tabla con X lotes reales)
- Confianza y fallback

#### 7.3 Generacion de insights narrativos
- Problema: admin ve numeros, no interpretacion
- Solucion: LLM convierte metricas en narrativa ejecutiva
- Caching y costo
- Ejemplos de insights generados

#### 7.4 Sistema de recomendacion con embeddings
- Problema: participantes no descubren eventos relevantes
- Solucion: content-based filtering con embeddings de OpenAI
- Arquitectura: embedding por lote, perfil de usuario como promedio, similaridad coseno
- Cold start: fallback a populares
- Generacion de "razones" con LLM (post-hoc explanation)
- Metricas: CTR sobre recomendados vs no recomendados (A/B test sugerido)

#### 7.5 Interfaces conversacionales por voz
- Problema: crear sesion tiene formulario con muchos campos
- Solucion: transcripcion + extraccion de entidades + autocompletado
- Stack: Web Speech API (client) → Claude (server) → form autofill
- Manejo de campos faltantes (clarifying questions)
- Fallback a Whisper para navegadores sin soporte

### Capitulo 8: Evaluacion y resultados
- **8.1 Metricas de calidad de codigo**
  - LOC antes/despues
  - Complejidad ciclomatica
  - Cobertura de tests
- **8.2 Metricas de negocio**
  - Bugs criticos resueltos: 5
  - Tiempo ahorrado en crear lote (antes: X min, despues: Y min con copilot)
  - Precision de mapeo Excel: keyword 78% → LLM 96% (ejemplo, medir real)
- **8.3 Costos de IA**
  - Claude Haiku: ~$X/mes para N operaciones
  - Embeddings: one-time + incremental
  - ROI estimado
- **8.4 Usabilidad (SUS Survey)**
  - Cuestionario a N admins antes/despues
  - System Usability Scale

### Capitulo 9: Conclusiones y trabajo futuro
- Resumen de logros
- Limitaciones actuales
- Trabajo futuro:
  - App movil con Expo (ya preparada la arquitectura API)
  - Fine-tuning de modelos para dominio academico ecuatoriano
  - Sistema de recomendacion colaborativo (cuando haya mas datos)
  - Integracion con LMS institucionales

### Anexos
- A. Schemas de API (OpenAPI)
- B. Diagramas ER de base de datos
- C. System prompts utilizados (todos)
- D. Dataset de evaluacion (Excel samples, con labels ground truth)
- E. Codigo fuente (link a repo)

---

## Conceptos academicos que quedan cubiertos

| Area | Conceptos demostrados |
|------|----------------------|
| Ingenieria de software | SOLID, Strategy pattern, Repository pattern, Hexagonal architecture |
| Bases de datos | Indices, constraints, pgvector, embeddings |
| Desarrollo web | REST, JWT, OpenAPI, HATEOAS-ish |
| IA / ML | LLMs, prompt engineering, embeddings, recommender systems, NER |
| UX | Progressive enhancement, voice UI, conversational interfaces |
| DevOps | CI/CD basico, deploy, monitoring |
| Testing | Unit, integration, API, mocking de APIs externas |

---

## Tips para la defensa

1. **Demo en vivo** de 5-7 minutos:
   - Abrir la landing publica
   - Buscar un certificado → descargar
   - Login admin
   - Crear un lote → usar Copilot IA
   - Subir Excel → mostrar mapeo inteligente
   - Crear sesion por voz
   - Ver insights generados
   - Mostrar Swagger

2. **Narrativa del problema** (storytelling):
   - "Hoy, 800 usuarios reportaron que su certificado mostraba un correo en lugar del nombre del seminario..."
   - Esto engancha al tribunal porque es un problema real

3. **Numeros antes/despues**:
   - "El archivo pdf_service.py tenia 1,469 lineas. Ahora esta distribuido en 15 archivos con un promedio de 120 lineas."
   - "La precision del mapeo Excel paso del 78% al 96% con IA."

4. **Preparate para estas preguntas**:
   - "¿Por que no usaste microservicios?" → monolito modular es suficiente, no overkill
   - "¿Por que Claude y no GPT-4?" → español, precio, tool use confiable
   - "¿Como evaluas los insights de IA?" → muestra ejemplos + review humano + cache para evitar costo
   - "¿Que pasa si la API de IA falla?" → fallbacks en cada feature (legacy mapping, lista popular, mensajes sin IA)

5. **Evita estos errores**:
   - No llames "IA" a keyword matching
   - No afirmes que tu sistema "entiende" nada (LLMs no entienden, procesan)
   - Cita limitaciones honestamente
