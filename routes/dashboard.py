import datetime
from flask import Blueprint, render_template
from routes.auth import login_required
from db import query_db

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # 1. Total counts
    student_count = query_db("SELECT COUNT(*) as count FROM students", one=True)['count']
    faculty_count = query_db("SELECT COUNT(*) as count FROM faculty", one=True)['count']
    classes_count = query_db("SELECT COUNT(DISTINCT class_name) as count FROM students", one=True)['count']
    
    # 2. Today's attendance
    today = datetime.date.today().isoformat()
    today_stats = query_db("""
        SELECT 
            COUNT(*) as total_marked,
            SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count,
            SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent_count
        FROM attendance 
        WHERE date = %s
    """, (today,), one=True)
    
    total_marked = today_stats['total_marked'] or 0
    present_count = today_stats['present_count'] or 0
    absent_count = today_stats['absent_count'] or 0
    today_rate = round((present_count / total_marked * 100), 1) if total_marked > 0 else 0
    
    # 3. Low attendance calculation (overall < 75% for students with at least 1 record)
    student_rates = query_db("""
        SELECT 
            s.id, s.roll_number, s.name, s.class_name,
            COUNT(a.id) as total_sessions,
            SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as attended,
            ROUND(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.id) * 100, 1) as percentage
        FROM students s
        INNER JOIN attendance a ON s.id = a.student_id
        GROUP BY s.id, s.roll_number, s.name, s.class_name
        HAVING percentage < 75.0
        ORDER BY percentage ASC
        LIMIT 5
    """)
    low_attendance_count = query_db("""
        SELECT COUNT(*) as count FROM (
            SELECT s.id,
                   ROUND(SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) / COUNT(a.id) * 100, 1) as percentage
            FROM students s
            INNER JOIN attendance a ON s.id = a.student_id
            GROUP BY s.id
            HAVING percentage < 75.0
        ) as low_att
    """, one=True)['count']
    
    # 4. Recent attendance sessions
    recent_logs = query_db("""
        SELECT date, class_name, subject, marked_by,
               COUNT(*) as total_students,
               SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present_count
        FROM attendance
        GROUP BY date, class_name, subject, marked_by
        ORDER BY date DESC, MAX(id) DESC
        LIMIT 5
    """)
    
    return render_template(
        'dashboard.html',
        student_count=student_count,
        faculty_count=faculty_count,
        classes_count=classes_count,
        today=today,
        total_marked=total_marked,
        present_count=present_count,
        absent_count=absent_count,
        today_rate=today_rate,
        low_attendance_count=low_attendance_count,
        low_attendance_students=student_rates,
        recent_logs=recent_logs
    )
