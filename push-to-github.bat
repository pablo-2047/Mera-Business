@echo off
REM GitHub Push Script for Mera Business (Windows)
REM This script helps you safely push code to GitHub without exposing secrets

echo ==================================
echo Mera Business - GitHub Push Script
echo ==================================
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo Error: Not in a git repository!
    echo Run: git init
    pause
    exit /b 1
)

echo [Step 1] Checking for sensitive files...

REM Check if .env exists
if exist ".env" (
    echo Warning: .env file found!
    findstr /C:".env" .gitignore >nul 2>&1
    if errorlevel 1 (
        echo CRITICAL: .env is NOT in .gitignore!
        echo Adding .env to .gitignore...
        echo .env >> .gitignore
    ) else (
        echo .env is properly ignored
    )
)

REM Verify .gitignore exists
if not exist ".gitignore" (
    echo Creating .gitignore...
    (
        echo # Environment variables with secrets
        echo .env
        echo.
        echo # Python
        echo __pycache__/
        echo *.py[cod]
        echo venv/
        echo *.db
        echo *.db-journal
        echo logs/
        echo *.log
        echo.
        echo # Media
        echo media/
        echo chat_media/
        echo invoices/
        echo.
        echo # IDE
        echo .vscode/
        echo .idea/
        echo.
        echo # OS
        echo .DS_Store
        echo Thumbs.db
        echo.
        echo # Docker secrets
        echo secrets/
    ) > .gitignore
)

echo.
echo [Step 2] Checking for hardcoded secrets...

REM Search for potential API keys (basic check)
findstr /R "AIzaSy" *.py >nul 2>&1
if not errorlevel 1 (
    echo WARNING: Potential API keys found in Python files!
    echo Please review your code before committing.
)

echo.
echo [Step 3] Verifying required files...

set missing=0

if not exist "README.md" (
    echo Missing: README.md
    set missing=1
)
if not exist ".gitignore" (
    echo Missing: .gitignore
    set missing=1
)
if not exist ".env.example" (
    echo Missing: .env.example
    set missing=1
)
if not exist "requirements.txt" (
    echo Missing: requirements.txt
    set missing=1
)
if not exist "Dockerfile" (
    echo Missing: Dockerfile
    set missing=1
)
if not exist "docker-compose.yml" (
    echo Missing: docker-compose.yml
    set missing=1
)

if %missing%==1 (
    echo.
    echo ERROR: Missing required files!
    pause
    exit /b 1
)

echo All required files present

echo.
echo [Step 4] Staging files...

git add .

echo.
echo Files to be committed:
git status --short

echo.
echo Review the files above.
pause

echo.
echo [Step 5] Creating commit...

set /p commit_message="Enter commit message (or press Enter for default): "

if "%commit_message%"=="" (
    set commit_message=Update: Production-ready Docker setup with documentation
)

git commit -m "%commit_message%"

echo.
echo [Step 6] Checking remote repository...

git remote | findstr "origin" >nul 2>&1
if errorlevel 1 (
    echo No remote 'origin' found.
    set /p repo_url="Enter your GitHub repository URL: "
    
    if not "!repo_url!"=="" (
        git remote add origin "!repo_url!"
        echo Remote added: !repo_url!
    ) else (
        echo No URL provided. Skipping remote setup.
        pause
        exit /b 1
    )
)

echo.
echo [Step 7] Pushing to GitHub...

REM Get current branch
for /f %%i in ('git branch --show-current') do set branch=%%i

if "%branch%"=="" (
    set branch=main
    git branch -M main
)

echo Pushing to branch: %branch%

git push -u origin %branch%

if errorlevel 1 (
    echo.
    echo Push failed!
    echo This might be because:
    echo 1. You need to authenticate
    echo 2. The repository doesn't exist yet
    echo 3. You don't have permission
    echo.
    echo To manually push, run:
    echo   git push -u origin %branch%
    pause
    exit /b 1
)

echo.
echo ==================================
echo SUCCESS! Pushed to GitHub!
echo ==================================
echo.
echo Your repository is now updated with:
echo - Production-ready Dockerfile
echo - Docker Compose configuration
echo - Comprehensive README
echo - Security documentation
echo - Judge quickstart guide
echo - .gitignore protecting secrets
echo.
echo Next steps:
echo 1. Visit your GitHub repository
echo 2. Verify README looks good
echo 3. Consider deploying to Railway/Render
echo 4. Share the repository link with judges
echo.
pause
