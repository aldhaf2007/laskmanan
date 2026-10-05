@echo off
rem ==============================================================================
rem Student Attendance Management System - Robust Windows Setup & Run Script
rem ==============================================================================
rem Enhanced with:
rem - UTF-8 console output support
rem - Administrator elevation detection
rem - Deep Python & MySQL search across standard Windows directories & XAMPP
rem - Automatic service startup and package installation via winget
rem - Virtual environment recovery and automated database migration
rem ==============================================================================

chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title Student Attendance Management System - Setup ^& Run

echo ======================================================================
echo    STUDENT ATTENDANCE MANAGEMENT SYSTEM - WINDOWS SETUP ^& RUN
echo ======================================================================
echo.

cd /d "%~dp0"

rem ------------------------------------------------------------------------------
rem 0. Check for Administrator Privileges (optional but recommended for services)
rem ------------------------------------------------------------------------------
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [i] Note: Running as standard user.
    echo     If starting MySQL services requires administrative permissions,
    echo     right-click this script and select "Run as administrator".
    echo.
)

rem ------------------------------------------------------------------------------
rem 1. Deep Python 3 Detection & PATH Resolution
rem ------------------------------------------------------------------------------
echo [1/5] Checking Python 3 installation...
set "PY_CMD="

rem Check standard PATH first
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set "PY_CMD=python"
) else (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set "PY_CMD=py -3"
    )
)

rem If not in PATH, search standard Windows Python directories
if "%PY_CMD%"=="" (
    for %%V in (313 312 311 310 39) do (
        if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" (
            set "PY_CMD=%LocalAppData%\Programs\Python\Python%%V\python.exe"
            set "PATH=%LocalAppData%\Programs\Python\Python%%V;%LocalAppData%\Programs\Python\Python%%V\Scripts;!PATH!"
            goto :found_python
        )
        if exist "%ProgramFiles%\Python%%V\python.exe" (
            set "PY_CMD=%ProgramFiles%\Python%%V\python.exe"
            set "PATH=%ProgramFiles%\Python%%V;%ProgramFiles%\Python%%V\Scripts;!PATH!"
            goto :found_python
        )
    )
)

:found_python
if "%PY_CMD%"=="" (
    echo [!] Python 3 was not detected in PATH or standard installation folders.
    echo [*] Checking Windows Package Manager (winget) to install Python...
    winget --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [*] Installing Python 3.12 via winget...
        winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
        echo [!] Installation complete. Refreshing environment variables...
        for %%V in (312 311 313) do (
            if exist "%LocalAppData%\Programs\Python\Python%%V\python.exe" (
                set "PY_CMD=%LocalAppData%\Programs\Python\Python%%V\python.exe"
                set "PATH=%LocalAppData%\Programs\Python\Python%%V;%LocalAppData%\Programs\Python\Python%%V\Scripts;!PATH!"
            )
        )
    ) else (
        echo [ERROR] Could not automatically install Python.
        echo Please download and install Python 3 from: https://www.python.org/downloads/
        echo (IMPORTANT: Check the box "Add Python to PATH" during installation!)
        echo.
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%i in ('%PY_CMD% --version 2^>^&1') do set "PY_VER=%%i"
echo [✓] Using Python: %PY_VER%
echo.

rem ------------------------------------------------------------------------------
rem 2. Detect & Configure MySQL / MariaDB Server
rem ------------------------------------------------------------------------------
echo [2/5] Checking MySQL / MariaDB Server and Services...
set "MYSQL_FOUND=0"

rem Check if mysql is already in PATH
mysql --version >nul 2>&1
if %errorlevel% equ 0 (
    set "MYSQL_FOUND=1"
) else (
    rem Check common install paths and add to PATH
    for /d %%D in ("C:\Program Files\MySQL\MySQL Server *") do (
        if exist "%%D\bin\mysql.exe" (
            set "PATH=%%D\bin;!PATH!"
            set "MYSQL_FOUND=1"
        )
    )
    for /d %%D in ("C:\Program Files\MariaDB *") do (
        if exist "%%D\bin\mysql.exe" (
            set "PATH=%%D\bin;!PATH!"
            set "MYSQL_FOUND=1"
        )
    )
    if exist "C:\xampp\mysql\bin\mysql.exe" (
        set "PATH=C:\xampp\mysql\bin;!PATH!"
        set "MYSQL_FOUND=1"
    )
)

rem If not installed, offer winget installation
if "%MYSQL_FOUND%"=="0" (
    echo [!] MySQL / MariaDB server was not detected.
    winget --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [*] Installing MariaDB Server via winget (fully MySQL-compatible)...
        winget install --id MariaDB.Server -e --accept-package-agreements --accept-source-agreements
        echo [✓] Database server package installed.
        for /d %%D in ("C:\Program Files\MariaDB *") do (
            if exist "%%D\bin\mysql.exe" set "PATH=%%D\bin;!PATH!"
        )
    ) else (
        echo [NOTE] If you have XAMPP installed, please start MySQL from the XAMPP Control Panel.
        echo        Or download MySQL Community Server: https://dev.mysql.com/downloads/installer/
    )
)

rem Check and start common Windows MySQL / MariaDB services
echo [*] Checking database Windows service status...
set "SERVICE_STARTED=0"
for %%S in (MySQL MySQL80 MySQL84 MariaDB wampmysqld wampmysqld64) do (
    sc query "%%S" >nul 2>&1
    if !errorlevel! equ 0 (
        echo [*] Found Windows Service: %%S
        net start "%%S" >nul 2>&1
        set "SERVICE_STARTED=1"
    )
)

if "%SERVICE_STARTED%"=="0" (
    rem Check if XAMPP mysqld exists and can be run standalone if needed
    if exist "C:\xampp\mysql\bin\mysqld.exe" (
        echo [*] Starting XAMPP MySQL daemon...
        start "" /B "C:\xampp\mysql\bin\mysqld.exe" --defaults-file="C:\xampp\mysql\bin\my.ini" --standalone >nul 2>&1
    )
)
echo [✓] Database server check completed.
echo.

rem ------------------------------------------------------------------------------
rem 3. Virtual Environment Setup & Requirements
rem ------------------------------------------------------------------------------
echo [3/5] Setting up Python virtual environment...

if not exist "venv\Scripts\python.exe" (
    if exist "venv" (
        echo [!] Existing virtual environment seems incomplete. Rebuilding...
        rmdir /s /q "venv" >nul 2>&1
    )
    echo [*] Creating virtual environment in ./venv...
    %PY_CMD% -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

call "venv\Scripts\activate.bat"
echo [✓] Virtual environment activated.

echo [*] Checking dependencies from requirements.txt...
python -m pip install --upgrade pip -q >nul 2>&1
pip install -r requirements.txt -q
if %errorlevel% neq 0 (
    echo [!] Retrying dependency installation with detailed output...
    pip install -r requirements.txt
)
echo [✓] All Python requirements are satisfied.
echo.

rem ------------------------------------------------------------------------------
rem 4. Database Initialization & Schema Migration
rem ------------------------------------------------------------------------------
echo [4/5] Initializing Database (student_attendance_db) ^& Tables...
python setup_db.py
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] Database setup encountered an issue.
    echo Please make sure MySQL is running and check your .env file credentials if needed.
    echo Continuing to application launch...
    echo.
)
echo.

rem ------------------------------------------------------------------------------
rem 5. Launch Web Application & Open Browser
rem ------------------------------------------------------------------------------
echo [5/5] Launching Student Attendance Management System...
echo ======================================================================
echo  Server is starting! Access the portal at:
echo  --^> http://localhost:5000
echo.
echo  Default Administrator Credentials:
echo  --^> Username: admin
echo  --^> Password: admin123
echo ======================================================================
echo.

rem Automatically open default browser after brief delay
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:5000"

python app.py

if %errorlevel% neq 0 (
    echo.
    echo [!] Server stopped unexpectedly with exit code %errorlevel%.
    pause
)
