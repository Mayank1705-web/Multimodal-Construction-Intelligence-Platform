#!/usr/bin/env bash
# Starts backend (port 8000) and frontend dev server (port 5173).
set -e
cd "$(dirname "$0")"
[ -f backend/.env ] || cp backend/.env.example backend/.env
(cd backend && python -m uvicorn app.main:app --reload --port 8000) &
BACK=$!
trap "kill $BACK" EXIT
cd frontend && npm install --no-audit --no-fund && npm run dev
