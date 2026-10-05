# ==============================================================================
# Student Attendance Management System - Automated Setup & Run Script (PowerShell)
# ==============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

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
# 1. Check Python
# ------------------------------------------------------------------------------
Write-Step "Checking Python 3 environment..."
$PythonCmd = $null

if (Get-Command "python" -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command "py" -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
}

if (-not $PythonCmd) {
    Write-Warn "Python was not found in PATH."
    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        Write-Host "[*] Installing Python 3.12 via winget..." -ForegroundColor Gray
        winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
        $PythonCmd = "python"
    } else {
        Write-Error "Please install Python 3 from https://www.python.org/downloads/ and ensure 'Add Python to PATH' is checked."
    }
}

$PyVersion = & $PythonCmd --version
Write-Success "Found $PyVersion"

# ------------------------------------------------------------------------------
# 2. Check & Start MySQL Service
# ------------------------------------------------------------------------------
Write-Step "Checking MySQL / MariaDB Server & Services..."

$MySQLInstalled = (Get-Command "mysql" -ErrorAction SilentlyContinue) -ne $null
if (-not $MySQLInstalled) {
    Write-Warn "MySQL CLI not found in PATH. Checking Windows Services..."
}

# Check common MySQL services
$Services = @("MySQL", "MySQL80", "MySQL84", "MariaDB")
$FoundService = $false

foreach ($svc in $Services) {
    $status = Get-Service -Name $svc -ErrorAction SilentlyContinue
    if ($status) {
        $FoundService = $true
        if ($status.Status -ne 'Running') {
            Write-Host "[*] Starting service $svc..." -ForegroundColor Gray
            Start-Service -Name $svc -ErrorAction SilentlyContinue
        }
        Write-Success "Service $($status.Name) is running."
        break
    }
}

if (-not $FoundService -and -not $MySQLInstalled) {
    if (Get-Command "winget" -ErrorAction SilentlyContinue) {
        Write-Host "[*] Installing MariaDB Server via winget (MySQL compatible)..." -ForegroundColor Gray
        winget install --id MariaDB.Server -e --accept-package-agreements --accept-source-agreements
    } else {
        Write-Warn "If running XAMPP, please start the MySQL module. Or install MySQL from https://dev.mysql.com/downloads/"
    }
}

# ------------------------------------------------------------------------------
# 3. Setup Virtual Environment
# ------------------------------------------------------------------------------
Write-Step "Setting up Python Virtual Environment..."

if (-not (Test-Path "venv")) {
    Write-Host "[*] Creating virtual environment (./venv)..." -ForegroundColor Gray
    & $PythonCmd -m venv venv
}

$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Error "Virtual environment creation failed at $VenvPython"
}

Write-Success "Virtual environment is ready."

Write-Host "[*] Installing dependencies from requirements.txt..." -ForegroundColor Gray
& $VenvPython -m pip install --upgrade pip -q
& $VenvPython -m pip install -r requirements.txt -q
Write-Success "All requirements installed."

# ------------------------------------------------------------------------------
# 4. Database Setup & Seeding
# ------------------------------------------------------------------------------
Write-Step "Configuring Database & Running Migrations..."
& $VenvPython setup_db.py

# ------------------------------------------------------------------------------
# 5. Launch Web Application
# ------------------------------------------------------------------------------
Write-Step "Launching Web Application..."
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
