@echo off
echo ========================================
echo    IoT Backend API Tester
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "app\main.py" (
    echo ❌ app\main.py not found
    echo Please run this script from the iot-backend directory
    pause
    exit /b 1
)

echo 📋 Available options:
echo 1. Install dependencies
echo 2. Start backend server
echo 3. Start backend + open frontend
echo 4. Exit
echo.

:menu
set /p choice="Choose option (1-4): "

if "%choice%"=="1" (
    echo.
    echo 📦 Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Error installing dependencies
    ) else (
        echo ✅ Dependencies installed successfully!
    )
    echo.
    goto menu
)

if "%choice%"=="2" (
    echo.
    echo 🚀 Starting backend server...
    echo 📝 API Documentation: http://localhost:8000/docs
    echo ⏹️  Press Ctrl+C to stop server
    echo.
    python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    goto menu
)

if "%choice%"=="3" (
    echo.
    echo 🚀 Starting backend server + frontend...
    echo ⏳ Starting server in background...
    
    REM Start server in background
    start /b python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
    REM Wait a bit for server to start
    timeout /t 3 /nobreak >nul
    
    REM Open frontend in browser
    echo 🌐 Opening test interface...
    start "" "frontend_test.html"
    
    echo.
    echo 📝 Backend running at: http://localhost:8000
    echo 🌐 Frontend opened in browser
    echo ⏹️  Press any key to stop server
    echo.
    pause >nul
    
    REM Kill the server process
    taskkill /f /im python.exe >nul 2>&1
    echo ⏹️  Server stopped
    echo.
    goto menu
)

if "%choice%"=="4" (
    echo 👋 Goodbye!
    exit /b 0
)

echo ❌ Invalid choice! Please choose 1-4
echo.
goto menu