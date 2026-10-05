#!/usr/bin/env python3
"""
Cross-Platform Database Setup & Diagnostic Tool
Tests MySQL connectivity, creates student_attendance_db if missing,
executes schema.sql, and seeds default admin and demo records.
"""

import sys
import os
import pymysql
from config import Config

def test_and_setup_db():
    print("=" * 60)
    print("  Student Attendance System - Database Setup & Verification")
    print("=" * 60)
    print(f"Target Database : {Config.MYSQL_DB}")
    print(f"Target Host     : {Config.MYSQL_HOST}:{Config.MYSQL_PORT}")
    print(f"Target User     : {Config.MYSQL_USER}")
    if Config.MYSQL_UNIX_SOCKET:
        print(f"Unix Socket     : {Config.MYSQL_UNIX_SOCKET}")
    print("-" * 60)

    try:
        from db import get_db_connection, init_db, query_db
    except ImportError as e:
        print(f"[!] Error importing project modules: {e}")
        print("[!] Please make sure requirements are installed: pip install -r requirements.txt")
        sys.exit(1)

    # 1. Test basic server connection (without database selected)
    print("[*] Probing MySQL server connection...")
    try:
        conn = get_db_connection(use_database=False)
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION();")
            ver = cur.fetchone()
            version_str = list(ver.values())[0] if isinstance(ver, dict) else ver[0]
            print(f"[+] Successfully connected to MySQL Server (Version: {version_str})")
        conn.close()
    except pymysql.err.OperationalError as e:
        code, msg = e.args
        print(f"[!] Unable to connect to MySQL Server (Error {code}: {msg})")
        print("-" * 60)
        print("TROUBLESHOOTING GUIDE:")
        if os.name == 'nt':
            print("  Windows:")
            print("  1. Ensure MySQL / MariaDB service is running:")
            print("     Open Command Prompt as Administrator and run: net start MySQL")
            print("     Or: net start MariaDB")
            print("  2. If MySQL is not installed, install it with:")
            print("     winget install Oracle.MySQL   OR   winget install MariaDB.Server")
            print("  3. Verify root password in your .env file:")
            print("     MYSQL_PASSWORD=your_password")
        else:
            print("  Linux:")
            print("  1. Ensure MySQL / MariaDB daemon is running:")
            print("     sudo systemctl start mysql   OR   sudo systemctl start mariadb")
            print("  2. If MySQL is not installed, install it with:")
            print("     Ubuntu/Debian: sudo apt update && sudo apt install -y mysql-server")
            print("     Fedora/RHEL:   sudo dnf install -y mariadb-server && sudo systemctl start mariadb")
            print("  3. Check socket permissions or update credentials in .env")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print(f"[!] Unexpected connection error: {e}")
        sys.exit(1)

    # 2. Run init_db to ensure database, tables, and seeds are created
    print("[*] Setting up database schema and seeding records...")
    try:
        init_db()
        print("[+] Schema and tables verified.")
    except Exception as e:
        print(f"[!] Error during database schema initialization: {e}")
        sys.exit(1)

    # 3. Verify table counts
    try:
        admins = query_db("SELECT COUNT(*) as c FROM admins", one=True)['c']
        students = query_db("SELECT COUNT(*) as c FROM students", one=True)['c']
        faculty = query_db("SELECT COUNT(*) as c FROM faculty", one=True)['c']
        attendance = query_db("SELECT COUNT(*) as c FROM attendance", one=True)['c']

        print("-" * 60)
        print("DATABASE STATUS SUMMARY:")
        print(f"  • Registered Admins   : {admins}")
        print(f"  • Enrolled Students   : {students}")
        print(f"  • Faculty Members     : {faculty}")
        print(f"  • Attendance Records  : {attendance}")
        print("-" * 60)
        print("[✓] Default Admin Account: Username: admin | Password: admin123")
        print("[✓] Database is ready for application launch!")
        print("=" * 60)
    except Exception as e:
        print(f"[!] Verification warning: {e}")

if __name__ == '__main__':
    test_and_setup_db()
