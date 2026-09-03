# Backend development script for Windows
Write-Host "Starting FinanLove Backend..." -ForegroundColor Blue
cd src/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
