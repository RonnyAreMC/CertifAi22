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

    USUARIO {
        int id PK
        string username UK
        string email
        string password
        string rol
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
        string estado
        int usuario_creado_id FK
        int aprobado_por_id FK
        datetime fecha_solicitud
        text motivo_rechazo
    }

    FACULTAD {
        int id PK
        string codigo UK
        string nombre
        text descripcion
        int orden
        bool activa
    }

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
        text imagen_base64
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

    SESION_ASISTENCIA {
        int id PK
        int lote_id FK
        string titulo
        text descripcion
        image imagen_banner
        string modalidad
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

    RESUMEN_SESION {
        int id PK
        int sesion_id FK
        string drive_file_id
        string drive_file_name
        text transcript_raw
        text resumen_md
        json puntos_clave
        json proximos_pasos
        json cuestionario
        int duracion_minutos
        string estado
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

    GOOGLE_CREDENTIAL {
        int id PK
        string email UK
        text access_token_cifrado
        text refresh_token_cifrado
        url token_uri
        string client_id
        string client_secret_cifrado
        json scopes
        datetime expiry
    }
    AI_CONFIG {
        int id PK
        string provider
        string model
        string api_key_cifrado
        float temperature
        int max_tokens
        text system_prompt_override
        bool enabled
    }

    AUDITORIA {
        int id PK
        int usuario_id FK
        string accion
        text detalle
        int content_type_id FK
        int object_id
        json cambios
        ip ip
        string user_agent
        datetime fecha
    }
    UI_DESIGN_TOKENS {
        int id PK
        string color_brand
        string color_brand_dark
        string color_accent
    }

    SOLICITUD_ACCESO ||--o| USUARIO : se_aprueba_como
    SOLICITUD_ACCESO }o--o| USUARIO : aprobada_por

    PARTICIPANTE ||--o{ PARTICIPANTE_TOKEN : tiene_sesiones
    PARTICIPANTE ||--o{ CONFIRMACION_ASISTENCIA : se_inscribe
    PARTICIPANTE ||--o{ REGISTRO_ASISTENCIA : asiste
    PARTICIPANTE ||--o{ CERTIFICADO : recibe
    PARTICIPANTE ||--o{ INTENTO_CUESTIONARIO : intenta

    LOTE_CERTIFICADOS ||--o{ CERTIFICADO : contiene
    LOTE_CERTIFICADOS ||--o{ SESION_ASISTENCIA : tiene_sesiones
    LOTE_CERTIFICADOS }o--o| USUARIO : creado_por
    LOTE_CERTIFICADOS }o--o| FIRMA_INSTITUCIONAL : firma_1_a_4

    DISENO_GLOBAL }o--o| FIRMA_INSTITUCIONAL : firma_1_a_3

    SESION_ASISTENCIA ||--o{ PONENTE : tiene_ponentes
    SESION_ASISTENCIA ||--o{ REGISTRO_ASISTENCIA : asistencias
    SESION_ASISTENCIA ||--o{ CONFIRMACION_ASISTENCIA : inscritos
    SESION_ASISTENCIA ||--|| RESUMEN_SESION : tiene_resumen
    SESION_ASISTENCIA ||--o{ INTENTO_CUESTIONARIO : cuestionarios

    USUARIO ||--o{ AUDITORIA : ejecuta_acciones
```

---

## Leyenda

| Notación | Significado |
|---|---|
| `PK` | Primary Key |
| `UK` | Unique Key (constraint UNIQUE) |
| `FK` | Foreign Key |
| `_cifrado` | Campo cifrado at-rest con Fernet (AES-128 + HMAC) |

### Cardinalidades Mermaid

| Notación | Significado |
|---|---|
| `||--o{` | Uno a muchos (1:N) |
| `||--||` | Uno a uno obligatorio (1:1) |
| `||--o|` | Uno a uno opcional |
| `}o--o|` | Muchos a uno opcional |

---

## Resumen estadístico

| Métrica | Valor |
|---|---|
| Tablas totales | **20** |
| Catálogos lookup | 1 (`Facultad`) |
| Singletons | 3 (`DisenoGlobal`, `AIConfig`, `UIDesignTokens`) |
| Relaciones 1:1 | 2 (`Sesion ↔ Resumen`, `Solicitud ↔ Usuario`) |
| Relaciones 1:N principales | 12 |
| Campos cifrados (Fernet) | 4 (api_key + 3 tokens Google) |
| Índices declarados | ~25 |

---

## Dominios funcionales

```
ADMINISTRACIÓN          CATÁLOGOS
 - Usuario               - Facultad
 - SolicitudAcceso       - (TextChoices)
       |
       v
 PARTICIPANTES
  - Participante
  - ParticipanteToken
       |
       +----------------+----------------+
       v                v                v
 CERTIFICADOS      SESIONES        PIPELINE IA
  - Lote            - Sesion         - ResumenSesion
  - Certificado     - Ponente        - IntentoCuestionario
  - FirmaInst       - Confirmacion         |
  - DisenoGlobal    - Registro             v
                                     INTEGRACIONES (cifradas)
                                      - GoogleCredential
                                      - AIConfig

 AUDITORIA (transversal con ContentType + diff JSON)
```

---

## Flujos principales

### 1. Certificación
```
Admin -> crea LoteCertificados -> carga Excel
        |
        v
    genera N Certificados (uno por Participante)
        |
        v
    Participante consulta via /verify/<hash>/  =>  descargas_count++
```

### 2. Evento + asistencia
```
Admin -> crea SesionAsistencia (con Ponentes)
        |
        v
    Participante escanea QR -> RegistroAsistencia
        |
        v
    Si transcripcion_habilitada:
        Celery Beat (cada 30 min) -> busca transcript Drive
            -> genera ResumenSesion (estado=listo)
        |
        v
    Participante hace Cuestionario -> IntentoCuestionario (max 2)
```

### 3. Pipeline IA
```
SesionAsistencia
   --> ResumenSesion (1:1)
         - resumen_md (Markdown)
         - puntos_clave (JSON list)
         - proximos_pasos (JSON list)
         - cuestionario (JSON con preguntas + opciones + correcta_idx)
              --> IntentoCuestionario (N por Participante)
```

---

## Pendientes de refactor

| # | Mejora | Impacto |
|---|---|---|
| 1 | Firmas 1..4 en `LoteCertificados` / `DisenoGlobal` -> tabla pivote `LoteFirma` | Normalización 1NF |
| 2 | `FirmaInstitucional.imagen` base64 (TextField) -> `ImageField` con archivo en media | Performance + storage |
| 3 | `RegistroAsistencia.certificado` / `participante` nullable redundante (legacy) | Limpieza |
