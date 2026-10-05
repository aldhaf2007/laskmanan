#!/usr/bin/env bash
# ==============================================================================
# Student Attendance Management System - Automated Setup & Run Script (Linux)
# ==============================================================================
# Automatically checks & installs:
# 1. Python 3 and venv
# 2. MySQL / MariaDB Server (detects apt, dnf, yum, pacman, zypper)
# 3. Python dependencies from requirements.txt
# 4. MySQL Database & Schema (student_attendance_db)
# 5. Launches the web application
# ==============================================================================

set -e

# ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${CYAN}${BOLD}"
echo "======================================================================"
echo "    STUDENT ATTENDANCE MANAGEMENT SYSTEM - ONE-CLICK SETUP & RUN      "
echo "======================================================================"
echo -e "${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ------------------------------------------------------------------------------
# 1. Detect Package Manager
# ------------------------------------------------------------------------------
detect_pkg_manager() {
    if command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v zypper &> /dev/null; then
        echo "zypper"
    else
        echo "unknown"
    fi
}

PKG_MGR=$(detect_pkg_manager)

# Helper function for sudo commands
run_as_root() {
    if [ "$EUID" -eq 0 ]; then
        "$@"
    elif command -v sudo &> /dev/null; then
        sudo "$@"
    else
        echo -e "${RED}[ERROR] Root or sudo privileges required to install system packages.${NC}"
        exit 1
    fi
}

# ------------------------------------------------------------------------------
# 2. Check & Install Python 3 and venv
# ------------------------------------------------------------------------------
echo -e "${BLUE}[1/5] Checking Python 3 environment...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}[!] Python 3 not found. Installing Python 3...${NC}"
    case "$PKG_MGR" in
        apt)
            run_as_root apt-get update
            run_as_root apt-get install -y python3 python3-pip python3-venv
            ;;
        dnf)
            run_as_root dnf install -y python3 python3-pip
            ;;
        yum)
            run_as_root yum install -y python3 python3-pip
            ;;
        pacman)
            run_as_root pacman -Sy --noconfirm python python-pip
            ;;
        zypper)
            run_as_root zypper install -y python3 python3-pip
            ;;
        *)
            echo -e "${RED}[ERROR] Could not detect package manager to install Python 3. Please install Python 3 manually.${NC}"
            exit 1
            ;;
    esac
fi

# Verify python3-venv availability
if ! python3 -c "import venv" &> /dev/null; then
    echo -e "${YELLOW}[!] python3-venv module missing. Installing...${NC}"
    case "$PKG_MGR" in
        apt)
            run_as_root apt-get update
            run_as_root apt-get install -y python3-venv
            ;;
        *)
            echo -e "${YELLOW}[!] Ensure python3-venv or virtualenv package is installed.${NC}"
            ;;
    esac
fi

PYTHON_VER=$(python3 --version)
echo -e "${GREEN}[✓] Found ${PYTHON_VER}${NC}"

# ------------------------------------------------------------------------------
# 3. Check & Install MySQL / MariaDB Server
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[2/5] Checking MySQL / MariaDB Server...${NC}"

is_mysql_installed() {
    command -v mysql &> /dev/null || command -v mysqld &> /dev/null || command -v mariadb &> /dev/null
}

if ! is_mysql_installed; then
    echo -e "${YELLOW}[!] MySQL / MariaDB server not found. Installing database server...${NC}"
    case "$PKG_MGR" in
        apt)
            run_as_root apt-get update
            run_as_root apt-get install -y mysql-server
            ;;
        dnf)
            run_as_root dnf install -y mariadb-server mariadb || run_as_root dnf install -y community-mysql-server
            ;;
        yum)
            run_as_root yum install -y mariadb-server mariadb
            ;;
        pacman)
            run_as_root pacman -Sy --noconfirm mariadb
            run_as_root mariadb-install-db --user=mysql --basedir=/usr --datadir=/var/lib/mysql
            ;;
        zypper)
            run_as_root zypper install -y mariadb mariadb-client
            ;;
        *)
            echo -e "${RED}[ERROR] Could not automatically install MySQL/MariaDB. Please install MySQL Server manually.${NC}"
            exit 1
            ;;
    esac
    echo -e "${GREEN}[✓] MySQL / MariaDB Server installed successfully.${NC}"
fi

# Ensure MySQL Service is running
echo -e "[*] Ensuring database daemon is running..."
start_mysql_service() {
    if command -v systemctl &> /dev/null; then
        for svc in mysql mariadb mysqld; do
            if systemctl list-unit-files | grep -q "^${svc}\.service"; then
                if ! systemctl is-active --quiet "$svc"; then
                    echo -e "${YELLOW}[!] Starting ${svc} service...${NC}"
                    run_as_root systemctl start "$svc"
                    run_as_root systemctl enable "$svc" 2>/dev/null || true
                fi
                echo -e "${GREEN}[✓] Service ${svc} is active.${NC}"
                return 0
            fi
        done
        # Direct attempt if list-unit-files was silent
        run_as_root systemctl start mysql 2>/dev/null || run_as_root systemctl start mariadb 2>/dev/null || true
    elif command -v service &> /dev/null; then
        run_as_root service mysql start 2>/dev/null || run_as_root service mariadb start 2>/dev/null || true
    fi
}
start_mysql_service

# ------------------------------------------------------------------------------
# 4. Setup Python Virtual Environment & Dependencies
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[3/5] Setting up Python virtual environment...${NC}"

if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment in ./venv..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate
echo -e "${GREEN}[✓] Virtual environment activated.$(which python)${NC}"

echo "[*] Installing required Python packages..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "${GREEN}[✓] All Python dependencies installed successfully.${NC}"

# ------------------------------------------------------------------------------
# 5. Initialize MySQL Database & Tables
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[4/5] Initializing Database & Verifying Records...${NC}"
python setup_db.py

# ------------------------------------------------------------------------------
# 6. Launch Application
# ------------------------------------------------------------------------------
echo -e "\n${BLUE}[5/5] Launching Student Attendance Management System...${NC}"
echo -e "${GREEN}${BOLD}"
echo "======================================================================"
echo " Application is starting! Access the portal at:"
echo " -> http://localhost:5000"
echo ""
echo " Default Admin Credentials:"
echo " -> Username: admin"
echo " -> Password: admin123"
echo "======================================================================"
echo -e "${NC}"

# Try to open default browser if in GUI session
if [ -n "$DISPLAY" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    (sleep 2 && (xdg-open http://localhost:5000 2>/dev/null || sensible-browser http://localhost:5000 2>/dev/null || true)) &
fi

exec python app.py
