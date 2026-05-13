# Modelo de Base de Datos · CertifAI

Diagrama entidad-relación (ERD) generado a partir del esquema actual.

> Para renderizarlo:
> - **GitHub**: se renderiza automáticamente al abrir este archivo en el repo
> - **VSCode**: instalar extensión _Markdown Preview Mermaid Support_ y abrir preview
> - **Online**: copiar el bloque mermaid a https://mermaid.live
> - **PNG**: en mermaid.live → Actions → Export PNG/SVG

---

## ERD por dominios

```mermaid
erDiagram
    %% ════════════════════════════════════════════════════════════
    %% USUARIOS DEL SISTEMA (admin panel)
    %% ════════════════════════════════════════════════════════════
    USUARIO {
        int id PK
        string username UK
        string email
        string password
        string rol "superadmin|admin"
        string facultad
        string telefono
        bool is_active
        datetime fecha_creacion
        datetime ultimo_acceso
    }
    SOLICITUD_ACCESO {
        int id PK
        string nombres
        string apellidos
        string email UK
        string telefono
        string facultad
        string estado "pendiente|aprobado|rechazado"
        int usuario_creado_id FK
        int aprobado_por_id FK
        datetime fecha_solicitud
        text motivo_rechazo
    }

    %% ════════════════════════════════════════════════════════════
    %% CATÁLOGOS (tablas lookup editables)
    %% ════════════════════════════════════════════════════════════
    FACULTAD {
        int id PK
        string codigo UK
        string nombre
        text descripcion
        int orden
        bool activa
    }

    %% ════════════════════════════════════════════════════════════
    %% PARTICIPANTES (usuarios finales)
    %% ════════════════════════════════════════════════════════════
    PARTICIPANTE {
        int id PK
        string cedula UK
        string nombres
        string apellidos
        string email UK
        string celular
        bool es_lider
        string password_hash
        image avatar
        datetime last_login
        datetime created_at
    }
    PARTICIPANTE_TOKEN {
        int id PK
        int participante_id FK
        string key UK
        datetime expires_at
        datetime last_used_at
        string user_agent
    }

    %% ════════════════════════════════════════════════════════════
    %% CERTIFICADOS Y DISEÑO
    %% ════════════════════════════════════════════════════════════
    LOTE_CERTIFICADOS {
        int id PK
        string nombre_lote
        int administrador_id FK
        string facultad
        file archivo_excel
        bool personalizar_diseno
        string plantilla
        string color_primario
        string color_secundario
        text cuerpo_certificado
        int firma_inst_1_id FK
        int firma_inst_2_id FK
        int firma_inst_3_id FK
        int firma_inst_4_id FK
        bool activo
        datetime fecha_creacion
    }
    CERTIFICADO {
        int id PK
        int lote_id FK
        int participante_id FK
        string cedula
        string nombres
        string apellidos
        string email
        string curso
        date fecha_curso
        int horas
        string hash_verificacion UK
        file pdf_generado
        int descargas_count
        int veces_buscado
        datetime created_at
    }
    FIRMA_INSTITUCIONAL {
        int id PK
        string nombre
        string cargo
        text imagen "base64 ⚠ migrar a ImageField"
        bool activa
        int orden
    }
    DISENO_GLOBAL {
        int id PK
        string plantilla
        string color_primario
        text cuerpo_certificado
        int firma_inst_1_id FK
        int firma_inst_2_id FK
        int firma_inst_3_id FK
    }

    %% ════════════════════════════════════════════════════════════
    %% SESIONES Y ASISTENCIA
    %% ════════════════════════════════════════════════════════════
    SESION_ASISTENCIA {
        int id PK
        int lote_id FK
        string titulo
        text descripcion
        image imagen_banner
        string modalidad "presencial|virtual"
        string plataforma_virtual
        url enlace_virtual
        string lugar
        date fecha
        time hora_inicio
        time hora_fin
        string codigo_qr UK
        int capacidad
        bool solo_lideres
        bool activa
        string google_calendar_event_id
        bool transcripcion_habilitada
    }
    PONENTE {
        int id PK
        int sesion_id FK
        string nombre
        string titulo
        string afiliacion
        text bio
        int orden
    }
    REGISTRO_ASISTENCIA {
        int id PK
        int sesion_id FK
        int participante_id FK
        int certificado_id FK
        datetime fecha_registro
        ip ip_address
    }
    CONFIRMACION_ASISTENCIA {
        int id PK
        int sesion_id FK
        int participante_id FK
        int certificado_id FK
        bool confirmado
        bool bloqueado
        datetime fecha_confirmacion
    }

    %% ════════════════════════════════════════════════════════════
    %% PIPELINE IA (resumen + cuestionario)
    %% ════════════════════════════════════════════════════════════
    RESUMEN_SESION {
        int id PK
        int sesion_id FK_UK
        string drive_file_id
        string drive_file_name
        text transcript_raw
        text resumen_md
        json puntos_clave
        json proximos_pasos
        json cuestionario
        int duracion_minutos
        string estado "pendiente|buscando|procesando|listo|fallido"
        text error_msg
        string ai_model
        int ai_input_tokens
        int ai_output_tokens
        datetime procesado_at
    }
    INTENTO_CUESTIONARIO {
        int id PK
        int participante_id FK
        int sesion_id FK
        int correctas
        int total
        int tiempo_total_seg
        json respuestas
        datetime created_at
    }

    %% ════════════════════════════════════════════════════════════
    %% INTEGRACIONES (Google + IA)
    %% ════════════════════════════════════════════════════════════
    GOOGLE_CREDENTIAL {
        int id PK
        string email UK
        text access_token "🔐 Fernet"
        text refresh_token "🔐 Fernet"
        url token_uri
        string client_id
        string client_secret "🔐 Fernet"
        json scopes
        datetime expiry
    }
    AI_CONFIG {
        int id PK_singleton
        string provider "claude|openai|groq"
        string model
        string api_key "🔐 Fernet"
        float temperature
        int max_tokens
        text system_prompt_override
        bool enabled
    }

    %% ════════════════════════════════════════════════════════════
    %% AUDITORÍA Y DISEÑO UI
    %% ════════════════════════════════════════════════════════════
    AUDITORIA {
        int id PK
        int usuario_id FK
        string accion "CREAR|EDITAR|ELIMINAR|..."
        text detalle
        int content_type_id FK
        int object_id
        json cambios "diff antes/después"
        ip ip
        string user_agent
        datetime fecha
    }
    UI_DESIGN_TOKENS {
        int id PK_singleton
        string color_brand
        string color_brand_dark
        string color_accent
    }

    %% ════════════════════════════════════════════════════════════
    %% RELACIONES
    %% ════════════════════════════════════════════════════════════

    %% Solicitudes ↔ Usuario
    SOLICITUD_ACCESO ||--o| USUARIO : "se aprueba como"
    SOLICITUD_ACCESO }o--o| USUARIO : "aprobada por"

    %% Participante ↔ todo lo del participante
    PARTICIPANTE ||--o{ PARTICIPANTE_TOKEN : "sesiones mobile"
    PARTICIPANTE ||--o{ CONFIRMACION_ASISTENCIA : "se inscribe"
    PARTICIPANTE ||--o{ REGISTRO_ASISTENCIA : "asiste"
    PARTICIPANTE ||--o{ CERTIFICADO : "recibe"
    PARTICIPANTE ||--o{ INTENTO_CUESTIONARIO : "intenta"

    %% Lote ↔ Certificado ↔ Sesion
    LOTE_CERTIFICADOS ||--o{ CERTIFICADO : "contiene"
    LOTE_CERTIFICADOS ||--o{ SESION_ASISTENCIA : "tiene sesiones"
    LOTE_CERTIFICADOS }o--o| USUARIO : "creado por"
    LOTE_CERTIFICADOS }o--o| FIRMA_INSTITUCIONAL : "firma 1..4 ⚠"

    %% Diseño global ↔ Firmas
    DISENO_GLOBAL }o--o| FIRMA_INSTITUCIONAL : "firma 1..3 ⚠"

    %% Sesión ↔ Asistencia ↔ Resumen
    SESION_ASISTENCIA ||--o{ PONENTE : "tiene"
    SESION_ASISTENCIA ||--o{ REGISTRO_ASISTENCIA : "asistencias"
    SESION_ASISTENCIA ||--o{ CONFIRMACION_ASISTENCIA : "inscritos"
    SESION_ASISTENCIA ||--|| RESUMEN_SESION : "1:1 resumen IA"
    SESION_ASISTENCIA ||--o{ INTENTO_CUESTIONARIO : "cuestionarios"

    %% Auditoría
    USUARIO ||--o{ AUDITORIA : "ejecuta acciones"
```

---

## Leyenda de notaciones

| Símbolo | Significado |
|---|---|
| `PK` | Primary Key |
| `UK` | Unique Key |
| `FK` | Foreign Key |
| `FK_UK` | FK con constraint único (relación 1:1) |
| `PK_singleton` | Singleton (siempre `pk=1`) |
| 🔐 Fernet | Campo cifrado at-rest |
| ⚠ | Pendiente de refactor (firmas repetidas / base64) |

### Cardinalidades Mermaid

| Notación | Significado |
|---|---|
| `||--o{` | Uno a muchos (1:N) |
| `||--||` | Uno a uno obligatorio (1:1) |
| `||--o|` | Uno a uno opcional |
| `}o--o|` | Muchos a uno opcional |
| `}o--||` | Muchos a uno obligatorio |

---

## Resumen estadístico

| Métrica | Valor |
|---|---|
| Tablas totales | **20** |
| Catálogos lookup | 1 (`Facultad`) |
| Singletons | 3 (`DisenoGlobal`, `AIConfig`, `UIDesignTokens`) |
| Relaciones 1:1 | 2 (`Sesion ↔ Resumen`, `Solicitud ↔ Usuario`) |
| Relaciones 1:N principales | 12 |
| Campos cifrados (Fernet) | 4 (`api_key`, `access_token`, `refresh_token`, `client_secret`) |
| Índices declarados explícitos | ~25 |

---

## Dominios funcionales

```
┌──────────────────────────────────────────────────────────────────┐
│                        CertifAI · Dominios                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────┐      ┌─────────────────┐                  │
│   │ ADMINISTRACIÓN  │      │  CATÁLOGOS      │                  │
│   │  · Usuario      │      │  · Facultad     │                  │
│   │  · Solicitud    │      │  · (TextChoices)│                  │
│   └────────┬────────┘      └─────────────────┘                  │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────────────────────────────┐                   │
│   │           PARTICIPANTES                  │                   │
│   │  · Participante                          │                   │
│   │  · ParticipanteToken (auth mobile)       │                   │
│   └────────┬──────────────┬──────────────────┘                   │
│            │              │                                       │
│            ▼              ▼                                       │
│   ┌─────────────┐  ┌──────────────────┐                          │
│   │ CERTIFICADOS │  │   SESIONES        │                         │
│   │ · Lote       │──│   · Sesión        │                         │
│   │ · Certificado│  │   · Ponente       │                         │
│   │ · FirmaInst  │  │   · Confirmación  │                         │
│   │ · Diseño     │  │   · Registro      │                         │
│   └─────────────┘  └────┬─────────────┬┘                         │
│                         │             │                          │
│                         ▼             ▼                          │
│              ┌──────────────────┐  ┌──────────────────┐          │
│              │   PIPELINE IA    │  │   INTEGRACIONES  │          │
│              │   · ResumenSes   │  │   · GoogleCred   │ 🔐       │
│              │   · IntentoQuiz  │◀─│   · AIConfig     │ 🔐       │
│              └──────────────────┘  └──────────────────┘          │
│                                                                  │
│                  ┌──────────────────┐                            │
│                  │    AUDITORÍA     │  (cross-domain)            │
│                  │  · Auditoría     │                            │
│                  │    (ContentType) │                            │
│                  └──────────────────┘                            │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Flujos principales (lectura cruzada del ERD)

### 1. Flujo de certificación
```
Usuario admin → crea LoteCertificados → carga Excel
       ↓
   genera N × Certificado (uno por Participante)
       ↓
   participante consulta via /verify/<hash>/  →  Certificado.descargas_count++
```

### 2. Flujo de evento + asistencia
```
Usuario admin → crea SesionAsistencia (vinculada a Lote opcionalmente)
       ↓                          ↓
agrega Ponentes        Participante escanea QR → RegistroAsistencia
       ↓
si transcripcion_habilitada=True:
   Celery Beat (30min) → busca transcript en Drive → genera ResumenSesion
       ↓
   Participante hace cuestionario → IntentoCuestionario
```

### 3. Flujo de IA (resumen + Q&A)
```
SesionAsistencia
   └─→ ResumenSesion (1:1, lazy)
         ├─→ resumen_md (Markdown)
         ├─→ puntos_clave (JSON list)
         ├─→ proximos_pasos (JSON list)
         └─→ cuestionario (JSON: [{pregunta, opciones, correcta_idx, explicacion}])
                  └─→ IntentoCuestionario (N por Participante, máx 2)
```

---

## Mejoras pendientes (refactor futuro)

| # | Mejora | Impacto |
|---|---|---|
| ⚠ 1 | Firmas 1..4 en `LoteCertificados` / `DisenoGlobal` → tabla pivote `LoteFirma` | Normalización 1NF |
| ⚠ 2 | `FirmaInstitucional.imagen` base64 (TextField) → `ImageField` con archivo en media | Performance + storage |
| ⚠ 3 | `RegistroAsistencia.certificado` / `participante` nullable redundante (legacy) | Limpieza |
