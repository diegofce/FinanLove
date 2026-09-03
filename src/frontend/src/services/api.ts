export type AccountType = "BANK" | "WALLET" | "CASH" | "OTHER";
export type TransactionType = "INCOME" | "EXPENSE" | "TRANSFER";
export type LoanStatus = "REQUESTED" | "ACCEPTED" | "REJECTED" | "SETTLED";
export type DebtStatus = "OPEN" | "SETTLED";

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
}

export interface Account {
  id: string;
  name: string;
  account_type: AccountType;
  currency: string;
  current_balance: string;
  is_active: boolean;
}

export interface Transaction {
  id: string;
  account_id: string;
  transaction_type: TransactionType;
  amount: string;
  description: string;
  category: string | null;
  occurred_at: string | null;
}

export interface Loan {
  id: string;
  borrower_id: string;
  lender_id: string;
  amount: string;
  description: string;
  status: LoanStatus;
  due_date: string | null;
}

export interface Budget {
  id: string;
  category: string;
  period_start: string;
  period_end: string;
  limit_amount: string;
  spent_amount: string;
  remaining_amount: string;
  percentage_used: string;
}

export interface Goal {
  id: string;
  name: string;
  target_amount: string;
  contributed_amount: string;
  deadline: string | null;
  progress_percentage: string;
}

export interface Notification {
  id: string;
  title: string;
  message: string;
  read_at: string | null;
}

export interface Debt {
  id: string;
  owner_id: string;
  creditor: string;
  amount: string;
  description: string;
  due_date: string | null;
  status: DebtStatus;
}

export interface Installment {
  id: string;
  debt_id: string;
  amount: string;
  due_date: string;
  status: DebtStatus;
}

export interface DashboardSummary {
  total_balance: string;
  income: string;
  expenses: string;
  active_loans: number;
  goals: number;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

interface RegisterPayload {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  password: string;
}

interface LoginPayload {
  login: string;
  password: string;
}

const API_ROOT = "/api/v1";
const TOKEN_KEY = "finanlove.access_token";
const USER_KEY = "finanlove.user";

export const tokenStore = {
  get: (): string | null => localStorage.getItem(TOKEN_KEY),
  set: (token: string): void => localStorage.setItem(TOKEN_KEY, token),
  setUser: (user: User): void =>
    localStorage.setItem(USER_KEY, JSON.stringify(user)),
  getUser: (): User | null => {
    const value = localStorage.getItem(USER_KEY);
    if (!value) return null;
    try {
      const parsed: unknown = JSON.parse(value);
      if (
        typeof parsed === "object" &&
        parsed !== null &&
        "id" in parsed &&
        "username" in parsed
      )
        return parsed as User;
    } catch {
      return null;
    }
    return null;
  },
  clear: (): void => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_ROOT}${path}`, { ...options, headers });
  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null);
    throw new Error(normalizeApiError(body));
  }
  return (await response.json()) as T;
}

export function normalizeApiError(body: unknown): string {
  if (typeof body === "string") return body;
  if (typeof body !== "object" || body === null) {
    return "No se pudo completar la solicitud";
  }
  if ("detail" in body) return formatErrorDetail(body.detail);
  if ("message" in body && typeof body.message === "string") {
    return body.message;
  }
  return "No se pudo completar la solicitud";
}

function formatErrorDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.flatMap((item) =>
      typeof item === "object" &&
      item !== null &&
      "msg" in item &&
      typeof item.msg === "string"
        ? [item.msg]
        : [],
    );
    return messages.length > 0
      ? messages.join(". ")
      : "Los datos enviados no son validos";
  }
  if (
    typeof detail === "object" &&
    detail !== null &&
    "message" in detail &&
    typeof detail.message === "string"
  ) {
    return detail.message;
  }
  return "No se pudo completar la solicitud";
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  body: JSON.stringify(body),
});

export const api = {
  login: async (payload: LoginPayload): Promise<TokenResponse> => {
    const result = await request<TokenResponse>(
      "/auth/login",
      json("POST", payload),
    );
    tokenStore.set(result.access_token);
    tokenStore.setUser(result.user);
    return result;
  },
  register: (payload: RegisterPayload): Promise<User> =>
    request<User>("/auth/register", json("POST", payload)),
  accounts: (): Promise<Account[]> => request<Account[]>("/accounts"),
  createAccount: (payload: Record<string, unknown>): Promise<Account> =>
    request<Account>("/accounts", json("POST", payload)),
  transactions: (): Promise<Transaction[]> =>
    request<Transaction[]>("/transactions"),
  createTransaction: (payload: Record<string, unknown>): Promise<Transaction> =>
    request<Transaction>("/transactions", json("POST", payload)),
  loans: (): Promise<Loan[]> => request<Loan[]>("/loans"),
  createLoan: (payload: Record<string, unknown>): Promise<Loan> =>
    request<Loan>("/loans", json("POST", payload)),
  budgets: (): Promise<Budget[]> => request<Budget[]>("/budgets"),
  goals: (): Promise<Goal[]> => request<Goal[]>("/goals"),
  notifications: (): Promise<Notification[]> =>
    request<Notification[]>("/notifications"),
  dashboard: (): Promise<DashboardSummary> =>
    request<DashboardSummary>("/dashboard"),
  debts: (): Promise<Debt[]> => request<Debt[]>("/debts"),
  createDebt: (payload: Record<string, unknown>): Promise<Debt> =>
    request<Debt>("/debts", json("POST", payload)),
  installments: (debtId: string): Promise<Installment[]> =>
    request<Installment[]>(`/debts/${debtId}/installments`),
  createInstallment: (
    debtId: string,
    payload: Record<string, unknown>,
  ): Promise<Installment> =>
    request<Installment>(
      `/debts/${debtId}/installments`,
      json("POST", payload),
    ),
  markNotificationRead: (id: string): Promise<Notification> =>
    request<Notification>(`/notifications/${id}/read`, { method: "PATCH" }),
};
