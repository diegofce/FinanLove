# FINANLOVE - AUDIT REPORT FASE 4.6

Fecha: 2026-09-03
Estado auditado: working tree actual despues de Fase 4.6; no existe una raiz Git detectable para asociar un commit.

## 1. Alcance

Se revisaron `AGENTS.md`, `CLAUDE.md`, instrucciones Copilot, `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`, `docs/PHASE4_STATUS.md`, `AUDIT_REPORT.md`, `AUDIT_REPORT_PHASE4_5.md`, ADRs, manifests, Compose, Dockerfiles, Alembic, backend, frontend y tests.

No se borraron migraciones, no se creo `.env`, no se crearon cuentas ni se usaron datos reales.

## 2. Cambios realizados en Fase 4.6

- Unit of Work SQLAlchemy integrado en `get_db` con commit/rollback por request.
- Fingerprint SHA-256 para payloads idempotentes.
- Lock advisory PostgreSQL por clave de idempotencia.
- Constraint unico para `owner_id + key + operation`.
- Actualizacion condicional de saldos para rechazar saldo insuficiente.
- CSRF basado en `Origin`/`Referer` para refresh cookie.
- Validacion de `JWT_SECRET` en produccion.
- Compose parametrizado con variables de entorno.
- Tests adicionales de seguridad, ownership, dashboard, idempotencia y reglas financieras.
- Test de errores frontend: se elimina `[object Object]`.
- CI configurada con servicio PostgreSQL, Alembic, integracion y coverage.
- Correccion de cadena Alembic y contratos MyPy.

## 3. Tests ejecutados

| Comando                                          | Resultado | Evidencia                                                                                       |
| ------------------------------------------------ | --------- | ----------------------------------------------------------------------------------------------- |
| `python -m ruff check .`                         | PASS      | Sin errores en 80 archivos backend.                                                             |
| `python -m mypy .`                               | PASS      | Sin errores en 80 archivos backend.                                                             |
| `python -m pytest`                               | PASS      | 20 passed, 8 skipped en la ultima ejecucion local.                                              |
| `python -m pytest --cov=app --cov-fail-under=60` | PASS      | 62.10%; supera umbral 60%.                                                                      |
| `npm run lint`                                   | PASS      | Warning no bloqueante por TypeScript fuera del rango soportado por parser.                      |
| `npm run typecheck`                              | PASS      | TypeScript estricto compila.                                                                    |
| `npm test`                                       | PASS      | 2 tests frontend.                                                                               |
| `npm run build`                                  | PASS      | Vite genera bundle.                                                                             |
| `docker compose config --quiet`                  | PASS      | Compose valido con variables efimeras.                                                          |
| `docker compose build`                           | PASS      | Imagenes backend/frontend construidas.                                                          |
| `alembic upgrade head` en contenedor             | PASS      | Migraciones aplicadas en ejecucion controlada previa.                                           |
| PostgreSQL integration desde Windows             | BLOCKED   | El hostname Compose `db` no resuelve desde host y el puente publicado puede cerrar la conexión. |
| PostgreSQL integration dentro de imagen runtime  | BLOCKED   | La imagen de producción no incluye pytest; CI instala el extra dev, pero no se ejecutó aquí.    |

## 4. Matriz

Regla aplicada: PASS requiere implementacion y prueba demostrativa del comportamiento. BLOCKED indica que la prueba requerida no pudo ejecutarse en el entorno actual.

| Requisito                        | Estado          | Evidencia                                                                            | Archivo                                                      |            Linea | Test                                                                                   |
| -------------------------------- | --------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------ | ---------------: | -------------------------------------------------------------------------------------- |
| Unit of Work                     | PARTIAL         | UoW existe y `get_db` lo usa                                                         | `src/backend/app/infrastructure/database.py`                 |            22-25 | Unit tests pasan; falta prueba de fallo HTTP multi-entidad                             |
| Rollback financiero real         | BLOCKED         | Context manager hace rollback, pero no hay evidencia PostgreSQL financiera ejecutada | `src/backend/app/infrastructure/unit_of_work.py`             |             7-16 | Integracion bloqueada                                                                  |
| Idempotency key persistente      | PARTIAL         | Tabla, unique y fingerprint SHA-256                                                  | `src/backend/app/infrastructure/models/idempotency.py`       |             8-24 | Tests unitarios; falta doble request PostgreSQL ejecutado                              |
| Idempotencia atomica             | PARTIAL         | `pg_advisory_xact_lock` y `ON CONFLICT DO NOTHING`                                   | `src/backend/app/infrastructure/repositories/idempotency.py` |            12-54 | No demostrada bajo concurrencia real                                                   |
| Payload fingerprint              | PARTIAL         | Fingerprint canonico de payload                                                      | `src/backend/app/presentation/idempotency.py`                |             1-10 | No hay prueba completa para todas las operaciones                                      |
| Misma key + payload distinto     | PASS            | Routers comparan fingerprint y devuelven 409                                         | `src/backend/app/presentation/transactions.py`               |            31-38 | `test_http_postgres.py`, preparado; ejecucion PostgreSQL bloqueada                     |
| Concurrencia de gastos           | PARTIAL         | `UPDATE ... current_balance + delta >= 0`                                            | `src/backend/app/infrastructure/repositories/accounts.py`    |            45-66 | No existe PASS: prueba PostgreSQL bloqueada                                            |
| Concurrencia de transferencias   | BLOCKED         | No hay prueba real ejecutada                                                         | `src/backend/app/application/transactions.py`                |            45-62 | Falta prueba concurrente                                                               |
| No saldo negativo                | PARTIAL         | Condicion SQL evita update invalido                                                  | `src/backend/app/infrastructure/repositories/accounts.py`    |            53-64 | Unit tests; falta PostgreSQL concurrencia                                              |
| Registro/login                   | PARTIAL         | Argon2, JWT, schemas y persistencia                                                  | `src/backend/app/presentation/auth.py`                       |            40-90 | Tests unitarios; HTTP DB bloqueado                                                     |
| Refresh token                    | PARTIAL         | Cookie HttpOnly, hash, expiracion y rotacion                                         | `src/backend/app/presentation/auth.py`                       |           92-126 | Test HTTP preparado; PostgreSQL bloqueado                                              |
| Refresh reuse detection          | PARTIAL         | Token rotado queda revocado                                                          | `src/backend/app/infrastructure/repositories/tokens.py`      |            25-58 | Test preparado; no ejecutado con DB real                                               |
| Logout server-side               | PARTIAL         | Revoca refresh y elimina cookie                                                      | `src/backend/app/presentation/auth.py`                       |          128-140 | Falta test HTTP real ejecutado                                                         |
| CSRF refresh                     | PARTIAL         | Valida Origin/Referer contra CORS                                                    | `src/backend/app/presentation/auth.py`                       |            22-32 | `test_phase46_security.py` cubre función; falta test de endpoint/DB                    |
| Secretos produccion              | PASS            | Produccion rechaza secreto corto/conocido                                            | `src/backend/app/core/config.py`                             |            20-31 | `test_phase46_security.py`                                                             |
| Secretos Compose                 | PARTIAL         | Compose exige variables, pero CI usa credenciales de servicio en YAML                | `compose.yml`                                                |             5-14 | Config valido; requiere política de secretos CI                                        |
| Ownership recurrencias           | PARTIAL         | Valida cuenta propia y activa                                                        | `src/backend/app/application/recurring.py`                   |            27-42 | Unit test; falta ownership HTTP PostgreSQL ejecutado                                   |
| Ownership cuentas                | PARTIAL         | Repositorio filtra owner                                                             | `src/backend/app/infrastructure/repositories/accounts.py`    |            32-43 | Falta prueba HTTP ejecutada                                                            |
| Ownership transacciones          | PARTIAL         | Cuenta origen se obtiene con owner autenticado                                       | `src/backend/app/application/transactions.py`                |            37-45 | Falta prueba HTTP ejecutada                                                            |
| Ownership deudas/cuotas          | PARTIAL         | Debt se consulta por owner antes de cuotas                                           | `src/backend/app/presentation/debts.py`                      |            54-93 | Falta modificar/pagar y prueba HTTP                                                    |
| Aceptacion de prestamo           | PARTIAL         | Exige cuentas y actualiza ambos saldos/ledger                                        | `src/backend/app/application/loans.py`                       |           91-175 | Falta PostgreSQL rollback/consistencia ejecutado                                       |
| Devolucion parcial               | PARTIAL         | Mueve fondos y crea ledger                                                           | `src/backend/app/application/loans.py`                       |          189-258 | Estado parcial explicito y prueba real faltan                                          |
| Devolucion completa              | PARTIAL         | Marca SETTLED cuando total aceptado iguala monto                                     | `src/backend/app/application/loans.py`                       |          279-292 | Falta prueba completa, saldo y retry                                                   |
| Ledger préstamo/devolucion       | PARTIAL         | Crea dos transacciones por movimiento                                                | `src/backend/app/application/loans.py`                       | 130-175, 240-278 | No probado con DB real                                                                 |
| Estados income/expense           | NOT IMPLEMENTED | Solo existe `TransactionType`                                                        | `src/backend/app/domain/transaction.py`                      |             1-21 | No existen estados EXPECTED/RECEIVED/PENDING/PAID                                      |
| Deudas/cuotas                    | PARTIAL         | Modelos, repositorio y endpoints minimos                                             | `src/backend/app/presentation/debts.py`                      |            25-93 | Faltan pagos, saldo pendiente e historial                                              |
| Dashboard agregado               | PARTIAL         | Endpoint agregado con cinco metricas                                                 | `src/backend/app/presentation/dashboard.py`                  |            15-30 | No incluye pendientes, proximas obligaciones ni estadisticas                           |
| Presupuestos                     | PARTIAL         | Calcula gasto y porcentaje                                                           | `src/backend/app/application/planning.py`                    |            19-59 | No hay CRUD completo ni alertas 50/80/100 deduplicadas                                 |
| Metas                            | PARTIAL         | Contribucion puede descontar cuenta y actualizar meta                                | `src/backend/app/application/planning.py`                    |           62-134 | Idempotencia y rollback real no demostrados                                            |
| Notificaciones                   | PARTIAL         | Listar, leer y algunos eventos automaticos                                           | `src/backend/app/application/planning.py`                    |          136-170 | Riesgo de duplicados al consultar presupuesto                                          |
| Categorias                       | PARTIAL         | Crear/listar por propietario                                                         | `src/backend/app/presentation/planning.py`                   |          174-198 | Faltan sistema, unicidad y lifecycle completo                                          |
| Recurrencias                     | PARTIAL         | Plantillas persistidas, ownership corregido                                          | `src/backend/app/application/recurring.py`                   |             1-80 | No hay scheduler, ejecucion ni idempotencia de ejecucion                               |
| Error frontend `[object Object]` | PASS            | Normalizador trata arrays/objects y mantiene mensaje legible                         | `src/frontend/src/services/api.ts`                           |          131-164 | Test frontend pasa                                                                     |
| Validacion registro frontend     | PARTIAL         | Minimo 12 y confirmacion visual                                                      | `src/frontend/src/app/App.tsx`                               |          130-177 | No compara igualdad de password antes de enviar                                        |
| API client                       | PARTIAL         | Cliente centralizado con Bearer y queries                                            | `src/frontend/src/services/api.ts`                           |          120-190 | Mantiene casts `as T` y no cubre todas las mutaciones                                  |
| TypeScript estricto              | PASS            | `strict`, noUnused y compilacion                                                     | `src/frontend/tsconfig.json`                                 |             2-29 | Typecheck/build pasan                                                                  |
| Tests unitarios                  | PARTIAL         | 14 backend y 2 frontend pasan                                                        | `src/backend/tests`, `src/frontend/tests`                    |                - | No sustituyen integracion financiera                                                   |
| Tests PostgreSQL reales          | BLOCKED         | Fixture y casos existen, pero no se ejecutaron localmente                            | `src/backend/tests/integration`                              |                - | CI es el entorno previsto                                                              |
| Tests E2E                        | NOT IMPLEMENTED | No existe flujo E2E completo automatizado                                            | `src/backend/tests/e2e`                                      |                - | Falta flujo financiero de extremo a extremo                                            |
| Coverage                         | PARTIAL         | Umbral 60 y cobertura local 61.55%                                                   | `src/backend/pyproject.toml`                                 |            48-54 | SPEC exige 100%; no se debe falsear                                                    |
| CI PostgreSQL                    | PARTIAL         | Servicio, Alembic e integracion declarados                                           | `.github/workflows/ci.yml`                                   |             8-64 | No se ejecutó CI real en este entorno                                                  |
| CI frontend                      | PASS            | npm ci, lint, typecheck, test, build                                                 | `.github/workflows/ci.yml`                                   |           68-100 | Parser mantiene warning de version                                                     |
| Migraciones                      | PARTIAL         | Cadena hasta 0010 y fingerprint                                                      | `src/backend/alembic/versions`                               |                - | Upgrade offline/imagen validado; downgrade no probado                                  |
| Constraints DB                   | PARTIAL         | Unique idempotencia y FKs                                                            | `src/backend/alembic/versions/0008_add_idempotency_keys.py`  |            15-31 | Faltan CHECKs de estados/montos/ownership compuesto                                    |
| Docker backend                   | PASS            | Build y Alembic configurado al inicio                                                | `docker/backend/Dockerfile`                                  |             1-16 | Build validado; pytest no forma parte del runtime                                      |
| Docker frontend                  | PASS            | Nginx SPA y proxy API                                                                | `docker/frontend/nginx.conf`                                 |             1-20 | Build y SPA validado                                                                   |
| Clean Architecture               | PARTIAL         | Capas y repositorios presentes                                                       | `src/backend/app`                                            |                - | Routers siguen componiendo infraestructura; UoW existe pero no es frontera de use case |
| Documentacion                    | PARTIAL         | PHASE4_STATUS y audit previos existen                                                | `docs/PHASE4_STATUS.md`                                      |             1-60 | SPEC/ARCHITECTURE/SECURITY no están sincronizados plenamente                           |
| ADRs                             | PARTIAL         | ADR-001 a ADR-003                                                                    | `docs/decisions`                                             |                - | Faltan ADR de UoW, idempotencia, concurrencia, sesiones, CSRF y préstamos              |

## 5. Financial Core

### Transacciones

- Ingresos, gastos y transferencias existen en backend.
- Los saldos usan `Decimal/Numeric`.
- El update SQL impide aplicar un delta que deje saldo negativo.
- No existe prueba PostgreSQL ejecutada de dos gastos concurrentes.
- No hay idempotencia demostrada para doble request concurrente.
- No hay prueba real de rollback con ledger y múltiples entidades.

Resultado: **PARTIAL/BLOCKED**, no PASS.

### Idempotencia

Existe fingerprint y constraint único. El lock advisory reduce la carrera de lectura, pero el diseño actual sigue ejecutando la operación antes de insertar la clave. No existe una reserva de operación pendiente ni una prueba PostgreSQL que demuestre que dos requests simultáneos no duplican el movimiento. Resultado: **PARTIAL**.

### Préstamos y repayments

Los casos de uso actualizan saldos y crean registros de ledger cuando reciben las dependencias financieras. Sin embargo, el modelo no representa explícitamente `FUNDS_TRANSFERRED` ni `PARTIALLY_REPAID`, y no hay evidencia PostgreSQL de rollback, concurrencia, saldo pendiente o retry. Resultado: **PARTIAL**.

## 6. Authentication/Security

- Argon2: implementado.
- Access JWT: implementado.
- Refresh HttpOnly con rotacion/revocacion: implementado parcialmente y sin suite DB ejecutada.
- Reuse detection: codigo presente, prueba real bloqueada.
- Logout: revoca refresh, pero un access JWT ya emitido puede seguir valido hasta expirar.
- CSRF: validacion Origin/Referer presente; falta test de endpoint en DB real y documentación formal completa.
- Secretos: producción rechaza secreto débil; Compose depende de variables. CI todavía contiene credenciales efímeras declaradas en el workflow.
- Rate limiting: faltante.
- Access token en frontend/localStorage: riesgo XSS persistente.

## 7. PostgreSQL

La cadena Alembic llega a 0010 y la migración de fingerprint es compatible con la tabla existente. El upgrade offline y el upgrade dentro de imagen se prepararon/validaron parcialmente. El test financiero real no se ejecutó: desde Windows `asyncpg` perdió la conexión publicada y la imagen de runtime no incluye pytest. Downgrade y upgrade nuevamente no fueron demostrados.

## 8. HTTP/API

Los endpoints de auth, cuentas, transacciones, préstamos, planificación, deudas y dashboard están registrados. Los schemas devuelven errores estructurados que el frontend ya normaliza. Faltan pruebas HTTP PostgreSQL de ownership, 401/403/404/409, rollback, idempotencia y flujos financieros completos.

## 9. Frontend

El error `[object Object]` está corregido en la fuente; el bundle debe regenerarse/deployarse para reflejarlo. Login/registro y dashboard inicial existen. Faltan igualdad de passwords, refresh automático, manejo central de 401/refresh, rutas por feature, acciones de préstamos/deudas/planificación y validación runtime de respuestas.

## 10. CI/CD

CI declara PostgreSQL, ejecuta Alembic, integración, coverage, Ruff, MyPy y frontend. No se ejecutó el workflow en una plataforma CI desde este entorno. La integración existente contiene pruebas reales de rollback, concurrencia, idempotencia y HTTP, pero son susceptibles de skip/error si el entorno no expone `TEST_DATABASE_URL`; CI sí la declara.

## 11. Coverage

- Total local: 61.10%-61.55% según corrida.
- Threshold configurado: 60%.
- Critical modules: préstamos, presentación HTTP y repositorios permanecen con cobertura baja según el reporte.
- SPEC exige 100%, por lo que el criterio global es **PARTIAL**.

## 12. Riesgos restantes

### CRÍTICO

- Idempotencia concurrente no demostrada y potencialmente vulnerable al patrón operación antes de reserva.
- Rollback financiero real no demostrado.
- Concurrencia de saldos no demostrada contra PostgreSQL.
- Secretos de desarrollo/CI siguen declarados en configuraciones, aunque no sean credenciales reales de usuario.

### ALTO

- Aceptación/devolución de préstamo depende de coordinación en routers y no tiene una frontera transaccional de aplicación única.
- Access JWT almacenado en `localStorage`.
- Ownership HTTP sistemático no probado.
- Devoluciones/aceptaciones no tienen prueba E2E financiera.

### MEDIO

- Falta CSRF endpoint-level comprobado.
- Alertas de presupuesto pueden duplicarse.
- Falta deudas con pagos y saldo restante.
- Dashboard incompleto.
- Runtime validation TypeScript ausente.

### BAJO

- Warning de compatibilidad TypeScript/parser.
- Nombres físicos de migraciones no reflejan siempre IDs internos cortos.
- Frontend concentrado en `App.tsx`.

## 13. Tests faltantes

- PostgreSQL real: rollback multi-entidad.
- PostgreSQL real: misma idempotency key concurrente.
- PostgreSQL real: fingerprint conflict y retry posterior.
- PostgreSQL real: dos gastos 80/80 sobre saldo 100.
- PostgreSQL real: transferencias concurrentes.
- HTTP real: register/login/refresh/reuse/logout/me.
- HTTP real: ownership de todos los recursos.
- Loan acceptance con balances y ledger.
- Repayment parcial/completo, saldo insuficiente, doble aceptación y retry.
- Pagos de Debt/Installment.
- Alertas 50/80/100 deduplicadas.
- E2E registro -> login -> cuenta -> ingreso -> gasto -> transferencia -> dashboard.
- E2E préstamo -> aceptación -> devolución parcial -> devolución total.
- Downgrade Alembic y upgrade posterior.
- Comparación de fingerprint con payload semánticamente igual/diferente.

## 14. Documentación actualizada

Durante esta fase se actualizó el estado de fase y se generó este informe. Aún falta sincronizar completamente `docs/SPEC.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md` y crear ADRs específicos para las nuevas decisiones.

## 15. Migraciones creadas

- `0010_add_idempotency_fingerprint.py`: columna fingerprint SHA-256 para claves idempotentes.

También se mantiene la migración `0009_add_debts_installments.py` de la fase anterior.

## 16. Comparación

### Fase 4

Núcleo inicial con login, cuentas, movimientos, planificación y préstamos básicos. Sin refresh, idempotencia, deudas ni dashboard agregado.

### Fase 4.5

Añadió refresh tokens, idempotencia inicial, saldos condicionales, ledger de préstamos/devoluciones, deudas mínimas y dashboard mínimo. Los audits dejaron pendientes pruebas reales, unidad transaccional, CSRF y secretos.

### Fase 4.6

Añadió UoW por request, fingerprint, advisory lock, pruebas de integración preparadas, CSRF, validación de secretos, Compose parametrizado y CI con PostgreSQL. El avance no llega a cierre porque las pruebas reales PostgreSQL no pudieron ejecutarse en este entorno y permanecen riesgos de diseño financiero.

## 17. FASE 5 READY

| Criterio                              | Estado  |
| ------------------------------------- | ------- |
| Financial Core seguro                 | FAIL    |
| Idempotencia atomica demostrada       | BLOCKED |
| Payload fingerprint                   | PARTIAL |
| Duplicate request concurrente probado | BLOCKED |
| Balance concurrente probado           | BLOCKED |
| Rollback PostgreSQL probado           | BLOCKED |
| Loan acceptance atomic                | PARTIAL |
| Repayment atomic                      | PARTIAL |
| Ownership HTTP probado                | BLOCKED |
| Refresh rotation probado              | PARTIAL |
| Refresh reuse rechazado               | PARTIAL |
| Logout probado                        | PARTIAL |
| Secret defaults eliminados            | PARTIAL |
| PostgreSQL integration ejecutada      | BLOCKED |
| CI ejecuta integration real           | PARTIAL |
| No critical financial FAIL            | FAIL    |
| Audit report Fase 4.6 generado        | PASS    |

## Decisión

# PHASE 5 NOT READY

No se recomienda pasar a Fase 5. Deben ejecutarse y aprobarse primero las pruebas PostgreSQL reales de rollback, idempotencia concurrente, concurrencia de saldos, ownership HTTP y préstamos/devoluciones; además deben eliminarse los fallos críticos de unidad transaccional e idempotencia y resolverse la política de secretos/CSRF.

## Actualización final de verificación

Después de la revisión inicial se corrigieron los contratos MyPy de lectura,
el fixture del dashboard, la aceptación insegura de préstamos sin integración
financiera y el healthcheck/instalación determinista de Docker. El estado actual
verificado es:

- Ruff: PASS.
- MyPy: PASS, 83 archivos.
- Pytest: 20 passed, 8 skipped.
- Coverage: 62.10%, threshold 60%.
- Frontend lint/typecheck/tests/build: PASS, 2 tests.
- Docker Compose config y build: PASS.
- Las migraciones hasta `0010` se inspeccionaron y la cadena es coherente en
  fuentes actuales.
- PostgreSQL financiero real, concurrencia y rollback: BLOCKED en Windows; el
  test de host falla con `asyncpg ConnectionDoesNotExistError` y la imagen de
  runtime no incluye pytest para ejecutar la suite dentro del contenedor.

La decisión no cambia: **PHASE 5 NOT READY**. La cobertura y los tests unitarios
no sustituyen la evidencia PostgreSQL exigida para dinero, idempotencia,
concurrencia y rollback.
