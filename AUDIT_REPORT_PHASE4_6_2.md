# FINANLOVE - AUDIT REPORT FASE 4.6.2

Fecha: 2026-09-04
Workflow auditado: [.github/workflows/ci.yml](.github/workflows/ci.yml)
Estado: workflow preparado; ejecución remota de GitHub Actions no disponible desde esta sesión.

## 1. PostgreSQL

**BLOCKED local / preparado para CI.**

El bloqueo local se diagnosticó:

- Desde Windows, `localhost:5432` llega al puente Docker pero `asyncpg` pierde la conexión.
- El hostname `db` solo resuelve dentro de la red Docker.
- Los intentos con usuario temporal `audit` chocaron con credenciales ya persistidas en el volumen.
- El runtime de producción no contiene pytest.

La configuración CI usa un service container PostgreSQL y `localhost:5432`, que es la estrategia correcta para un runner GitHub con services. El workflow ahora instala `postgresql-client`, espera con `pg_isready` y exporta `DATABASE_URL`/`TEST_DATABASE_URL`.

## 2. Alembic

**PARTIAL/BLOCKED.**

- `alembic heads` muestra un único head: `0010_add_idempotency_fingerprint`.
- El workflow ejecuta `alembic upgrade head` antes de las pruebas.
- La cadena fue revisada en fuentes actuales.
- `downgrade -1` y `upgrade head` posterior no se pudieron ejecutar con una PostgreSQL accesible desde esta sesión.

## 3. Tests de integración

**BLOCKED local / PASS esperado en CI solo después de ejecución real.**

La suite existe y cubre:

- rollback multi-entidad;
- dos gastos concurrentes sobre saldo 100;
- idempotencia HTTP y fingerprint;
- refresh rotation/reuse/logout;
- ownership de cuentas y recurrencias;
- CSRF HTTP.

Los tests PostgreSQL se omiten localmente si no existe `TEST_DATABASE_URL`. En CI, `CI=true` convierte la ausencia de esa variable en fallo mediante `pytest.fail`; por tanto no hay skip silencioso en GitHub Actions.

## 4. Financial Core

| Criterio                    | Estado  | Evidencia                                         | Test                                                   |
| --------------------------- | ------- | ------------------------------------------------- | ------------------------------------------------------ |
| Unit of Work                | PARTIAL | `get_db` abre y cierra transacción                | Tests unitarios; integración pendiente                 |
| Rollback financiero real    | BLOCKED | UoW y test existen                                | `test_multi_entity_balance_changes_rollback_together`  |
| Idempotencia persistente    | PARTIAL | Unique owner/key/operation + fingerprint          | Test HTTP preparado                                    |
| Idempotencia atómica        | PARTIAL | `pg_advisory_xact_lock` + inserción conflict-safe | Falta ejecución PostgreSQL                             |
| Same key + same payload     | BLOCKED | Retry implementado                                | Test integración preparado                             |
| Same key + payload distinto | BLOCKED | 409 por fingerprint                               | Test integración preparado                             |
| Concurrent same key         | BLOCKED | Operación serializada por advisory lock           | Falta ejecución real                                   |
| Concurrent expense          | BLOCKED | UPDATE condicional `balance + delta >= 0`         | `test_concurrent_expenses_allow_only_one_and_leave_20` |
| Transfer concurrency        | BLOCKED | No hay evidencia ejecutada                        | Test pendiente                                         |
| No negative balance         | PARTIAL | Restricción en UPDATE SQL                         | Unit tests pasan                                       |
| Loan acceptance             | PARTIAL | Balances y ledger con cuentas explícitas          | Falta PostgreSQL                                       |
| Repayment partial/full      | PARTIAL | Movimientos y SETTLED al total                    | Falta PostgreSQL                                       |
| Excessive repayment         | PARTIAL | Valida saldo pendiente                            | Falta integración                                      |

## 5. Authentication

| Criterio                     | Estado          | Evidencia                                    |
| ---------------------------- | --------------- | -------------------------------------------- | -------------------------------------------------- |
| Register/login               | PARTIAL         | Endpoints, Argon2 y JWT                      | HTTP PostgreSQL pendiente                          |
| Refresh rotation             | PARTIAL         | Cookie HttpOnly, hash y rotación             | Test HTTP preparado                                |
| Refresh reuse rejection      | PARTIAL         | Token revocado no rota nuevamente            | Test preparado                                     |
| Logout                       | PARTIAL         | Revoca refresh y borra cookie                | Test preparado                                     |
| CSRF                         | PARTIAL         | Origin/Referer allowlist                     | Unit/HTTP sin DB pasa; flujo persistente pendiente |
| Production secret validation | PASS            | Rechaza secreto débil/conocido en producción | Test unitario pasa                                 |
| Rate limiting                | NOT IMPLEMENTED | No existe                                    | -                                                  |

## 6. Ownership

**BLOCKED para PASS.** Los filtros de ownership existen en cuentas, transacciones, recurrencias, planificación, deudas y préstamos, y hay pruebas HTTP preparadas. Falta ejecutarlas contra PostgreSQL real para demostrar aislamiento entre User A y User B.

## 7. CI

**PARTIAL/BLOCKED.** `.github/workflows/ci.yml` ahora ejecuta:

1. PostgreSQL service.
2. `pg_isready` explícito.
3. instalación `.[dev]`.
4. `alembic upgrade head`.
5. Ruff.
6. MyPy.
7. `pytest tests/integration -q -ra` con `CI=true`.
8. tests unitarios y coverage.
9. frontend lint/typecheck/tests/build.

El workflow no puede marcarse como PASS hasta ejecutarse en GitHub Actions. No tengo capacidad desde esta sesión para disparar o leer un workflow remoto.

## 8. Coverage

- Última cobertura local: aproximadamente `62.10%`.
- Threshold: `60%`.
- Los módulos financieros críticos tienen cobertura incompleta.
- La exigencia de 100% de `docs/SPEC.md` sigue sin cumplirse.

## 9. Resultado Docker

- `docker compose config --quiet`: PASS con variables efímeras.
- Build backend/frontend: PASS en ejecuciones previas y actuales.
- SPA HTTP 200: verificada.
- Health backend: verificado en una ejecución reconstruida; algunos intentos fueron demasiado tempranos y fallaron por lifecycle.
- Suite PostgreSQL dentro de Docker: no produjo un resultado completo dentro del límite local; no se marca PASS.

## 10. Riesgos restantes

### CRITICAL

- No existe evidencia ejecutada en GitHub Actions de rollback, concurrencia e idempotencia financiera.
- No se puede afirmar que dos requests concurrentes con la misma clave produzcan un solo movimiento hasta ejecutar PostgreSQL real.

### HIGH

- Routers aún componen repositorios y la frontera transaccional no está completamente encapsulada en application.
- Loans/repayments carecen de E2E PostgreSQL ejecutado.
- Access JWT puede seguir válido hasta expirar después de logout.

### MEDIUM

- Falta rate limiting.
- Deudas/cuotas no tienen pagos ni saldo pendiente completo.
- No hay estados formales de ingresos/gastos.
- No hay scheduler de recurrencias.

## 11. Tests faltantes o bloqueados

- PostgreSQL rollback real.
- Same-key concurrent idempotency.
- Concurrent expenses 80/80.
- Concurrent transfers.
- HTTP ownership completo.
- Loan acceptance y repayments con PostgreSQL.
- Downgrade Alembic seguido de upgrade.
- E2E financiero completo.

## 12. Decisión

# PHASE 5 NOT READY

No se declara `PHASE 4.6.2 VERIFIED` porque el workflow remoto de GitHub Actions no se ha ejecutado desde esta sesión y los tests financieros PostgreSQL no tienen resultado real aquí. El siguiente paso obligatorio es ejecutar el workflow en GitHub Actions y revisar su salida completa, incluyendo `collected X items`, rollback, idempotencia, concurrencia, ownership, auth, loans y repayments.
