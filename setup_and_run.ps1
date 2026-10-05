# ==============================================================================
# Student Attendance Management System - Robust PowerShell Setup & Run Script
# ==============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Write-Step {
    param([string]$Message)
    Write-Host "`n[STEP] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[✓] $Message" -ForegroundColor Green
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[!] $Message" -ForegroundColor Yellow
}

Write-Host "======================================================================" -ForegroundColor Magenta
Write-Host "    STUDENT ATTENDANCE MANAGEMENT SYSTEM - POWERSHELL SETUP & RUN    " -ForegroundColor Magenta
Write-Host "======================================================================" -ForegroundColor Magenta

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# ------------------------------------------------------------------------------
# 1. Deep Python 3 Detection
# ------------------------------------------------------------------------------
Write-Step "1/5: Checking Python 3 environment..."
$PythonCmd = $null

if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
}

# If not in PATH, search standard Windows Python directories
if (-not $PythonCmd) {
    $LocalPython = Get-ChildItem -Path "$env:LOCALAPPDATA\Programs\Python" -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($LocalPython) {
        $PythonCmd = $LocalPython.FullName
    } else {
        $GlobalPython = Get-ChildItem -Path "$env:ProgramFiles\Python*" -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($GlobalPython) {
            $PythonCmd = $GlobalPython.FullName
        }
    }
}

if (-not $PythonCmd) {
    Write-Warn "Python 3 was not found in PATH or standard installation directories."
    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        Write-Host "[*] Installing Python 3.12 via Windows Package Manager (winget)..." -ForegroundColor Gray
        winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
        $PythonCmd = "python"
    } else {
        Write-Host "[ERROR] Please install Python 3 from https://www.python.org/downloads/ (check 'Add Python to PATH')" -ForegroundColor Red
        Read-Host "Press Enter to exit..."
        exit 1
    }
}

$PyVersion = & $PythonCmd --version 2>&1
Write-Success "Using Python: $PyVersion"

# ------------------------------------------------------------------------------
# 2. Check & Start MySQL / MariaDB Service
# ------------------------------------------------------------------------------
Write-Step "2/5: Checking MySQL / MariaDB Server & Services..."

$MySQLInstalled = (Get-Command "mysql" -ErrorAction SilentlyContinue) -ne $null
$Services = @("MySQL", "MySQL80", "MySQL84", "MariaDB", "wampmysqld", "wampmysqld64")
$FoundService = $false

foreach ($svc in $Services) {
    $status = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($status) {
        $FoundService = $true
        if ($status.Status -ne 'Running') {
            Write-Host "[*] Starting Windows Service '$svc'..." -ForegroundColor Gray
            Start-Service -Name $svc -ErrorAction SilentlyContinue
        }
        Write-Success "Service '$($status.Name)' is active and running."
        break
    }
}

# Check for XAMPP
if (-not $FoundService -and (Test-Path "C:\xampp\mysql\bin\mysqld.exe")) {
    Write-Host "[*] Starting XAMPP MySQL standalone daemon..." -ForegroundColor Gray
    Start-Process -FilePath "C:\xampp\mysql\bin\mysqld.exe" -ArgumentList "--defaults-file=C:\xampp\mysql\bin\my.ini", "--standalone" -WindowStyle Hidden -ErrorAction SilentlyContinue
    $FoundService = $true
}

# If not installed anywhere, install via winget
if (-not $FoundService -and -not $MySQLInstalled) {
    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        Write-Host "[*] Installing MariaDB Server via winget (MySQL compatible)..." -ForegroundColor Gray
        winget install --id MariaDB.Server -e --accept-package-agreements --accept-source-agreements
        Write-Success "MariaDB package installed."
    } else {
        Write-Warn "If you use XAMPP, please start the MySQL module from XAMPP Control Panel."
    }
}

# ------------------------------------------------------------------------------
# 3. Setup Virtual Environment & Dependencies
# ------------------------------------------------------------------------------
Write-Step "3/5: Setting up Python Virtual Environment..."

$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    if (Test-Path "venv") {
        Remove-Item -Recurse -Force "venv" -ErrorAction SilentlyContinue
    }
    Write-Host "[*] Creating virtual environment in ./venv..." -ForegroundColor Gray
    & $PythonCmd -m venv venv
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "[ERROR] Virtual environment creation failed at $VenvPython" -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Success "Virtual environment is ready."

Write-Host "[*] Checking and updating required dependencies..." -ForegroundColor Gray
& $VenvPython -m pip install --upgrade pip -q 2>$null
& $VenvPython -m pip install -r requirements.txt -q
Write-Success "All requirements installed successfully."

# ------------------------------------------------------------------------------
# 4. Database Setup & Seeding
# ------------------------------------------------------------------------------
Write-Step "4/5: Initializing Database (student_attendance_db) & Running Migrations..."
& $VenvPython setup_db.py

# ------------------------------------------------------------------------------
# 5. Launch Web Application & Open Browser
# ------------------------------------------------------------------------------
Write-Step "5/5: Starting Web Application..."
Write-Host "======================================================================" -ForegroundColor Green
Write-Host " Application starting at: http://localhost:5000" -ForegroundColor Green
Write-Host " Default Admin: admin | Password: admin123" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green

# Open browser in background
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:5000"
} | Out-Null

& $VenvPython app.py
