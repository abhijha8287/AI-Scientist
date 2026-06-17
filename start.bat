@echo off
echo Starting AI Scientist...
echo.

echo [1/2] Starting backend (FastAPI on :8000)...
start "AI Scientist Backend" cmd /k "cd /d "%~dp0backend" && pip install -r requirements.txt & uvicorn main:app --reload --port 8000"

timeout /t 4 /nobreak >nul

echo [2/2] Starting frontend (Next.js on :3000)...
start "AI Scientist Frontend" cmd /k "cd /d "%~dp0frontend" && npm install && npm run dev"

echo.
echo Both servers starting. Open http://localhost:3000
