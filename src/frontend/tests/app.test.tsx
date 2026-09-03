import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "../src/app/App";
import { normalizeApiError } from "../src/services/api";

describe("App", () => {
  it("redirects unauthenticated visitors to login", () => {
    render(
      <QueryClientProvider client={new QueryClient()}>
        <MemoryRouter initialEntries={["/"]}>
          <App />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(
      screen.getByRole("heading", { name: "Bienvenido de nuevo" }),
    ).toBeInTheDocument();
  });
});

describe("normalizeApiError", () => {
  it("formats FastAPI validation errors without object coercion", () => {
    expect(
      normalizeApiError({
        detail: [
          {
            loc: ["body", "password"],
            msg: "String should be at least 12 characters",
          },
        ],
      }),
    ).toBe("String should be at least 12 characters");
  });
});
