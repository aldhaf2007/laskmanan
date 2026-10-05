import os
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash
from config import Config

def get_db_connection(use_database=True):
    """Establish and return a connection to MySQL, supporting both Unix socket and TCP."""
    base_params = {
        'user': Config.MYSQL_USER,
        'password': Config.MYSQL_PASSWORD,
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': True,
        'charset': 'utf8mb4'
    }
    
    if use_database:
        base_params['database'] = Config.MYSQL_DB

    # Strategy 1: If unix socket is configured and exists on filesystem, attempt it
    if Config.MYSQL_UNIX_SOCKET and os.path.exists(Config.MYSQL_UNIX_SOCKET):
        try:
            return pymysql.connect(unix_socket=Config.MYSQL_UNIX_SOCKET, **base_params)
        except Exception:
            pass  # Fall back to TCP

    # Strategy 2: Standard TCP connection (Windows default & standard remote/local)
    try:
        return pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            **base_params
        )
    except Exception as e:
        # If localhost failed, also try 127.0.0.1 explicitly
        if Config.MYSQL_HOST == 'localhost':
            try:
                return pymysql.connect(
                    host='127.0.0.1',
                    port=Config.MYSQL_PORT,
                    **base_params
                )
            except Exception:
                pass
        raise e

def query_db(query, args=(), one=False):
    """Execute a query and fetch results as dictionaries."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            rv = cursor.fetchall()
            return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()

def execute_db(query, args=()):
    """Execute an INSERT, UPDATE, or DELETE query and return affected rows and lastrowid."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(query, args)
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()

def execute_many(query, seq_of_args):
    """Execute a query across a sequence of parameters."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.executemany(query, seq_of_args)
            conn.commit()
            return cursor.rowcount
    finally:
        conn.close()

def init_db():
    """Initialize database tables and seed initial records if needed."""
    # 1. Connect without database to ensure database exists
    conn = get_db_connection(use_database=False)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    finally:
        conn.close()
        
    # 2. Execute schema.sql on the database
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if os.path.exists(schema_path):
        conn = get_db_connection(use_database=True)
        try:
            with open(schema_path, 'r') as f:
                sql_content = f.read()
            
            # Split commands by semicolon while respecting comments
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            with conn.cursor() as cursor:
                for statement in statements:
                    # Ignore USE database since we're already connected to it
                    if statement.upper().startswith('USE '):
                        continue
                    cursor.execute(statement)
        finally:
            conn.close()
            
    # 3. Seed default admin if none exists
    admin_count = query_db("SELECT COUNT(*) as count FROM admins", one=True)['count']
    if admin_count == 0:
        default_password = generate_password_hash('admin123')
        execute_db(
            "INSERT INTO admins (username, password_hash, full_name, email) VALUES (%s, %s, %s, %s)",
            ('admin', default_password, 'System Administrator', 'admin@institution.edu')
        )
        print("Seeded default admin user: admin / admin123")
        
    # 4. Seed initial sample data if students and faculty are empty
    student_count = query_db("SELECT COUNT(*) as count FROM students", one=True)['count']
    if student_count == 0:
        sample_students = [
            ('CSE2024001', 'Aarav Sharma', 'CSE-A', '+91 9876543210'),
            ('CSE2024002', 'Ananya Patel', 'CSE-A', '+91 9876543211'),
            ('CSE2024003', 'Rohan Verma', 'CSE-A', '+91 9876543212'),
            ('CSE2024004', 'Diya Iyer', 'CSE-A', '+91 9876543213'),
            ('CSE2024005', 'Vikram Singh', 'CSE-A', '+91 9876543214'),
            ('ECE2024001', 'Kavya Nair', 'ECE-B', '+91 9876543215'),
            ('ECE2024002', 'Arjun Reddy', 'ECE-B', '+91 9876543216'),
            ('ECE2024003', 'Sneha Kulkarni', 'ECE-B', '+91 9876543217'),
            ('ME2024001', 'Rahul Deshmukh', 'MECH-A', '+91 9876543218'),
            ('ME2024002', 'Pooja Choudhary', 'MECH-A', '+91 9876543219'),
        ]
        execute_many(
            "INSERT INTO students (roll_number, name, class_name, contact) VALUES (%s, %s, %s, %s)",
            sample_students
        )
        print("Seeded sample students.")
        
    faculty_count = query_db("SELECT COUNT(*) as count FROM faculty", one=True)['count']
    if faculty_count == 0:
        sample_faculty = [
            ('FAC001', 'Dr. Ramesh Kumar', 'Computer Science', 'Data Structures & Algorithms', 'ramesh.k@institution.edu', '+91 9123456780'),
            ('FAC002', 'Prof. Priya Sundaram', 'Computer Science', 'Database Management Systems', 'priya.s@institution.edu', '+91 9123456781'),
            ('FAC003', 'Dr. Suresh Menon', 'Electronics & Comm.', 'Digital Signal Processing', 'suresh.m@institution.edu', '+91 9123456782'),
            ('FAC004', 'Prof. Meera Joshi', 'Mechanical Engg.', 'Thermodynamics', 'meera.j@institution.edu', '+91 9123456783'),
        ]
        execute_many(
            "INSERT INTO faculty (faculty_id, name, department, subject, email, phone) VALUES (%s, %s, %s, %s, %s, %s)",
            sample_faculty
        )
        print("Seeded sample faculty.")

    # 5. Seed initial attendance records if empty
    attendance_count = query_db("SELECT COUNT(*) as count FROM attendance", one=True)['count']
    if attendance_count == 0:
        students = query_db("SELECT id, roll_number, class_name FROM students WHERE class_name = 'CSE-A'")
        if students:
            # Let's seed 3 past dates for testing reports & calculations
            import datetime
            today = datetime.date.today()
            dates = [
                today - datetime.timedelta(days=2),
                today - datetime.timedelta(days=1),
                today
            ]
            sample_att = []
            for dt in dates:
                for idx, s in enumerate(students):
                    # Student 4 and 5 have low attendance to test monitoring alert
                    if s['roll_number'] in ('CSE2024004', 'CSE2024005') and dt != dates[0]:
                        status = 'Absent'
                    else:
                        status = 'Present'
                    sample_att.append((s['id'], dt.isoformat(), 'CSE-A', 'Data Structures & Algorithms', status, 'Dr. Ramesh Kumar'))
            execute_many(
                """INSERT INTO attendance (student_id, date, class_name, subject, status, marked_by)
                   VALUES (%s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE status = VALUES(status), marked_by = VALUES(marked_by)""",
                sample_att
            )
            print("Seeded initial sample attendance records.")

if __name__ == '__main__':
    print("Initializing Student Attendance Database...")
    init_db()
    print("Database initialization complete!")
