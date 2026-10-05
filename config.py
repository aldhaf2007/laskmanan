import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'attendance-secret-key-super-secure-2026')
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'student_attendance_db')
    
    # Cross-platform socket detection:
    # On Windows (os.name == 'nt'), unix sockets do not exist, so default to None (connects via TCP).
    # On Linux, inspect standard socket paths.
    default_socket = None
    if os.name != 'nt':
        common_sockets = [
            '/var/lib/mysql/mysql.sock',
            '/run/mysqld/mysqld.sock',
            '/tmp/mysql.sock',
            '/var/run/mysqld/mysqld.sock'
        ]
        for s in common_sockets:
            if os.path.exists(s):
                default_socket = s
                break

    MYSQL_UNIX_SOCKET = os.getenv('MYSQL_UNIX_SOCKET', default_socket)
