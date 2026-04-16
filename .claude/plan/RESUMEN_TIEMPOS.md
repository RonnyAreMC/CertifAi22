# Cronograma Maestro

## Tabla de fases

| Fase | Nombre | Tiempo | Dependencias | Riesgo |
|------|--------|--------|--------------|--------|
| 0 | Limpieza critica | 2h | - | Bajo |
| 1 | Estructura base | 1 dia | Fase 0 | Bajo |
| 2 | Split pdf_service (Strategy) | 2-3 dias | Fase 1 | Medio |
| 3 | Split views por dominio | 1-2 dias | Fase 1 | Bajo |
| 4 | Managers y querysets | 1 dia | Fase 3 | Bajo |
| 5 | Setup DRF + JWT | 1 dia | Fase 4 | Bajo |
| 6 | Endpoints API principales | 2-3 dias | Fase 5 | Medio |
| 7 | Endpoints IA (placeholder) | medio dia | Fase 5 | Bajo |
| 8 | IA: Copilot cuerpo | 2-3 horas | Fase 7 | Bajo |
| 9 | IA: Mapeo Excel | 1-2 dias | Fase 7 | Medio |
| 10 | IA: Insights dashboard | 1 dia | Fase 7 | Bajo |
| 11 | IA: Recomendaciones | 2-3 dias | Fase 7 + PostgreSQL | Alto |
| 12 | IA: Comandos de voz | 3-5 dias | Fase 7 | Alto |
| 13.1 | Tests | 2 dias | Todas | Medio |
| 13.2 | Config produccion | medio dia | - | Bajo |
| 13.3 | Migracion PostgreSQL | medio dia | - | Alto |
| 13.4 | Monitoreo Sentry | medio dia | - | Bajo |

**Total:** ~22-28 dias laborales (~4-6 semanas)

## Cronograma visual (5 semanas)

```
Semana 1: REFACTOR BASE
├── Lun-Mar: Fase 0 + Fase 1 (base/, helpers/)
├── Mie-Jue-Vie: Fase 2 (split pdf_service con Strategy)

Semana 2: REFACTOR AVANZADO + API
├── Lun-Mar: Fase 3 (split views)
├── Mie: Fase 4 (managers)
├── Jue-Vie: Fase 5 (DRF + JWT)

Semana 3: API + PRIMERAS IAS
├── Lun-Mar-Mie: Fase 6 (endpoints core)
├── Jue: Fase 7 + Fase 8 (copilot)
├── Vie: Fase 10 (insights)

Semana 4: IAS AVANZADAS
├── Lun-Mar: Fase 9 (mapeo Excel)
├── Mie-Jue-Vie: Fase 11 (recomendaciones + PostgreSQL)

Semana 5: CIERRE
├── Lun-Mar-Mie: Fase 12 (voz)
├── Jue-Vie: Fase 13 (tests + deploy + docs)
```

## Ruta critica

**Si tienes poco tiempo (2-3 semanas):**
- Fase 0 (obligatoria, ya parcial)
- Fase 1 (base)
- Fase 2 (Strategy PDFs — alto impacto arquitectonico)
- Fase 5 + Fase 6 (API minima viable)
- Fase 8 (copilot — win rapido)
- Fase 9 (mapeo Excel — resuelve bug real documentado)
- Fase 11 (recomendaciones — academicamente muy fuerte)

**Omitir si tiempo justo:** Fase 12 (voz), Fase 13.4 (Sentry)

## Puntos de commit sugeridos

Cada fase debe terminar con uno o mas commits semantico:

```
refactor: remove duplicate pdf_service functions and dead code
feat: add core/base module with decorators and mixins
refactor: split pdf_service into strategy-based designs
refactor: modularize admin_panel views by domain
feat: add custom managers and querysets
feat: setup Django REST Framework with JWT auth
feat: implement core REST API endpoints
feat: add AI copilot for certificate body text
feat: implement AI-powered Excel column mapping
feat: add AI-generated dashboard insights
feat: content-based event recommendations with embeddings
feat: voice-controlled session creation
test: add unit and integration tests
chore: production configuration and PostgreSQL migration
```

## Criterios de exito por fase

Cada fase se considera completada cuando:
1. `python manage.py check` pasa
2. Las pruebas manuales criticas funcionan
3. Hay commit con mensaje descriptivo
4. El codigo esta en la rama correspondiente
5. Se actualizo este plan (`.claude/plan/`) con lo aprendido

## Recomendacion final

Empezar **en orden**. No saltar a IA sin hacer el refactor primero — la IA construida sobre arquitectura mala es mas dificil de mantener y menos defendible academicamente.

El refactor demuestra **ingenieria de software**. La IA demuestra **aplicacion innovadora**. Ambos son necesarios para una tesis solida.
