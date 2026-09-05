# FINANLOVE - AUDIT REPORT FASE 4.7

Fecha: 2026-09-05
Commit auditado: `506f7545a3e3c5446584df6d9601b560b53383ac`
Rama: `main`
Estado: cambios de Phase 4.7 presentes en working tree; no se realizó commit.

## Resumen ejecutivo

Phase 4.7 amplió las pruebas del núcleo financiero y endureció préstamos/repayments con locks `SELECT FOR UPDATE`, transferencias concurrentes y pruebas HTTP de idempotencia. CI ejecuta explícitamente PostgreSQL, Alembic, integración, tests unitarios, coverage y frontend.

La fase no puede declararse cerrada desde esta sesión porque las pruebas PostgreSQL no se ejecutan localmente y no se dispone de logs/artifacts del workflow remoto. Los tests financieros existen y están preparados para CI, pero implementación más test preparado no equivale a comportamiento demostrado.

## Estado inicial

El audit de readiness anterior identificó como condiciones: concurrencia de transferencias, idempotencia concurrente, loans/repayments end-to-end, ownership HTTP exhaustivo, rollback PostgreSQL, rate limiting, pagos de deuda y cobertura crítica.

## Workstreams completados parcialmente

- Tests de transferencias concurrentes añadidos.
- Tests de repayments parcial/completo/excesivo y rollback añadidos.
- Test HTTP same-key concurrente añadido.
- Locks `FOR UPDATE` añadidos para loan y repayment.
- CI ejecuta integración PostgreSQL y coverage conjunto.
- Decisión de rate limiting documentada como fuera de Phase 4.7 por requerir infraestructura compartida para producción.
- Warning HTTPX de cookies corregido.

## Validación local

- Ruff: PASS.
- MyPy: PASS, 83 archivos.
- Pytest: `20 passed`, `11 skipped`.
- Coverage: `61.99%`, threshold 60%.
- Frontend lint/typecheck/tests/build: PASS, 2 tests.
- Alembic heads: un único head `0010_add_idempotency_fingerprint`.
- Docker Compose/build: configurado y validado en ejecuciones anteriores.
- Tests PostgreSQL críticos: BLOCKED localmente por DNS/lifecycle/credenciales Docker desde Windows.

## Matriz de cierre

| Criterio                          | Estado          | Evidencia                                           | Test                                                                  |
| --------------------------------- | --------------- | --------------------------------------------------- | --------------------------------------------------------------------- |
| Atomicidad financiera             | PARTIAL         | Unit of Work y misma sesión                         | Integración preparada, no ejecutada localmente                        |
| Rollback financiero real          | BLOCKED         | Test multi-entidad presente                         | `test_multi_entity_balance_changes_rollback_together`                 |
| Idempotencia persistente          | PARTIAL         | Unique + fingerprint + advisory lock                | Tests HTTP preparados                                                 |
| Idempotencia same-key concurrente | BLOCKED         | Endpoint y test existen                             | `test_transaction_same_key_concurrent_creates_one_movement`           |
| Fingerprint conflict              | PARTIAL         | 409 para payload distinto                           | `test_transaction_idempotency_and_payload_conflict`                   |
| Retry same payload                | PARTIAL         | Segunda respuesta reutiliza resultado               | Test HTTP preparado                                                   |
| Concurrent expenses 80/80         | BLOCKED         | UPDATE condicional                                  | `test_concurrent_expenses_allow_only_one_and_leave_20`                |
| Concurrent transfers              | BLOCKED         | Test nuevo compara balances y ledger                | `test_concurrent_transfers_allow_only_one_and_preserve_both_balances` |
| No saldo negativo                 | PARTIAL         | Condición SQL `balance + delta >= 0`                | Unit tests; integración bloqueada                                     |
| Loan acceptance                   | PARTIAL         | Cuentas explícitas, balances y ledger               | Sin ejecución PostgreSQL verificable                                  |
| Partial repayment                 | PARTIAL         | Repayment 30/100 en test nuevo                      | Sin ejecución PostgreSQL verificable                                  |
| Full repayment                    | PARTIAL         | Repayment 70 y SETTLED en test nuevo                | Sin ejecución PostgreSQL verificable                                  |
| Repayment excessive               | PARTIAL         | Rechazo sobre outstanding                           | Sin ejecución PostgreSQL verificable                                  |
| Repayment concurrency             | BLOCKED         | Locks `FOR UPDATE` agregados                        | No existe evidencia de test concurrente ejecutado                     |
| Ownership HTTP                    | PARTIAL         | Test recurring/account y filtros owner              | Matriz exhaustiva de todos los recursos no ejecutada                  |
| Refresh rotation/reuse/logout     | PARTIAL         | Test HTTP preparado                                 | PostgreSQL persistente bloqueado localmente                           |
| CSRF                              | PARTIAL         | Origin permitido/no permitido en tests              | Cobertura básica, no workflow PostgreSQL visible                      |
| Secrets                           | PASS            | Producción rechaza JWT débil; Compose usa variables | Tests unitarios de configuración                                      |
| Rate limiting                     | NOT IMPLEMENTED | Decisión documentada fuera de fase                  | Requiere store compartido/edge                                        |
| Deudas/pagos                      | PARTIAL         | Debt/Installment iniciales                          | No hay payment/outstanding completo                                   |
| Budgets thresholds                | NOT IMPLEMENTED | No hay 50/80/100 deduplicados                       | -                                                                     |
| Goals contributions               | PARTIAL         | Contribución y movimiento opcional                  | Idempotencia/rollback PostgreSQL no demostrados                       |
| Recurring execution               | PARTIAL         | Templates y ownership                               | Scheduler Phase 5 documentado                                         |
| E2E                               | NOT IMPLEMENTED | No existe browser E2E completo                      | -                                                                     |
| Coverage                          | PARTIAL         | 61.99%, threshold 60%                               | SPEC exige 100%, críticos siguen bajos                                |
| CI PostgreSQL                     | PARTIAL         | Workflow ejecuta service/wait/Alembic/integration   | Run remoto y artifacts no disponibles aquí                            |
| Alembic                           | PARTIAL         | Único head `0010`                                   | Downgrade/upgrade real no demostrado en esta sesión                   |

## Financial Core

La implementación cuenta con protecciones importantes: Decimal/Numeric, update condicional de balance, UoW por request, advisory lock de idempotencia y locks de loan/repayment. Sin embargo, los criterios de cierre requieren ejecución PostgreSQL real de rollback, concurrencia, idempotencia same-key y flujo completo de loans/repayments. El estado global es **PARTIAL/BLOCKED**, no PASS.

## Seguridad

### Cerrado o parcialmente cerrado

- Argon2.
- JWT access.
- Refresh HttpOnly con hash/rotación/revocación.
- CSRF Origin/Referer para refresh.
- Validación de secreto fuerte en producción.
- Ownership de recurrencias a nivel de caso de uso.

### Riesgos restantes

- Access JWT puede seguir válido hasta expirar después de logout.
- No hay rate limiting distribuido para login/registro/refresh.
- Access token del frontend permanece en `localStorage`.
- Ownership HTTP de todos los recursos no está demostrado.

## Arquitectura

La separación Domain/Application/Infrastructure/Presentation existe y el UoW está conectado al ciclo de vida de la sesión. Aún hay composición de repositorios y casos de uso en routers, por lo que la frontera de aplicación no está completamente limpia.

## CI/CD

El workflow contiene:

- PostgreSQL service;
- health check y espera `pg_isready`;
- `DATABASE_URL` y `TEST_DATABASE_URL`;
- `alembic upgrade head`;
- Ruff/MyPy;
- integración `tests/integration -q -ra`;
- unit/e2e/integration con coverage;
- frontend lint/typecheck/tests/build.

El workflow no se puede marcar PASS desde esta sesión sin sus logs/artifacts reales. El último estado GREEN citado por el usuario no está disponible como artefacto dentro del workspace.

## Riesgos restantes

### CRITICAL

- No existe evidencia local verificable de PostgreSQL real para los criterios financieros críticos.
- Idempotencia concurrente, rollback financiero y concurrencia de transferencias no están demostrados en esta sesión.

### HIGH

- Loans/repayments no tienen E2E PostgreSQL verificable.
- Ownership HTTP exhaustivo no está cubierto.
- Access-token revocation inmediata no existe.

### MEDIUM

- Deudas no tienen pagos/saldo pendiente completo.
- Budgets thresholds y deduplicación no implementados.
- No hay scheduler de recurrencias.
- E2E de navegador no implementado.

### LOW

- Warning parser TypeScript.
- Coverage global 61.99% frente a exigencia histórica de 100%.
- Frontend concentrado en `App.tsx`.

## Comparación

- Phase 4: núcleo inicial sin refresh, idempotencia, deuda ni dashboard agregado.
- Phase 4.5: refresh, balances condicionales, ledger, deudas mínimas y dashboard.
- Phase 4.6: UoW, fingerprint, advisory lock, CSRF, secretos parametrizados y CI PostgreSQL.
- Phase 4.7 actual: locks de loans/repayments, transfer concurrency tests, same-key HTTP test, repayment tests y CI integration+coverage conjunto.

## Decisión final

# PHASE 4.7 NOT CLOSED

La fase no puede cerrarse hasta que GitHub Actions ejecute y conserve logs de:

1. rollback PostgreSQL;
2. idempotencia same-key concurrente;
3. fingerprint conflict;
4. retry posterior;
5. concurrent expense 80/80;
6. concurrent transfers;
7. ownership HTTP;
8. refresh/reuse/logout/CSRF;
9. loan acceptance;
10. partial/full repayment;
11. excessive/duplicate repayment.

Phase 5 no debe comenzar como trabajo de producto hasta que esos criterios sean GREEN y exista evidencia auditable del workflow.
