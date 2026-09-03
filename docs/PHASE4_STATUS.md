# Fase 4: estado de implementación

## Implementado

- Movimientos autenticados de tipo `INCOME`, `EXPENSE` y `TRANSFER`.
- Ingresos y gastos con `Decimal`, validación de importe positivo y control de saldo.
- Transferencias entre cuentas propias, con moneda coincidente y actualización atómica de saldos.
- Préstamos entre usuarios autenticados, con validación de usuarios distintos, importe y estado inicial `REQUESTED`.
- Persistencia SQLAlchemy async y migración Alembic encadenada `0003_transactions_loans`.
- Endpoints versionados `POST/GET /api/v1/transactions` y `POST/GET /api/v1/loans`.
- Flujo de préstamos: aceptar/rechazar solicitudes, devoluciones parciales o totales
  y aceptación/rechazo por el prestamista.
- Presupuestos autenticados por categoría y periodo, con gasto calculado desde
  transacciones `EXPENSE`, restante y porcentaje usado.
- Metas de ahorro con contribuciones y porcentaje de progreso.
- Notificaciones internas autenticadas con listado y marcado de lectura.
- Migraciones encadenadas `0004_add_loan_repayments`, `0005_add_planning_features` y
  `0006_add_transaction_category` y `0007_categories_recurring`.
- Categorías reutilizables autenticadas por propietario (`/api/v1/categories`) y
  plantillas de movimientos recurrentes (`/api/v1/recurring-transactions`). Las
  plantillas conservan cuenta, tipo, importe, categoría, frecuencia y próxima fecha.
- Contribuciones de metas integrables con movimientos mediante `source_account_id`:
  valida ownership/saldo, registra un gasto `Ahorro` y actualiza el progreso.
- Notificaciones automáticas internas para solicitudes y decisiones de préstamos,
  presupuestos excedidos al consultarlos y saldo que llega exactamente a cero tras
  un gasto.
- La migración de categorías y recurrencias es `0007_categories_recurring`.
- Fase 4.5: ownership estricto de cuentas en recurrencias, saldos protegidos por
  actualización condicional, idempotencia persistente mediante `Idempotency-Key`
  para operaciones financieras y refresh tokens server-side con rotación y
  revocación en cookie HttpOnly.
- Los préstamos aceptados y sus devoluciones validan cuentas explícitas de cada
  participante y actualizan los saldos usando la misma sesión transaccional.
- `GET /api/v1/auth/me` expone el rol mínimo (`USER` por defecto); `POST
/api/v1/auth/refresh` y `POST /api/v1/auth/logout` gestionan la sesión refresh.

## Pendiente

- TODO funcional: definir un umbral configurable distinto de cero para “saldo bajo”.
  Hasta entonces la alerta no inventa un umbral y se emite cuando el saldo llega a cero.
- TODO funcional: definir calendario, reintentos e idempotencia de ejecución de
  recurrencias. Por ahora son plantillas persistidas y no se ejecutan automáticamente.
- TODO funcional: definir si una contribución debe ser siempre un gasto y si requiere
  una cuenta por defecto. Sólo se crea movimiento cuando el cliente envía
  explícitamente `source_account_id`; sin él se conserva el comportamiento anterior.
- Limitación conocida: la suite disponible es unitaria y no ejecuta PostgreSQL/Alembic
  en CI; debe ejecutarse `alembic upgrade head` y una prueba concurrente contra
  PostgreSQL antes de desplegar. La clave idempotente requiere que el cliente la
  reutilice exactamente (por usuario y operación).

## Fase 4.5 completada

- Se añadió `GET /api/v1/dashboard` con agregación de balances, ingresos, gastos,
  préstamos activos y metas.
- Se añadieron `Debt` e `Installment` mínimos, migración `0009`, repositorio y
  endpoints autenticados con ownership estricto.
- CI configura PostgreSQL, ejecuta `alembic upgrade head` y aplica cobertura mínima
  del 60%. La prueba PostgreSQL local se omite cuando no existe una URL PostgreSQL.
- La ejecución automática de recurrencias sigue sin implementarse: faltan calendario,
  reintentos e idempotencia de ejecución definidos por producto.
- La semántica de deuda (liquidación, pagos y relación con préstamos) no se inventa;
  esta fase sólo persiste deudas y cuotas abiertas.
