# Certifai AI Minutes
### El evento termina. El contenido empieza.

---

## El problema que nadie está resolviendo

En la educación continua universitaria pasa algo absurdo:

> Se organizan eventos con ponentes de talla internacional. Asisten 200 personas virtualmente. Se graba la sesión. **Y todo ese conocimiento se muere el mismo día que terminó la reunión.**

Lo que existe hoy en el mejor de los casos:
- Un video de 2 horas que nadie va a volver a ver.
- Un PDF de asistencia que prueba que alguien "estuvo conectado".
- Un certificado que certifica presencia, no aprendizaje.

El 90% del valor educativo **se pierde** apenas el organizador cierra Zoom o Meet.

---

## La pregunta radical

**¿Y si cada evento virtual generara, automáticamente y sin intervención humana, el siguiente contenido?**

- Un **resumen ejecutivo** publicable, navegable, consultable.
- Un **timeline interactivo** con los momentos clave en timestamps clickeables.
- **10-15 preguntas y respuestas** generadas por IA para quien no pudo asistir.
- Los **highlights**: frases memorables, citables, con autor y minuto exacto.
- **Temas principales** etiquetados para búsqueda cruzada entre eventos.

**Todo eso. Publicado automático. En minutos. En tu sitio. Para siempre.**

Eso es lo que construimos.

---

## Cómo funciona en 30 segundos

```
   1. Admin crea evento en la plataforma
            ↓
   2. Plataforma genera link de Meet automáticamente
            ↓
   3. Ponentes y asistentes entran con ese link
            ↓
   4. Meet graba y transcribe (nativo de Google)
            ↓
   5. Plataforma detecta transcript nuevo en Drive
            ↓
   6. Claude AI procesa el transcript → resumen + Q&A + timeline
            ↓
   7. Página pública del evento se rellena sola
            ↓
   8. ∞
```

**El ponente no hace nada distinto. El admin no sube archivos. El asistente no llena formularios.** Todo es automático.

---

## Por qué esto es radical

### 1. Invierte el ciclo de vida del evento

Hoy: evento crea asistencia → asistencia genera certificado → fin.
Con esta idea: evento crea **contenido permanente** → contenido atrae nuevos estudiantes → genera **más eventos**.

Es un volante de crecimiento, no una métrica de cumplimiento.

### 2. Hace irrelevante la asistencia como KPI

Para eventos virtuales, "quién se conectó" es una métrica mentirosa. Mucha gente entra y se va a hacer otra cosa. Lo que importa es: **¿qué se aprendió?** Este sistema lo mide en contenido, no en logs de conexión.

### 3. Democratiza el conocimiento internacional

Un ponente del MIT da una charla a 200 personas en Milagro, Ecuador. Antes: 200 lo veían. Ahora: **200 lo viven, 20,000 lo consultan**. El resumen y Q&A se indexan en Google. Un estudiante de Loja que busca "IA ética" encuentra esa charla meses después.

### 4. Elimina la fricción de los ponentes internacionales

Los ponentes no necesitan cuenta UNEMI, no suben archivos, no graban localmente. Se unen al link como a cualquier Meet. El sistema hace todo por detrás. **Invitar a un ponente de Stanford es igual de fácil que invitar al de al lado.**

### 5. Convierte a la IA en infraestructura, no en gimmick

No hay "asistente IA que responde en el chat". No hay "predicción de deserción". La IA aquí hace **trabajo invisible**: lee, entiende, sintetiza, publica. Es un editor silencioso que convierte 2 horas de video en contenido consumible en 5 minutos.

---

## El valor en números

Imagina una facultad que organiza 30 eventos al año:

| Métrica | Hoy | Con AI Minutes |
|---|:---:|:---:|
| Tiempo manual post-evento | 3-4h por evento | 0 minutos |
| Contenido reutilizable generado | ~0 | ~30 resúmenes + 300 Q&As + 250 highlights |
| Alcance post-evento | 0 personas/mes | Indefinido (SEO + compartibles) |
| Costo por evento procesado | N/A | ~$0.05 en IA |
| Trabajo humano para mantenerlo | Inviable | 1 clic |

**Un año de eventos se convierte en una biblioteca navegable permanente.** Sin contratar a nadie nuevo. Sin pedir nada extra a los docentes.

---

## Lo que lo hace técnicamente elegante

La mayoría de "integraciones con Zoom/Meet" que existen en el mercado son pesadas:
- Bots que se unen a tu reunión (incómodo visualmente, límites de plan).
- SDKs propietarios costosos.
- Grabaciones que hay que subir manualmente.

Esta arquitectura **evita todo eso**:

- **Usa lo que Google YA hace gratis** (transcripción nativa de Workspace Education).
- **No necesita bots externos** — tu propia cuenta es el organizador, todo queda en tu Drive.
- **No duplica storage** — el video vive en Drive, solo se referencia.
- **Escalable por default** — las cuotas gratuitas de Google API cubren miles de eventos.

El costo marginal por evento procesado es **$0.05 en Claude API**. Nada más.

---

## Escenarios que desbloquea

### Para el estudiante
> "Perdí la charla del Dr. Martínez el martes. Abro Certifai, busco su nombre, leo el resumen en 3 minutos, veo las 10 preguntas que generó la IA. En 10 minutos tengo el 80% del valor de haber estado 2 horas."

### Para el docente
> "Di una clase magistral sobre ética de IA. Al día siguiente el sistema publica mi resumen automático. Lo comparto en LinkedIn. Me invitan a dar la misma charla en otra universidad."

### Para el director académico
> "¿Qué temas fueron más discutidos este semestre? El sistema me da una nube de temas clusterizados con la IA de todos los eventos. Puedo detectar tendencias, gaps curriculares, oportunidades."

### Para el estudiante externo que llegó por Google
> "Busqué 'modelos de lenguaje aplicados a educación' y encontré el evento del Dr. López en Certifai. No sabía que existía UNEMI. Me inscribí al siguiente evento."

---

## Por qué esto es una tesis, no solo un producto

Como trabajo académico, esta solución:

- **Integra 3 sistemas heterogéneos** (Google Workspace, Claude API, Django). Demuestra dominio de arquitecturas distribuidas.
- **Usa técnicas modernas de IA aplicada**: prompt engineering, prompt caching, structured output, multi-step reasoning.
- **Es evaluable cuantitativamente**: precisión del resumen vs humano, tiempo ahorrado, retención de contenido.
- **Tiene fundamento pedagógico**: la generación automática de Q&A se apoya en la taxonomía de Bloom (comprensión, aplicación, análisis).
- **Es replicable**: cualquier universidad con Google Workspace puede adoptarlo en semanas.
- **Genera contribución original**: no existe un sistema open-source equivalente para educación continua universitaria en español.

---

## Lo que se logra en 2 semanas de trabajo

Con la arquitectura ya diseñada en [09_meet_integration.md](./09_meet_integration.md), el MVP está a **10-14 días** de trabajo enfocado:

- Semana 1: OAuth con Google + Calendar API + descarga de transcripts + pipeline Claude.
- Semana 2: Detección automática + UI pública del resumen + testing end-to-end.

Todo dentro del cronograma de tesis. **Es factible y ambicioso a la vez** — la combinación exacta que un tribunal respeta.

---

## La apuesta

**Construimos esto y Certifai deja de ser "una plataforma de certificados" para convertirse en algo que no tiene nombre todavía:**

- No es LMS.
- No es herramienta de videoconferencia.
- No es un generador de notas con IA.

Es el **cerebro compartido** de una universidad. La capa que captura cada conversación educativa y la vuelve accesible, navegable, perpetua.

Cada evento que organiza UNEMI lo hace una institución más inteligente.
Cada evento que se pierde es contenido que no va a existir nunca.

---

## Una última cosa

Si esto te convence, el siguiente paso es pequeño:

1. Conectar la cuenta UNEMI al proyecto (una vez).
2. Crear una sesión virtual de prueba.
3. Hacer una reunión de 15 minutos de cualquier cosa.
4. Ver cómo, automáticamente, en tu página aparece un resumen con timeline y Q&A.

Ese momento — cuando veas tu primera reunión convertida en contenido sin haber tocado un solo archivo — es cuando entiendes que estamos construyendo algo diferente.

---

**Certifai AI Minutes**
*Porque el conocimiento no debería morir cuando termina la reunión.*
