# FINANLOVE - AUDIT REPORT FASE 4.5

Fecha: 2026-09-03
Alcance: auditoria del codigo actual despues del hardening Fase 4.5. Se revisaron fuentes, modelos, repositorios, casos de uso, routers, migraciones, frontend, CI, Docker y tests. No se sobrescribe `AUDIT_REPORT.md`.

## Evidencia ejecutada

- Backend Ruff: PASS.
- Backend MyPy: PASS, 75 archivos.
- Backend pytest: PASS, 14 tests; 1 test de disponibilidad PostgreSQL omitido sin URL local.
- Backend coverage: PASS umbral configurado, 61.55% con `--cov-fail-under=60`.
- Frontend lint/typecheck/test/build: PASS; 2 tests frontend.
- Docker build: PASS.
- Alembic dentro de contenedor contra PostgreSQL de Compose: PASS hasta head.
- SPA Docker: HTTP 200 verificado.
- Health HTTP desde host Windows: no se marca PASS en el ultimo intento por timing de arranque; hubo una ejecucion anterior de la imagen corregida con `/health` HTTP 200.
- No se crearon cuentas, contraseñas ni datos financieros reales.

## Matriz de requisitos principales

| Requisito                      | Estado            | Evidencia                                                 | Archivo                                                                                   |            Línea | Observación                                                                                                                                        |
| ------------------------------ | ----------------- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ---------------: | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| Registro                       | [PASS]            | Schema Pydantic, hash Argon2, commit y respuesta sin hash | [auth.py](src/backend/app/presentation/auth.py)                                           |            40-59 | El flujo backend existe y el cliente muestra errores legibles. Falta prueba HTTP completa contra DB desde Windows.                                 |
| Error de registro              | [PASS]            | Normalizador para string, array de objetos y object       | [api.ts](src/frontend/src/services/api.ts)                                                |          131-164 | Se eliminó la conversión directa a `String(body.detail)` que producía `[object Object]`.                                                           |
| Validación frontend registro   | [PASS]            | `minLength={12}` y confirmación de contraseña             | [App.tsx](src/frontend/src/app/App.tsx)                                                   |          130-177 | No hay validación de igualdad de contraseñas antes del submit.                                                                                     |
| Login                          | [PARTIAL]         | Access JWT y consulta de usuario                          | [auth.py](src/backend/app/presentation/auth.py)                                           |            64-89 | No existe test HTTP completo de login válido, inválido e inactivo.                                                                                 |
| Refresh token                  | [PARTIAL]         | Cookie HttpOnly, hash, rotación y revocación              | [auth.py](src/backend/app/presentation/auth.py)                                           |           92-126 | Falta test HTTP de reutilización de token rotado/revocado y política CSRF documentada/implementada.                                                |
| Logout server-side             | [PARTIAL]         | Revoca refresh token y borra cookie                       | [auth.py](src/backend/app/presentation/auth.py)                                           |          128-140 | No revoca access JWT ya emitido; no existe test HTTP.                                                                                              |
| Perfil /me                     | [PASS]            | Endpoint protegido retorna UserResponse con rol           | [auth.py](src/backend/app/presentation/auth.py)                                           |          143-147 | No hay tests HTTP de autorización del endpoint.                                                                                                    |
| RBAC                           | [PARTIAL]         | Campo `role` y valor USER                                 | [user.py](src/backend/app/infrastructure/models/user.py)                                  |            20-24 | No hay permisos Admin/User aplicados a endpoints.                                                                                                  |
| Ownership cuentas              | [PASS]            | Consultas y updates filtran owner_id                      | [accounts.py](src/backend/app/infrastructure/repositories/accounts.py)                    |            32-61 | Falta prueba HTTP con dos usuarios.                                                                                                                |
| Ownership recurrencias         | [PARTIAL]         | Caso usa repository de cuentas para validar               | [recurring.py](src/backend/app/application/recurring.py)                                  |             1-80 | Debe verificarse el código actual del caso y falta prueba HTTP demostrativa completa.                                                              |
| Ownership transacciones        | [PASS]            | Cuenta se obtiene con owner autenticado                   | [transactions.py](src/backend/app/application/transactions.py)                            |            37-45 | Falta test de integración/API.                                                                                                                     |
| Ownership préstamos            | [PARTIAL]         | Loan se busca por borrower o lender                       | [loans.py](src/backend/app/infrastructure/repositories/loans.py)                          |            27-48 | Las operaciones financieras relacionadas requieren más pruebas de aislamiento.                                                                     |
| Ownership planificación        | [PARTIAL]         | Budgets/goals/notificaciones tienen owner/user filters    | [planning.py](src/backend/app/infrastructure/repositories/planning.py)                    |           27-161 | No hay suite HTTP sistemática para cada recurso.                                                                                                   |
| Idempotencia persistente       | [PARTIAL]         | Tabla y unique(owner_id,key,operation)                    | [0008_add_idempotency_keys.py](src/backend/alembic/versions/0008_add_idempotency_keys.py) |            15-31 | Existe mecanismo, pero el patrón get -> operar -> add puede tener carrera entre requests concurrentes.                                             |
| Idempotencia transacciones     | [PARTIAL]         | Header e idempotency repository                           | [transactions.py](src/backend/app/presentation/transactions.py)                           |            20-83 | Falta test HTTP de retry y doble submit concurrente.                                                                                               |
| Idempotencia préstamos         | [PARTIAL]         | Header y registro de response_id                          | [loans.py](src/backend/app/presentation/loans.py)                                         |            33-95 | Falta hash de payload: misma clave con payload distinto no se rechaza explícitamente.                                                              |
| Idempotencia repayment         | [PARTIAL]         | Header en endpoints de repayment                          | [loans.py](src/backend/app/presentation/loans.py)                                         |          117-281 | Falta demostrar concurrencia y consistencia con fondos.                                                                                            |
| Idempotencia metas             | [PARTIAL]         | El cliente actualiza goal y movimiento opcional           | [planning.py](src/backend/app/presentation/planning.py)                                   |          114-134 | No se observa una clave idempotente conectada en este endpoint.                                                                                    |
| Concurrencia saldo             | [PARTIAL]         | Update condicional evita saldo negativo                   | [accounts.py](src/backend/app/infrastructure/repositories/accounts.py)                    |            45-61 | No existe test concurrente PostgreSQL real; no se puede afirmar garantía completa.                                                                 |
| Rollback financiero            | [PARTIAL]         | Algunos routers hacen rollback explícito                  | [transactions.py](src/backend/app/presentation/transactions.py)                           |            48-83 | No existe una unidad transaccional de aplicación común; aceptación de préstamo y metas requieren pruebas de fallo intermedio.                      |
| Unidad transaccional           | [FAIL]            | Routers crean repositorios y ejecutan commit              | [loans.py](src/backend/app/presentation/loans.py)                                         |            42-95 | La presentación sigue coordinando transacciones y commits.                                                                                         |
| Aceptación préstamo            | [PARTIAL]         | Requiere cuentas y actualiza ambos saldos/ledger          | [loans.py](src/backend/app/application/loans.py)                                          |           91-175 | El estado sigue siendo ACCEPTED, no existe estado explícito FUNDS_TRANSFERRED. Falta prueba de rollback real.                                      |
| Rechazo préstamo               | [PASS]            | Solo lender puede decidir REQUESTED -> REJECTED           | [loans.py](src/backend/app/application/loans.py)                                          |          103-125 | Falta test API.                                                                                                                                    |
| Devolución parcial             | [PARTIAL]         | Valida importe pendiente y mueve saldos/ledger al aceptar | [loans.py](src/backend/app/application/loans.py)                                          |          189-258 | Falta actualización explícita a PARTIALLY_REPAID y test PostgreSQL.                                                                                |
| Devolución completa            | [PARTIAL]         | Marca SETTLED si total aceptado iguala préstamo           | [loans.py](src/backend/app/application/loans.py)                                          |          279-292 | Falta flujo de fondos probado end-to-end e idempotencia concurrente.                                                                               |
| No duplicar dinero             | [PARTIAL]         | Ledger de préstamo/devolución y balances                  | [loans.py](src/backend/app/application/loans.py)                                          | 130-175, 240-278 | Falta prueba de doble request y constraints que unan ledger con operación.                                                                         |
| Ingresos                       | [PARTIAL]         | TransactionType INCOME aumenta saldo                      | [transactions.py](src/backend/app/application/transactions.py)                            |            62-67 | No existen estados EXPECTED/RECEIVED/CANCELLED ni casos de uso dedicados.                                                                          |
| Gastos                         | [PARTIAL]         | EXPENSE descuenta saldo                                   | [transactions.py](src/backend/app/application/transactions.py)                            |            57-76 | No existen estados PENDING/PAID/CANCELLED ni pago separado.                                                                                        |
| Transferencias                 | [PARTIAL]         | Debita/acredita cuentas propias y verifica moneda         | [transactions.py](src/backend/app/application/transactions.py)                            |            45-61 | Falta prueba concurrente y la UI requiere verificar destino en todas las pantallas.                                                                |
| Deudas                         | [PARTIAL]         | Debt e Installment, endpoints y migración                 | [debts.py](src/backend/app/presentation/debts.py)                                         |            25-93 | Solo creación/listado/cuotas; faltan pagos, saldo restante e historial.                                                                            |
| Cuotas                         | [PARTIAL]         | Modelo y endpoint de creación/listado                     | [debt.py](src/backend/app/domain/debt.py)                                                 |             1-24 | No hay pago de cuota ni cálculo de outstanding balance.                                                                                            |
| Presupuestos                   | [PARTIAL]         | Crea/lista y suma EXPENSE por periodo                     | [planning.py](src/backend/app/application/planning.py)                                    |            19-59 | No hay actualizar/archivar y las alertas se generan al consultar.                                                                                  |
| Alertas 50/80/100              | [NOT IMPLEMENTED] | Solo se detecta excedido                                  | [planning.py](src/backend/app/application/planning.py)                                    |            37-59 | No existen umbrales ni deduplicación.                                                                                                              |
| Metas                          | [PARTIAL]         | Crea/lista/contribuye y progreso                          | [planning.py](src/backend/app/application/planning.py)                                    |           62-134 | Falta idempotencia integrada y decisión clara sobre movimiento vs seguimiento.                                                                     |
| Notificaciones                 | [PARTIAL]         | Persistencia/listado/lectura y algunos eventos            | [planning.py](src/backend/app/application/planning.py)                                    |          136-170 | Falta contador dedicado, paginación y deduplicación de alertas.                                                                                    |
| Categorías                     | [PARTIAL]         | Crear/listar por owner                                    | [planning.py](src/backend/app/presentation/planning.py)                                   |          174-198 | No hay categorías de sistema, edición, borrado ni unique robusto.                                                                                  |
| Recurrentes                    | [PARTIAL]         | Plantilla persistente                                     | [recurring.py](src/backend/app/application/recurring.py)                                  |             1-80 | No hay scheduler, ejecución, reintentos ni idempotencia de ejecución.                                                                              |
| Dashboard backend              | [PARTIAL]         | Endpoint agregado                                         | [dashboard.py](src/backend/app/presentation/dashboard.py)                                 |            15-30 | Solo devuelve balance, ingresos, gastos, préstamos activos y cantidad de metas.                                                                    |
| Dashboard frontend             | [PARTIAL]         | Consulta y renderiza datos reales                         | [App.tsx](src/frontend/src/app/App.tsx)                                                   |          183-420 | No cubre próximos pagos, estadísticas, pendientes ni todas las acciones.                                                                           |
| API client                     | [PARTIAL]         | Cliente centralizado con Bearer                           | [api.ts](src/frontend/src/services/api.ts)                                                |          120-190 | Usa casts genéricos y no cubre todos los endpoints/mutaciones.                                                                                     |
| Rutas frontend                 | [PARTIAL]         | Login/register y wildcard protegida                       | [App.tsx](src/frontend/src/app/App.tsx)                                                   |          640-666 | Faltan rutas independientes de cuentas, deudas, settings, etc.                                                                                     |
| TypeScript strict              | [PASS]            | strict/noUnused y typecheck                               | [tsconfig.json](src/frontend/tsconfig.json)                                               |             2-29 | No se observan `any` en fuentes revisadas.                                                                                                         |
| Testing unitario               | [PARTIAL]         | 14 tests backend, 2 frontend                              | [src/backend/tests](src/backend/tests)                                                    |                - | Cubre reglas aisladas, no contratos completos ni infraestructura.                                                                                  |
| Testing integración PostgreSQL | [PARTIAL]         | Test de conectividad existente                            | [test_postgres.py](src/backend/tests/integration/test_postgres.py)                        |             7-22 | En Windows host falla conexión asyncpg; dentro del contenedor solo se verificó migración, no suite pytest porque imagen runtime no incluye pytest. |
| Testing E2E                    | [NOT IMPLEMENTED] | No hay flujo E2E ejecutable                               | [src/backend/tests/e2e](src/backend/tests/e2e)                                            |                - | Falta registro -> login -> cuentas -> movimientos -> dashboard y préstamo completo.                                                                |
| Coverage                       | [PARTIAL]         | 61.55%, threshold 60                                      | [pyproject.toml](src/backend/pyproject.toml)                                              |            48-54 | Cumple umbral artificial/configurado, pero no cubre la exigencia SPEC de 100%.                                                                     |
| CI backend                     | [PARTIAL]         | Postgres service, Alembic, Ruff, MyPy, coverage           | [.github/workflows/ci.yml](.github/workflows/ci.yml)                                      |            10-39 | No ejecuta tests integración explícitos, concurrencia, downgrade ni E2E.                                                                           |
| CI frontend                    | [PASS]            | npm ci, lint, typecheck, test, build                      | [.github/workflows/ci.yml](.github/workflows/ci.yml)                                      |            42-76 | Sigue warning de parser por TypeScript fuera del rango soportado.                                                                                  |
| Docker backend                 | [PASS]            | Instala runtime y ejecuta Alembic al inicio               | [Dockerfile](docker/backend/Dockerfile)                                                   |             1-16 | Build y migración dentro de contenedor verificados.                                                                                                |
| Docker frontend                | [PASS]            | Nginx sirve SPA y proxy `/api`                            | [nginx.conf](docker/frontend/nginx.conf)                                                  |             1-20 | SPA HTTP 200 verificada.                                                                                                                           |
| Secretos                       | [FAIL]            | Credenciales DB fijas y JWT default conocido              | [compose.yml](compose.yml), [config.py](src/backend/app/core/config.py)                   |         5-9 / 13 | Contradice reglas de seguridad para cualquier entorno no local.                                                                                    |
| Cookies/CSRF                   | [PARTIAL]         | Refresh HttpOnly SameSite lax                             | [auth.py](src/backend/app/presentation/auth.py)                                           |          102-112 | No hay CSRF token/doble submit ni documentación completa de amenaza.                                                                               |
| Arquitectura Clean             | [PARTIAL]         | Capas, puertos y repositorios presentes                   | [src/backend/app](src/backend/app)                                                        |                - | Commits/orquestación en routers; casos de uso aceptan dependencias opcionales que permiten estados no uniformes.                                   |
| Migraciones                    | [PARTIAL]         | Cadena hasta 0009 y Alembic ejecutable                    | [src/backend/alembic/versions](src/backend/alembic/versions)                              |                - | La cadena funciona, pero nombres físicos e IDs internos no son coherentes en 0003/0007; no hay downgrade probado.                                  |
| Documentación                  | [PARTIAL]         | PHASE4_STATUS actualizado                                 | [docs/PHASE4_STATUS.md](docs/PHASE4_STATUS.md)                                            |             1-60 | SPEC, ARCHITECTURE y SECURITY siguen sin reflejar todas las decisiones/limitaciones de Fase 4.5.                                                   |
| ADRs                           | [PARTIAL]         | Solo ADR-001..003                                         | [docs/decisions](docs/decisions)                                                          |                - | Faltan ADRs de sesiones, dinero, ownership, préstamos, idempotencia y transacciones.                                                               |

## Funcionalidades completas verificables

- Normalización de errores frontend: evita `[object Object]` y tiene test.
- Hashing Argon2 y emisión/validación básica de JWT.
- Modelo server-side de refresh tokens con rotación/revocación implementado.
- Ownership básico en cuentas, transacciones y recursos de planificación.
- Actualización condicional de saldos para impedir updates sobre saldo insuficiente a nivel SQL.
- Ledger de movimientos de préstamos y devoluciones en el caso de uso.
- Entidades/endpoints mínimos de `Debt` e `Installment`.
- Endpoint agregado mínimo de dashboard.
- CI con servicio PostgreSQL, Alembic y coverage configurado.
- Build de Docker, migraciones dentro de contenedor y SPA servida por Nginx.

## Funcionalidades parciales

- Registro/login/logout/refresh: falta suite HTTP completa, CSRF y revocación de access tokens.
- Idempotencia: existe almacenamiento y manejo básico, pero no está demostrada bajo carreras y payload conflictivo.
- Saldos: update condicional existe, pero no hay test concurrente PostgreSQL.
- Préstamos/devoluciones: ledger y saldos se actualizan en casos de uso, pero falta unidad transaccional común, estados parciales explícitos y E2E.
- Deudas/cuotas: persistencia inicial sin pagos ni saldo restante.
- Presupuestos/metas/notificaciones: capacidades básicas sin thresholds/deduplicación completa.
- Dashboard: resumen mínimo, no todas las métricas del producto.
- Frontend: dashboard real inicial, pero sin rutas/feature modules ni todas las mutaciones.
- Coverage: 61.55%, lejos del 100% exigido por SPEC.

## Funcionalidades faltantes

- Pruebas E2E completas.
- Concurrencia y rollback verificados contra PostgreSQL real.
- Alertas 50/80/100 deduplicadas.
- Ejecución segura de recurrentes.
- Pagos y saldo restante de deudas/cuotas.
- Estados formales de ingresos/gastos.
- Dashboard completo con pendientes, próximas obligaciones y estadísticas.
- RBAC aplicado.
- CSRF completo para refresh cookie.
- Tests HTTP de ownership para todos los recursos.
- Downgrade Alembic verificado.

## Riesgos técnicos

1. Los routers siguen controlando `commit`, creando repositorios y orquestando operaciones.
2. `get -> operar -> registrar idempotency key` puede competir bajo doble request.
3. La aceptación de préstamo y la devolución actualizan varias entidades sin una unidad transaccional de aplicación única.
4. Las notificaciones de presupuesto pueden duplicarse al consultar repetidamente.
5. Los repositorios de presupuesto calculan por presupuesto con consultas adicionales.
6. El frontend mantiene toda la UI en `App.tsx` y usa casts genéricos para respuestas.
7. La integración real no tiene pruebas de operaciones financieras; solo conectividad/migración.

## Riesgos de seguridad

1. Credenciales PostgreSQL hardcodeadas en Compose.
2. `JWT_SECRET` conocido por defecto.
3. Access token en `localStorage`.
4. Refresh cookie sin protección CSRF demostrada.
5. Falta de rate limiting en login/registro.
6. Falta de pruebas HTTP sistemáticas de ownership.
7. Idempotencia no demostrada bajo concurrencia.
8. Recursos financieros de préstamos/devoluciones requieren pruebas de autorización y consistencia.

## Deuda técnica

- Separar frontend por features.
- Crear unidad de trabajo/transacción en aplicación.
- Añadir runtime validation de respuestas TypeScript.
- Añadir restricciones CHECK/índices/unique de dominio.
- Completar ADRs y sincronizar documentación fuente.
- Elevar coverage gradualmente sin tests artificiales.
- Resolver warning TypeScript/ESLint mediante upgrade planificado.

## Tests faltantes

- HTTP register/login/refresh/logout/me.
- Duplicados y credenciales inválidas.
- Ownership HTTP para todas las entidades.
- Idempotencia retry y doble submit concurrente.
- Dos gastos concurrentes sobre una cuenta.
- Rollback de fallo después de actualizar el primer saldo.
- Loan accept/reject con fondos y ledger.
- Repayment parcial/completo, saldo, duplicado y autorización.
- Deuda, cuota, pago y saldo pendiente.
- Budget thresholds deduplicados.
- Contribución de meta idempotente.
- Ejecución de recurrencias cuando se defina scheduler.
- E2E completo.

## Inconsistencias documentales

- `docs/SPEC.md` mantiene módulos con checklist pendiente aunque `PHASE4_STATUS.md` declara implementaciones parciales.
- `docs/SECURITY.md` exige refresh seguro, pero no documenta CSRF ni access token en localStorage.
- `docs/ARCHITECTURE.md` no refleja la unidad transaccional pendiente ni el dashboard agregado mínimo.
- `PHASE4_STATUS.md` declara hardening implementado, pero reconoce que no se han ejecutado pruebas PostgreSQL concurrentes.
- CI configura PostgreSQL, pero el test de integración disponible no cubre operaciones financieras reales.

## Conteo audit anterior vs Fase 4.5

El audit anterior clasificó el núcleo como mayoritariamente `PARTIAL`, con refresh, idempotencia, deudas y dashboard como `NOT IMPLEMENTED`. En esta auditoría, el estado mejoró a implementación parcial de esos bloques, pero no a PASS porque falta evidencia de comportamiento completo.

Conteo actual de la matriz principal:

- PASS: 14
- PARTIAL: 39
- FAIL: 2
- NOT IMPLEMENTED: 7

El conteo se refiere a filas principales de esta matriz, no a cada subrequisito del prompt completo. No se considera una mejora válida convertir un requisito en PASS solo por existir un endpoint.

## Recomendaciones priorizadas

1. Corregir el manejo de idempotencia concurrente con reserva atómica de la clave y payload fingerprint.
2. Centralizar la unidad transaccional de operaciones monetarias y cubrir rollback con PostgreSQL.
3. Añadir pruebas HTTP de ownership y sesión, y E2E financieros.
4. Hacer obligatorios los secretos fuera de desarrollo y eliminar credenciales fijas de Compose.
5. Añadir CSRF explícito para refresh cookie o cambiar la estrategia de almacenamiento de sesión.
6. Completar deudas/cuotas y estados de income/expense antes de ampliar dashboard.
7. Implementar thresholds de presupuesto deduplicados.
8. Actualizar SPEC/ARCHITECTURE/SECURITY y crear ADRs de decisiones nuevas.
9. Subir coverage con comportamiento real y ejecutar integración en CI de forma explícita.

## Conclusión

Fase 4.5 mejoró materialmente la base: el error visible del registro está corregido, hay sesiones refresh, saldos SQL condicionales, idempotencia persistente inicial, ledger de préstamos/devoluciones, deudas mínimas, dashboard mínimo y CI con PostgreSQL. No obstante, la Fase 4.5 no puede considerarse completamente cerrada según sus propios criterios: faltan pruebas reales de concurrencia, rollback, idempotencia, ownership HTTP y E2E, además de riesgos de secretos, CSRF y unidad transaccional.
