@echo off
rem ==============================================================================
rem Student Attendance Management System - Automated Setup & Run Script (Windows)
rem ==============================================================================
rem Automatically checks & installs:
rem 1. Python 3
rem 2. MySQL / MariaDB Server (via winget or choco)
rem 3. Python virtualenv & dependencies from requirements.txt
rem 4. Database creation & seeding (student_attendance_db)
rem 5. Launches the app and opens the browser
rem ==============================================================================

setlocal enabledelayedexpansion
title Student Attendance Management System - Setup ^& Run

echo ======================================================================
echo    STUDENT ATTENDANCE MANAGEMENT SYSTEM - WINDOWS SETUP ^& RUN
echo ======================================================================
echo.

cd /d "%~dp0"

rem ------------------------------------------------------------------------------
rem 1. Check Python Installation
rem ------------------------------------------------------------------------------
echo [1/5] Checking Python installation...
set "PY_CMD="

python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
) else (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=py"
    )
)

if "%PY_CMD%"=="" (
    echo [!] Python is not found in system PATH.
    echo [*] Attempting to install Python via Windows Package Manager (winget)...
    winget --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [*] Installing Python 3.12 via winget...
        winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
        echo [!] Python installation finished. Please restart this script if environment variables do not refresh.
        set "PY_CMD=python"
    ) else (
        echo [ERROR] Could not automatically install Python.
        echo Please download and install Python 3 from: https://www.python.org/downloads/
        echo (IMPORTANT: Check the box "Add Python to PATH" during installation!)
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%i in ('%PY_CMD% --version') do set "PY_VER=%%i"
echo [OK] Found %PY_VER%
echo.

rem ------------------------------------------------------------------------------
rem 2. Check & Install MySQL / MariaDB Server
rem ------------------------------------------------------------------------------
echo [2/5] Checking MySQL / MariaDB Server...
set "MYSQL_FOUND=0"

mysql --version >nul 2>&1
if %errorlevel% equ 0 (
    set "MYSQL_FOUND=1"
) else (
    rem Check common Windows MySQL / MariaDB paths
    if exist "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" set "MYSQL_FOUND=1"
    if exist "C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe" set "MYSQL_FOUND=1"
    if exist "C:\Program Files\MariaDB*\bin\mysql.exe" set "MYSQL_FOUND=1"
    if exist "C:\xampp\mysql\bin\mysql.exe" set "MYSQL_FOUND=1"
)

if "%MYSQL_FOUND%"=="0" (
    echo [!] MySQL / MariaDB not detected.
    echo [*] Checking for Windows Package Manager (winget) to install MariaDB / MySQL...
    winget --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [*] Installing MariaDB Server via winget (lightweight, fully MySQL-compatible)...
        winget install --id MariaDB.Server -e --accept-package-agreements --accept-source-agreements
        echo [OK] Database server package installed.
    ) else (
        echo [NOTE] winget not found. If you use XAMPP, start the MySQL module.
        echo Otherwise download MySQL from: https://dev.mysql.com/downloads/installer/
    )
)

rem Ensure MySQL / MariaDB Windows service is running
echo [*] Checking database Windows service status...
net start MySQL >nul 2>&1
if %errorlevel% neq 0 (
    net start MySQL80 >nul 2>&1
    if !errorlevel! neq 0 (
        net start MariaDB >nul 2>&1
    )
)
echo [OK] Database service check completed.
echo.

rem ------------------------------------------------------------------------------
rem 3. Setup Python Virtual Environment & Dependencies
rem ------------------------------------------------------------------------------
echo [3/5] Setting up virtual environment...

if not exist "venv" (
    echo [*] Creating virtual environment in venv folder...
    %PY_CMD% -m venv venv
)

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment creation failed.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo [OK] Virtual environment activated.

echo [*] Installing and updating required Python packages...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
echo [OK] Python dependencies installed successfully.
echo.

rem ------------------------------------------------------------------------------
rem 4. Initialize Database & Tables
rem ------------------------------------------------------------------------------
echo [4/5] Initializing Database (student_attendance_db) ^& Tables...
python setup_db.py
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Database setup encountered an issue.
    echo Please verify MySQL is running and check your .env credentials if needed.
    echo.
)
echo.

rem ------------------------------------------------------------------------------
rem 5. Launch Application
rem ------------------------------------------------------------------------------
echo [5/5] Starting Web Application...
echo ======================================================================
echo  Application is starting!
echo  URL: http://localhost:5000
echo.
echo  Default Admin Login:
echo  - Username: admin
echo  - Password: admin123
echo ======================================================================
echo.

rem Open default browser after a brief delay
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:5000"

python app.py

pause
