#!/bin/bash
# Backend development script
echo "Starting FinanLove Backend..."
cd src/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
