@echo off
echo Starting Systematic Quote Intelligence Server...
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
