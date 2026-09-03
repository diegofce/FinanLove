import {
  api,
  tokenStore,
  type AccountType,
  type TransactionType,
  type User,
} from "@/services/api";
import { useMutation, useQueries, useQueryClient } from "@tanstack/react-query";
import { FormEvent, ReactNode, useState } from "react";
import { Link, Navigate, Route, Routes, useNavigate } from "react-router-dom";

const money = (value: string): string =>
  new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(Number(value));

function Shell({
  user,
  onLogout,
  children,
}: {
  user: User;
  onLogout: () => void;
  children: ReactNode;
}) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand">
          <span className="brand-mark">F</span>
          <span>FinanLove</span>
        </Link>
        <div className="profile">
          <div className="avatar">
            {user.first_name[0]}
            {user.last_name[0]}
          </div>
          <div>
            <strong>
              {user.first_name} {user.last_name}
            </strong>
            <small>@{user.username}</small>
          </div>
        </div>
        <nav>
          <Link to="/">Resumen</Link>
          <a href="#activity">Actividad</a>
          <a href="#planning">Planificación</a>
        </nav>
        <button className="ghost-button logout" onClick={onLogout}>
          Cerrar sesión
        </button>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}

function ProtectedRoute({
  user,
  children,
}: {
  user: User | null;
  children: ReactNode;
}) {
  return user ? <>{children}</> : <Navigate to="/login" replace />;
}

function AuthPage({
  mode,
  onLogin,
}: {
  mode: "login" | "register";
  onLogin: (user: User) => void;
}) {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const login = useMutation({
    mutationFn: api.login,
    onSuccess: (result) => {
      onLogin(result.user);
      navigate("/");
    },
    onError: (reason: Error) => setError(reason.message),
  });
  const register = useMutation({
    mutationFn: api.register,
    onSuccess: () => navigate("/login"),
    onError: (reason: Error) => setError(reason.message),
  });
  const submit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    setError(null);
    const data = Object.fromEntries(
      new FormData(event.currentTarget).entries(),
    );
    if (mode === "login")
      login.mutate({
        login: String(data.login),
        password: String(data.password),
      });
    else
      register.mutate({
        username: String(data.username),
        email: String(data.email),
        first_name: String(data.first_name),
        last_name: String(data.last_name),
        password: String(data.password),
      });
  };
  const busy = login.isPending || register.isPending;
  return (
    <div className="auth-page">
      <div className="auth-panel">
        <Link to="/" className="brand">
          <span className="brand-mark">F</span>
          <span>FinanLove</span>
        </Link>
        <p className="eyebrow">Tu dinero, en común</p>
        <h1>
          {mode === "login"
            ? "Bienvenido de nuevo"
            : "Crea tu espacio financiero"}
        </h1>
        <p className="muted">
          {mode === "login"
            ? "Accede para continuar donde lo dejaste."
            : "Organiza tus cuentas y decisiones compartidas."}
        </p>
        <form onSubmit={submit} className="form-stack">
          {mode === "register" && (
            <>
              <label>
                Usuario
                <input name="username" required minLength={3} />
              </label>
              <div className="form-grid">
                <label>
                  Nombre
                  <input name="first_name" required />
                </label>
                <label>
                  Apellido
                  <input name="last_name" required />
                </label>
              </div>
              <label>
                Correo
                <input name="email" type="email" required />
              </label>
              <label>
                Contraseña
                <input
                  name="password"
                  type="password"
                  minLength={12}
                  required
                />
              </label>
              <label>
                Confirmar contraseña
                <input
                  name="password_confirmation"
                  type="password"
                  minLength={12}
                  required
                />
              </label>
            </>
          )}
          <label>
            {mode === "login" ? "Usuario o correo" : ""}
            <input
              name="login"
              type={mode === "login" ? "text" : "password"}
              required={mode === "login"}
              hidden={mode === "register"}
            />
          </label>
          {mode === "login" && (
            <label>
              Contraseña
              <input name="password" type="password" required />
            </label>
          )}
          {error && <div className="error-box">{error}</div>}
          <button className="primary-button" disabled={busy}>
            {busy
              ? "Procesando..."
              : mode === "login"
                ? "Entrar"
                : "Registrarme"}
          </button>
        </form>
        <p className="switch-auth">
          {mode === "login" ? "¿Aún no tienes cuenta?" : "¿Ya tienes cuenta?"}{" "}
          <Link to={mode === "login" ? "/register" : "/login"}>
            {mode === "login" ? "Regístrate" : "Inicia sesión"}
          </Link>
        </p>
      </div>
    </div>
  );
}

function Dashboard() {
  const client = useQueryClient();
  const results = useQueries({
    queries: [
      { queryKey: ["accounts"], queryFn: api.accounts },
      { queryKey: ["transactions"], queryFn: api.transactions },
      { queryKey: ["loans"], queryFn: api.loans },
      { queryKey: ["budgets"], queryFn: api.budgets },
      { queryKey: ["goals"], queryFn: api.goals },
      { queryKey: ["notifications"], queryFn: api.notifications },
      { queryKey: ["dashboard"], queryFn: api.dashboard },
      { queryKey: ["debts"], queryFn: api.debts },
    ],
  });
  const [showForm, setShowForm] = useState<
    "account" | "transaction" | "loan" | null
  >(null);
  const accounts = results[0].data ?? [];
  const transactions = results[1].data ?? [];
  const loans = results[2].data ?? [];
  const budgets = results[3].data ?? [];
  const goals = results[4].data ?? [];
  const notifications = results[5].data ?? [];
  const dashboard = results[6].data;
  const debts = results[7].data ?? [];
  const firstError = results.find((result) => result.error)?.error as
    | Error
    | undefined;
  const create = useMutation({
    mutationFn: async (input: {
      kind: "account" | "transaction" | "loan";
      data: Record<string, unknown>;
    }) =>
      input.kind === "account"
        ? api.createAccount(input.data)
        : input.kind === "transaction"
          ? api.createTransaction(input.data)
          : api.createLoan(input.data),
    onSuccess: () => {
      setShowForm(null);
      void client.invalidateQueries();
    },
  });
  const total =
    dashboard?.total_balance ??
    accounts.reduce((sum, account) => sum + Number(account.current_balance), 0);
  return (
    <div>
      <header className="topbar">
        <div>
          <p className="eyebrow">Resumen financiero</p>
          <h1>Tu panorama</h1>
        </div>
        <button
          className="primary-button"
          onClick={() => setShowForm("transaction")}
        >
          + Nuevo movimiento
        </button>
      </header>
      {firstError && (
        <div className="error-box page-error">{firstError.message}</div>
      )}
      <section className="hero-metric">
        <div>
          <span className="metric-label">Balance consolidado</span>
          <strong>{money(String(total))}</strong>
          <span className="metric-caption">
            {accounts.length}{" "}
            {accounts.length === 1 ? "cuenta conectada" : "cuentas conectadas"}
          </span>
        </div>
        <div className="metric-actions">
          <button onClick={() => setShowForm("account")}>+ Cuenta</button>
          <button onClick={() => setShowForm("loan")}>+ Préstamo</button>
        </div>
      </section>
      <section className="summary-grid">
        <Metric
          title="Cuentas"
          value={accounts.length}
          loading={results[0].isLoading}
        />
        <Metric
          title="Movimientos"
          value={transactions.length}
          loading={results[1].isLoading}
        />
        <Metric
          title="Préstamos activos"
          value={
            loans.filter(
              (loan) =>
                loan.status === "ACCEPTED" || loan.status === "REQUESTED",
            ).length
          }
          loading={results[2].isLoading}
        />
        <Metric
          title="Alertas"
          value={notifications.filter((item) => !item.read_at).length}
          loading={results[5].isLoading}
        />
      </section>
      <div className="dashboard-grid">
        <section className="panel">
          <PanelTitle title="Deudas" />
          <ListState
            loading={results[7].isLoading}
            empty={debts.length === 0}
            emptyText="No hay deudas registradas."
          >
            <div className="list">
              {debts.slice(0, 4).map((item) => (
                <div className="list-row" key={item.id}>
                  <div className="row-main">
                    <strong>{item.creditor}</strong>
                    <small>{item.description}</small>
                  </div>
                  <strong>{money(item.amount)}</strong>
                </div>
              ))}
            </div>
          </ListState>
        </section>
        <section className="panel" id="activity">
          <PanelTitle title="Movimientos recientes" action="Ver actividad" />
          <ListState
            loading={results[1].isLoading}
            empty={transactions.length === 0}
            emptyText="Aún no hay movimientos."
          >
            <div className="list">
              {transactions.slice(0, 5).map((item) => (
                <div className="list-row" key={item.id}>
                  <div
                    className={`type-dot ${item.transaction_type.toLowerCase()}`}
                  ></div>
                  <div className="row-main">
                    <strong>{item.description}</strong>
                    <small>{item.category ?? "Sin categoría"}</small>
                  </div>
                  <strong
                    className={
                      item.transaction_type === "INCOME"
                        ? "positive"
                        : "negative"
                    }
                  >
                    {item.transaction_type === "INCOME" ? "+" : "-"}
                    {money(item.amount)}
                  </strong>
                </div>
              ))}
            </div>
          </ListState>
        </section>
        <section className="panel">
          <PanelTitle
            title="Cuentas"
            action="Nueva cuenta"
            onAction={() => setShowForm("account")}
          />
          <ListState
            loading={results[0].isLoading}
            empty={accounts.length === 0}
            emptyText="Crea tu primera cuenta."
          >
            <div className="list">
              {accounts.map((item) => (
                <div className="list-row" key={item.id}>
                  <div className="account-icon">{item.account_type[0]}</div>
                  <div className="row-main">
                    <strong>{item.name}</strong>
                    <small>
                      {item.account_type} · {item.currency}
                    </small>
                  </div>
                  <strong>{money(item.current_balance)}</strong>
                </div>
              ))}
            </div>
          </ListState>
        </section>
        <section className="panel" id="planning">
          <PanelTitle title="Planificación" />
          <ListState
            loading={results[3].isLoading || results[4].isLoading}
            empty={budgets.length === 0 && goals.length === 0}
            emptyText="No hay presupuestos ni metas todavía."
          >
            <div className="planning-list">
              {budgets.map((item) => (
                <div key={item.id}>
                  <div className="row-between">
                    <strong>{item.category}</strong>
                    <span>
                      {money(item.spent_amount)} / {money(item.limit_amount)}
                    </span>
                  </div>
                  <div className="progress">
                    <span
                      style={{
                        width: `${Math.min(Number(item.percentage_used), 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
              {goals.map((item) => (
                <div key={item.id}>
                  <div className="row-between">
                    <strong>Meta: {item.name}</strong>
                    <span>{Number(item.progress_percentage).toFixed(0)}%</span>
                  </div>
                  <div className="progress teal">
                    <span
                      style={{
                        width: `${Math.min(Number(item.progress_percentage), 100)}%`,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </ListState>
        </section>
        <section className="panel">
          <PanelTitle title="Préstamos" />
          <ListState
            loading={results[2].isLoading}
            empty={loans.length === 0}
            emptyText="No hay préstamos registrados."
          >
            <div className="list">
              {loans.slice(0, 4).map((item) => (
                <div className="list-row" key={item.id}>
                  <div className="loan-icon">↗</div>
                  <div className="row-main">
                    <strong>{item.description}</strong>
                    <small>{item.status}</small>
                  </div>
                  <strong>{money(item.amount)}</strong>
                </div>
              ))}
            </div>
          </ListState>
        </section>
        <section className="panel notifications">
          <PanelTitle title="Notificaciones" />
          <ListState
            loading={results[5].isLoading}
            empty={notifications.length === 0}
            emptyText="No tienes notificaciones."
          >
            <div className="list">
              {notifications.slice(0, 4).map((item) => (
                <div
                  className={`notification ${item.read_at ? "read" : ""}`}
                  key={item.id}
                >
                  <span></span>
                  <div>
                    <strong>{item.title}</strong>
                    <p>{item.message}</p>
                  </div>
                </div>
              ))}
            </div>
          </ListState>
        </section>
      </div>
      {showForm && (
        <DataForm
          kind={showForm}
          accounts={accounts.map((account) => ({
            id: account.id,
            name: account.name,
          }))}
          onClose={() => setShowForm(null)}
          onSubmit={(data) => create.mutate({ kind: showForm, data })}
          busy={create.isPending}
          error={create.error instanceof Error ? create.error.message : null}
        />
      )}
    </div>
  );
}

function Metric({
  title,
  value,
  loading,
}: {
  title: string;
  value: number;
  loading: boolean;
}) {
  return (
    <div className="metric-card">
      <span>{title}</span>
      <strong>{loading ? "..." : value}</strong>
    </div>
  );
}
function PanelTitle({
  title,
  action,
  onAction,
}: {
  title: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="panel-title">
      <h2>{title}</h2>
      {action && (
        <button onClick={onAction}>
          {action} <span>→</span>
        </button>
      )}
    </div>
  );
}
function ListState({
  loading,
  empty,
  emptyText,
  children,
}: {
  loading: boolean;
  empty: boolean;
  emptyText: string;
  children: ReactNode;
}) {
  if (loading) return <div className="state">Cargando datos...</div>;
  if (empty) return <div className="state">{emptyText}</div>;
  return <>{children}</>;
}

function DataForm({
  kind,
  accounts,
  onClose,
  onSubmit,
  busy,
  error,
}: {
  kind: "account" | "transaction" | "loan";
  accounts: { id: string; name: string }[];
  onClose: () => void;
  onSubmit: (data: Record<string, unknown>) => void;
  busy: boolean;
  error: string | null;
}) {
  const submit = (event: FormEvent<HTMLFormElement>): void => {
    event.preventDefault();
    const raw = Object.fromEntries(new FormData(event.currentTarget).entries());
    const data: Record<string, unknown> = { ...raw };
    if (kind === "account") data.current_balance = raw.current_balance || "0";
    onSubmit(data);
  };
  return (
    <div className="modal-backdrop">
      <div className="modal">
        <div className="panel-title">
          <h2>
            {kind === "account"
              ? "Nueva cuenta"
              : kind === "transaction"
                ? "Nuevo movimiento"
                : "Nuevo préstamo"}
          </h2>
          <button onClick={onClose}>×</button>
        </div>
        <form onSubmit={submit} className="form-stack">
          {kind === "account" && (
            <>
              <label>
                Nombre
                <input name="name" required />
              </label>
              <label>
                Tipo
                <select
                  name="account_type"
                  defaultValue={"BANK" satisfies AccountType}
                >
                  <option value="BANK">Banco</option>
                  <option value="WALLET">Billetera</option>
                  <option value="CASH">Efectivo</option>
                  <option value="OTHER">Otro</option>
                </select>
              </label>
              <label>
                Saldo inicial
                <input
                  name="current_balance"
                  type="number"
                  min="0"
                  step="0.01"
                  defaultValue="0"
                />
              </label>
            </>
          )}
          {kind === "transaction" && (
            <>
              <label>
                Cuenta
                <select name="account_id" required>
                  {accounts.map((account) => (
                    <option value={account.id} key={account.id}>
                      {account.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Tipo
                <select
                  name="transaction_type"
                  defaultValue={"EXPENSE" satisfies TransactionType}
                >
                  <option value="EXPENSE">Gasto</option>
                  <option value="INCOME">Ingreso</option>
                  <option value="TRANSFER">Transferencia</option>
                </select>
              </label>
              <label>
                Importe
                <input
                  name="amount"
                  type="number"
                  min="0.01"
                  step="0.01"
                  required
                />
              </label>
              <label>
                Descripción
                <input name="description" required />
              </label>
              <label>
                Categoría
                <input name="category" />
              </label>
            </>
          )}
          {kind === "loan" && (
            <>
              <label>
                ID de quien presta
                <input name="lender_id" placeholder="UUID" required />
              </label>
              <label>
                Importe
                <input
                  name="amount"
                  type="number"
                  min="0.01"
                  step="0.01"
                  required
                />
              </label>
              <label>
                Descripción
                <input name="description" required />
              </label>
              <label>
                Fecha límite
                <input name="due_date" type="datetime-local" />
              </label>
            </>
          )}
          {error && <div className="error-box">{error}</div>}
          <button className="primary-button" disabled={busy}>
            {busy ? "Guardando..." : "Guardar"}
          </button>
        </form>
      </div>
    </div>
  );
}

function App() {
  const [user, setUser] = useState<User | null>(() => tokenStore.getUser());
  const logout = (): void => {
    tokenStore.clear();
    setUser(null);
  };
  return (
    <Routes>
      <Route
        path="/login"
        element={<AuthPage mode="login" onLogin={setUser} />}
      />
      <Route
        path="/register"
        element={<AuthPage mode="register" onLogin={setUser} />}
      />
      <Route
        path="*"
        element={
          <ProtectedRoute user={user}>
            <Shell user={user as User} onLogout={logout}>
              <Dashboard />
            </Shell>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
