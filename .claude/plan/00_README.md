# Plan Maestro — Refactor + API REST + IA

Este directorio contiene el plan completo de evolucion del proyecto Certify.

## Orden de lectura

1. [01_evaluacion_arquitectura.md](01_evaluacion_arquitectura.md) — Diagnostico actual
2. [02_bugs_corregidos.md](02_bugs_corregidos.md) — Bugs arreglados antes de refactor
3. [03_nueva_arquitectura.md](03_nueva_arquitectura.md) — Arquitectura objetivo (API REST + microservicios logicos)
4. [04_fases_refactor.md](04_fases_refactor.md) — Fases 0-4: reestructuracion
5. [05_fases_api_rest.md](05_fases_api_rest.md) — Fases 5-7: DRF + endpoints
6. [06_fases_ia.md](06_fases_ia.md) — Fases 8-12: features de IA
7. [07_tests_deploy.md](07_tests_deploy.md) — Fase 13: tests + deploy
8. [08_tesis_capitulos.md](08_tesis_capitulos.md) — Mapeo a capitulos de tesis

## Resumen ejecutivo

**Objetivo:** convertir un monolito Django de 4,000+ lineas en un sistema API-first modular con IA integrada, listo para consumir desde una app movil (Expo/React Native) en el futuro.

**Duracion estimada:** 20-25 dias laborales (~4-5 semanas).

**Entregables principales:**
- [x] Bugs criticos corregidos
- [ ] Arquitectura modular (base/, helpers/, managers/, services/pdf/)
- [ ] API REST con DRF (consumible por movil)
- [ ] 5 features de IA integradas
- [ ] Cobertura de tests basica
- [ ] Documentacion tecnica para defensa

## Principios del plan

1. **Cada fase es independiente** — puedes pausar entre fases sin romper nada
2. **No big-bang** — refactor incremental con migraciones graduales
3. **API opcional, no obligatoria** — admin panel sigue siendo Django MVC, API es capa adicional
4. **IA como diferenciador** — no como gimmick, cada feature resuelve problema real
5. **Tesis-ready** — cada decision tecnica tiene justificacion academica

## Stack final

- **Backend:** Django 6 + Django REST Framework
- **Base de datos:** PostgreSQL (migracion desde SQLite)
- **IA:** Claude API (Anthropic) como proveedor principal + embeddings OpenAI
- **Auth:** Sesiones (admin) + JWT (API)
- **Deploy:** Railway.app (sin Docker, como pediste)
- **Futuro movil:** Expo/React Native consumira la misma API
