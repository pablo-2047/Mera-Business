@echo off
REM Final verification script before GitHub push

echo ==========================================
echo Pre-Push Security and Quality Verification
echo ==========================================
echo.

set ERRORS=0
set WARNINGS=0

echo [Security Checks]
echo.

REM 1. Check .gitignore has .env
echo Checking .gitignore has .env...
findstr /C:".env" .gitignore >nul 2>&1
if errorlevel 1 (
    echo [X] .env missing from .gitignore
    set /a ERRORS+=1
) else (
    echo [OK] .env in .gitignore
)

REM 2. Check .env is not tracked by git
echo Checking .env is not in git...
git ls-files --error-unmatch .env >nul 2>&1
if not errorlevel 1 (
    echo [X] DANGER: .env is tracked by git!
    echo     Run: git rm --cached .env
    set /a ERRORS+=1
) else (
    echo [OK] .env not tracked
)

REM 3. Check for API keys in code
echo Checking for hardcoded API keys...
findstr /R "AIzaSy" *.py >nul 2>&1
if not errorlevel 1 (
    echo [!] Warning: Found potential API keys
    set /a WARNINGS+=1
) else (
    echo [OK] No hardcoded keys found
)

echo.
echo [Required Files]
echo.

set required=README.md JUDGE_QUICKSTART.md HOW_TO_RUN.md SECURITY.md .gitignore .env.example Dockerfile docker-compose.yml requirements.txt app.py database.py

for %%f in (%required%) do (
    if exist "%%f" (
        echo [OK] %%f
    ) else (
        echo [X] %%f missing
        set /a ERRORS+=1
    )
)

echo.
echo [Docker Configuration]
echo.

if exist "Dockerfile" (
    echo [OK] Dockerfile
) else (
    echo [X] Dockerfile missing
    set /a ERRORS+=1
)

if exist "docker-compose.yml" (
    echo [OK] docker-compose.yml
) else (
    echo [X] docker-compose.yml missing
    set /a ERRORS+=1
)

if exist ".dockerignore" (
    echo [OK] .dockerignore
) else (
    echo [!] .dockerignore missing (recommended)
    set /a WARNINGS+=1
)

echo.
echo ==========================================
echo SUMMARY
echo ==========================================
echo.

if %ERRORS% EQU 0 (
    if %WARNINGS% EQU 0 (
        echo [OK] ALL CHECKS PASSED!
        echo.
        echo Your project is ready to push to GitHub!
        echo.
        echo Next steps:
        echo   git add .
        echo   git commit -m "Production-ready: Docker, docs, security"
        echo   git push origin main
    ) else (
        echo [!] %WARNINGS% WARNING(S)
        echo.
        echo Your project is mostly ready, but has minor issues.
        echo You can proceed with push, but consider fixing warnings.
    )
) else (
    echo [X] %ERRORS% ERROR(S), %WARNINGS% WARNING(S)
    echo.
    echo Please fix the errors above before pushing to GitHub!
)

echo.
pause
