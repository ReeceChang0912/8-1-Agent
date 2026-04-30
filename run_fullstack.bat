@echo off
echo ========================================
echo   家庭智能管家 - 前后端分离版本
echo ========================================
echo.

echo [1/2] 启动后端服务 (FastAPI)...
start "Backend" cmd /k "cd backend && ..\.venv\Scripts\python.exe main.py"

timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务 (React + Vite)...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   服务已启动！
echo   后端: http://localhost:8000
echo   前端: http://localhost:3000
echo   API文档: http://localhost:8000/docs
echo ========================================
echo.
pause
