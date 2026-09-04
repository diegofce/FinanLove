# FINANLOVE - AUDIT REPORT FASE 4.6.1

Fecha: 2026-09-04
Estado auditado: working tree actual despues de Fase 4.6.1. No se sobrescriben `AUDIT_REPORT.md`, `AUDIT_REPORT_PHASE4_5.md` ni `AUDIT_REPORT_PHASE4_6.md`.

## 1. Estado del proyecto

El nucleo tiene Unit of Work por request, idempotencia con fingerprint y advisory lock, actualizacion condicional de saldos, refresh rotation, CSRF por Origin/Referer, ownership de recurrencias, pruebas de integración preparadas y CI con PostgreSQL.

No se puede declarar el núcleo financiero verificado porque las pruebas PostgreSQL críticas no llegaron a ejecutarse correctamente en este entorno Windows.

## 2. Diagnóstico del bloqueo PostgreSQL

Se probaron varias rutas:

1. Ejecutar pytest/Alembic desde Windows con `localhost:5432`:
   - falla `asyncpg.exceptions.ConnectionDoesNotExistError` / `WinError 64`.
2. Ejecutar desde Windows con hostname `db`:
   - falla resolución DNS `socket.gaierror: [Errno 11001] getaddrinfo failed`.
3. Ejecutar contenedor de test dentro de la red Compose:
   - se preparó `docker/backend/Dockerfile.test`;
   - se intentó instalar `.[dev]`, migrar y ejecutar integración;
   - el proceso excedió el límite local sin emitir resultado de pytest.
4. Ejecutar con usuario temporal `audit` contra un volumen PostgreSQL existente:
   - falla `InvalidPasswordError`, porque el volumen ya fue inicializado con otras credenciales.

No se borró el volumen ni se ejecutó reset destructivo. El problema combina:

- hostname `db` válido solo dentro de la red Docker;
- puente host Windows/asyncpg inestable en este entorno;
- credenciales persistidas del volumen que no coinciden con variables temporales;
- imagen runtime sin pytest;
- instalación de dependencias lenta dentro de la prueba local.

La configuración CI sí define PostgreSQL, `TEST_DATABASE_URL`, Alembic y los tests de integración. La verificación definitiva debe ejecutarse en CI/Linux o con una red Docker de test completamente disponible.

## 3. Cambios realizados

- Unit of Work conectado al ciclo de vida de `get_db`.
- Fingerprint SHA-256 y locks advisory para idempotencia.
- Validación de payload conflictivo para Idempotency-Key.
- Actualización condicional de saldos.
- CSRF refresh por Origin/Referer.
- Validación de JWT_SECRET en producción.
- Compose parametrizado, sin credenciales embebidas.
- Healthcheck PostgreSQL parametrizado.
- Docker frontend usa `npm ci`.
- Tests de integración de rollback, concurrencia, idempotencia, auth y ownership preparados.
- ADR-004: frontera transaccional.
- ADR-005: idempotencia y concurrencia.
- ADR-006: refresh sessions y CSRF.
- Documentación sincronizada.
- Imagen de test [Dockerfile.test](docker/backend/Dockerfile.test) añadida para ejecutar pytest dentro de la red Docker.

## 4. Tests ejecutados

| Comando                                          | Resultado                                                |
| ------------------------------------------------ | -------------------------------------------------------- |
| `python -m ruff check .`                         | PASS                                                     |
| `python -m mypy .`                               | PASS, 83 archivos                                        |
| `python -m pytest -q`                            | PASS, 20 passed, 8 skipped                               |
| `python -m pytest --cov=app --cov-fail-under=60` | PASS, 62.10%                                             |
| `npm run lint`                                   | PASS, warning parser TypeScript                          |
| `npm run typecheck`                              | PASS                                                     |
| `npm test`                                       | PASS, 2 tests                                            |
| `npm run build`                                  | PASS                                                     |
| `docker compose config --quiet`                  | PASS                                                     |
| `docker compose build`                           | PASS                                                     |
| `alembic heads`                                  | PASS, `0010_add_idempotency_fingerprint`                 |
| PostgreSQL integration desde Windows             | BLOCKED                                                  |
| PostgreSQL integration dentro de Docker          | BLOCKED por timeout/preparación; sin resultado de pytest |

Los skips son explícitos y corresponden a pruebas que requieren `TEST_DATABASE_URL`. No se cuentan como PASS.

## 5. Financial Core

| Criterio                    | Estado  | Evidencia                                        | Test                                                                            |
| --------------------------- | ------- | ------------------------------------------------ | ------------------------------------------------------------------------------- |
| Unit of Work                | PARTIAL | `get_db` usa commit/rollback por request         | Unit tests; falta fallo multi-entidad PostgreSQL ejecutado                      |
| Rollback financiero real    | BLOCKED | UoW implementado                                 | `test_multi_entity_balance_changes_rollback_together`, no ejecutado con DB real |
| Idempotencia persistente    | PARTIAL | Unique owner/key/operation + fingerprint         | Tests HTTP preparados, PostgreSQL bloqueado                                     |
| Idempotencia atómica        | PARTIAL | `pg_advisory_xact_lock` + conflict insert        | No demostrada bajo doble request real                                           |
| Same key + same payload     | PARTIAL | Retry devuelve registro existente                | Test preparado, no ejecutado con DB                                             |
| Same key + payload distinto | PARTIAL | 409 por fingerprint distinto                     | Test HTTP preparado, no ejecutado con DB                                        |
| Concurrent same key         | BLOCKED | Prueba no ejecutada                              | PostgreSQL bloqueado                                                            |
| Concurrent expenses         | BLOCKED | UPDATE condicional implementado                  | `test_concurrent_expenses_allow_only_one_and_leave_20`, PostgreSQL bloqueado    |
| Concurrent transfers        | BLOCKED | No hay evidencia ejecutada                       | Falta prueba real                                                               |
| No negative balance         | PARTIAL | SQL condiciona balance final >= 0                | Unit tests pasan; falta concurrencia PostgreSQL                                 |
| Loan acceptance             | PARTIAL | Actualiza saldos y ledger con cuentas explícitas | Falta prueba PostgreSQL                                                         |
| Loan rollback               | BLOCKED | UoW disponible                                   | Falta fallo deliberado PostgreSQL                                               |
| Partial repayment           | PARTIAL | Mueve saldos y ledger                            | Falta prueba PostgreSQL                                                         |
| Full repayment              | PARTIAL | Marca SETTLED al total aceptado                  | Falta prueba PostgreSQL                                                         |
| Repayment duplicate         | BLOCKED | Idempotencia preparada                           | Falta prueba concurrente real                                                   |
| Repayment excessive         | PARTIAL | Valida total pendiente                           | Falta prueba persistente                                                        |

## 6. Authentication

- Argon2: PASS por implementación y tests unitarios.
- Login/register HTTP: PARTIAL, tests preparados pero PostgreSQL bloqueado.
- Refresh rotation: PARTIAL, código y test preparado.
- Refresh reuse: PARTIAL, rechazo implementado; prueba DB bloqueada.
- Logout: PARTIAL, revoca refresh; test DB bloqueado.
- CSRF: PARTIAL, función y test HTTP sin DB pasan; falta flujo real con refresh persistido.
- Access JWT: PARTIAL, logout no revoca access JWT ya emitido; expira por TTL.
- Rate limiting: NOT IMPLEMENTED.

## 7. Ownership

- Cuentas: PARTIAL, repositorio filtra owner; prueba HTTP PostgreSQL bloqueada.
- Transacciones: PARTIAL, cuenta origen exige owner; prueba HTTP bloqueada.
- Recurrencias: PARTIAL, account_id debe pertenecer al usuario; prueba HTTP bloqueada.
- Deudas/cuotas: PARTIAL, deuda se comprueba antes de cuotas; faltan pagos y pruebas HTTP.
- Loans: PARTIAL, borrower/lender se verifican por operación; falta suite HTTP persistente.

## 8. PostgreSQL

- PostgreSQL real en Compose: disponible y healthy en pruebas previas.
- Alembic head: `0010_add_idempotency_fingerprint`.
- Upgrade: preparado y validado en ejecuciones de contenedor previas, pero no se completó la suite financiera en esta corrida.
- Downgrade/upgrade: no verificado.
- Constraints: unique idempotencia y FKs; faltan CHECKs financieros amplios.
- Locks: advisory idempotency y update condicional de balances.

## 9. CI

CI configura:

- PostgreSQL service;
- `TEST_DATABASE_URL` y `DATABASE_URL`;
- `alembic upgrade head`;
- tests `tests/integration`;
- coverage;
- Ruff/MyPy;
- frontend lint/typecheck/tests/build.

La CI está preparada para ejecutar la evidencia real, pero no se ejecutó un workflow remoto desde este entorno. Por ello el resultado CI es PARTIAL.

## 10. Coverage

- Total local: 62.10%.
- Threshold: 60%.
- Financial core y presentación de préstamos tienen cobertura baja.
- SPEC exige 100%; estado global PARTIAL.

## 11. Riesgos

### CRITICAL

- PostgreSQL financiero real no verificado.
- Idempotencia concurrente no demostrada.
- Rollback financiero no demostrado contra PostgreSQL.
- Concurrencia de balances no demostrada.

### HIGH

- Routers aún componen repositorios y participan en la frontera transaccional.
- Access JWT permanece válido hasta expirar tras logout.
- Ownership HTTP completo no probado.
- Préstamos/devoluciones sin E2E financiero.

### MEDIUM

- Deudas sin pagos/saldo pendiente.
- Alertas de presupuesto sin thresholds/deduplicación.
- Recurrencias sin scheduler.
- Frontend usa casts runtime genéricos.

### LOW

- Warning TypeScript/parser.
- Cobertura inferior al 100% de SPEC.
- Frontend concentrado en `App.tsx`.

## 12. Tests faltantes

- Ejecutar todos los `tests/integration` en CI/Linux.
- Downgrade `-1` y upgrade posterior.
- Concurrencia same-key.
- Concurrencia de gastos 80/80.
- Concurrencia de transferencias.
- Rollback financiero multi-entidad.
- Loan acceptance y repayments con PostgreSQL.
- Ownership HTTP completo.
- E2E financiero completo.

## 13. Migraciones

- `0010_add_idempotency_fingerprint.py` añade fingerprint SHA-256.
- No se eliminaron ni modificaron migraciones históricas durante esta fase.
- `alembic heads` muestra un único head.

## 14. Documentación

Actualizada:

- `docs/ARCHITECTURE.md`
- `docs/SECURITY.md`
- `docs/PHASE4_STATUS.md`
- `src/backend/README.md`
- ADR-004, ADR-005 y ADR-006
- `AUDIT_REPORT_PHASE4_6.md`

## 15. Comparación

- Fase 4: núcleo inicial sin sesiones refresh, idempotencia, deudas ni dashboard agregado.
- Fase 4.5: añadió refresh, idempotencia inicial, saldos condicionales, ledger, deudas mínimas y dashboard.
- Fase 4.6: añadió UoW, fingerprint, advisory lock, CSRF, secretos parametrizados, CI y pruebas de integración preparadas.
- Fase 4.6.1: diagnosticó el bloqueo de red/credenciales, añadió imagen de test dedicada y confirmó que la evidencia financiera sigue bloqueada localmente.

## 16. FASE 5 READY

| Criterio              | Estado  |
| --------------------- | ------- |
| Financial Core seguro | FAIL    |
| Idempotencia          | BLOCKED |
| Concurrency           | BLOCKED |
| Rollback              | BLOCKED |
| Loans                 | PARTIAL |
| Repayments            | PARTIAL |
| Ownership             | BLOCKED |
| Authentication        | PARTIAL |
| CSRF                  | PARTIAL |
| Secrets               | PARTIAL |
| PostgreSQL            | BLOCKED |
| CI integration        | PARTIAL |
| Migrations            | PARTIAL |

# PHASE 5 NOT READY

La Fase 5 no está autorizada. La suite PostgreSQL crítica debe ejecutarse en CI/Linux o en un entorno Docker accesible y sus resultados deben ser revisados antes de avanzar.
