@echo off
setlocal enabledelayedexpansion

:: ==================================================
::     BHARAT BIZ-AGENT - WINDOWS SETUP SCRIPT
:: ==================================================

echo.
echo Checking Python version...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    pause
    exit /b 1
)

:: Check for Python 3.11+
for /f "tokens=2" %%v in ('python --version') do set ver=%%v
for /f "tokens=1,2 delims=." %%a in ("%ver%") do (
    set major=%%a
    set minor=%%b
)

if %major% LSS 3 (
    goto :version_error
) else (
    if %major% EQU 3 if %minor% LSS 11 goto :version_error
)

echo [OK] Python %ver% found.
goto :venv_setup

:version_error
echo [ERROR] Python 3.11+ required (found: %ver%)
pause
exit /b 1

:venv_setup
echo.
echo Creating virtual environment...
if exist venv (
    echo [!] Virtual environment already exists.
    set /p "recreate=Do you want to recreate it? (y/n): "
    if /i "!recreate!"=="y" (
        echo Removing old venv...
        rmdir /s /q venv
        python -m venv venv
        echo [OK] Virtual environment recreated.
    )
) else (
    python -m venv venv
    echo [OK] Virtual environment created.
)

echo.
echo Activating virtual environment...
:: Activation on Windows uses Scripts folder instead of bin
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    exit /b 1
)
echo [OK] Virtual environment activated.

echo.
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo [OK] pip upgraded.

echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed.
    exit /b 1
)
echo [OK] Dependencies installed.

echo.
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo [OK] .env file created.
    echo [!] Please edit .env with your API keys.
) else (
    echo [!] .env file already exists.
)

echo.
echo Initializing database...
python database.py
echo [OK] Database initialized with sample data.

echo.
echo Verifying database...
python test_agent.py check
echo [OK] Database verified.

echo.
echo Creating directories...
if not exist media mkdir media
if not exist logs mkdir logs
echo [OK] Directories created.

echo.
echo ==================================================
echo            SETUP COMPLETED! 
echo ==================================================
echo.
echo Next steps:
echo.
echo 1. Edit your .env file with API credentials:
echo    notepad .env
echo.
echo 2. Get your API keys:
echo    - WhatsApp: https://developers.facebook.com/
echo    - Gemini: https://makersuite.google.com/app/apikey
echo.
echo 3. Start the server:
echo    call venv\Scripts\activate
echo    uvicorn app:app --reload
echo.
echo 4. In another terminal, expose with ngrok:
echo    ngrok http 8000
echo.
echo 5. Configure WhatsApp webhook with ngrok URL
echo.
echo 6. Or run the test suite:
echo    python test_agent.py demo
echo.
echo ==================================================
echo For detailed instructions, see README.md
echo ==================================================
pause