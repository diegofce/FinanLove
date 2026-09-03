from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.presentation.accounts import router as accounts_router
from app.presentation.auth import router as auth_router
from app.presentation.dashboard import router as dashboard_router
from app.presentation.debts import router as debts_router
from app.presentation.loans import router as loans_router
from app.presentation.planning import router as planning_router
from app.presentation.transactions import router as transactions_router

app = FastAPI(
    title="FinanLove API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(accounts_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
app.include_router(loans_router, prefix="/api/v1")
app.include_router(planning_router, prefix="/api/v1")
app.include_router(debts_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
