@echo off
chcp 65001 >nul
echo ========================================
echo   🏡 家庭智能管家 - 启动服务
echo ========================================
echo.

echo [1/2] 启动后端服务 (FastAPI)...
start "Backend - FastAPI" cmd /k "cd /d %~dp0backend && ..\.venv\Scripts\python.exe main.py"

timeout /t 3 /nobreak >nul

echo [2/2] 启动前端服务 (React + Vite)...
start "Frontend - React" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   ✅ 服务启动中...
echo.
echo   🌐 前端界面: http://localhost:3000
echo   🔧 后端 API: http://localhost:8000
echo   📖 API文档: http://localhost:8000/docs
echo.
echo   按任意键关闭此窗口（不影响服务运行）
echo ========================================
pause >nul
