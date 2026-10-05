import csv
import io
import datetime
from flask import Blueprint, render_template, request, Response
from routes.auth import login_required
from db import query_db

reports_bp = Blueprint('reports', __name__)

def fetch_report_data(class_name='', subject='', student_id='', start_date='', end_date='', low_only=False):
    """Query and calculate attendance statistics based on filters."""
    query = """
        SELECT 
            s.id as student_id,
            s.roll_number,
            s.name as student_name,
            s.class_name,
            s.contact,
            COUNT(a.id) as total_classes,
            SUM(CASE WHEN a.status = 'Present' THEN 1 ELSE 0 END) as present_classes,
            SUM(CASE WHEN a.status = 'Absent' THEN 1 ELSE 0 END) as absent_classes
        FROM students s
        LEFT JOIN attendance a ON s.id = a.student_id
        WHERE 1=1
    """
    params = []
    
    if class_name:
        query += " AND s.class_name = %s"
        params.append(class_name)
        
    if student_id:
        query += " AND s.id = %s"
        params.append(student_id)
        
    if subject:
        # If subject is selected, filter attendance by subject
        query += " AND (a.subject = %s OR a.subject IS NULL)"
        params.append(subject)
        
    if start_date:
        query += " AND (a.date >= %s OR a.date IS NULL)"
        params.append(start_date)
        
    if end_date:
        query += " AND (a.date <= %s OR a.date IS NULL)"
        params.append(end_date)
        
    query += " GROUP BY s.id, s.roll_number, s.name, s.class_name, s.contact"
    query += " ORDER BY s.class_name ASC, s.roll_number ASC"
    
    rows = query_db(query, tuple(params))
    
    report_rows = []
    for r in rows:
        total = r['total_classes'] or 0
        present = r['present_classes'] or 0
        absent = r['absent_classes'] or 0
        
        percentage = round((present / total * 100), 1) if total > 0 else 0.0
        is_low = (total > 0 and percentage < 75.0)
        
        item = {
            'student_id': r['student_id'],
            'roll_number': r['roll_number'],
            'name': r['student_name'],
            'class_name': r['class_name'],
            'contact': r['contact'],
            'total_classes': total,
            'present_classes': present,
            'absent_classes': absent,
            'percentage': percentage,
            'is_low': is_low
        }
        
        if low_only:
            if is_low:
                report_rows.append(item)
        else:
            report_rows.append(item)
            
    return report_rows

@reports_bp.route('/reports')
@login_required
def index():
    class_name = request.args.get('class_name', '').strip()
    subject = request.args.get('subject', '').strip()
    student_id = request.args.get('student_id', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    low_only = request.args.get('low_only') == '1'
    
    # Filter dropdown choices
    classes = query_db("SELECT DISTINCT class_name FROM students ORDER BY class_name ASC")
    class_list = [c['class_name'] for c in classes]
    
    subjects = query_db("""
        SELECT DISTINCT subject FROM (
            SELECT subject FROM faculty WHERE subject IS NOT NULL AND subject != ''
            UNION
            SELECT subject FROM attendance WHERE subject IS NOT NULL AND subject != ''
        ) as sub ORDER BY subject ASC
    """)
    subject_list = [s['subject'] for s in subjects]
    
    students = query_db("SELECT id, roll_number, name, class_name FROM students ORDER BY class_name ASC, roll_number ASC")
    
    # Fetch report records
    records = fetch_report_data(class_name, subject, student_id, start_date, end_date, low_only)
    
    # Calculate overall summary metrics
    total_evaluated = len(records)
    total_present_sum = sum(r['present_classes'] for r in records)
    total_classes_sum = sum(r['total_classes'] for r in records)
    overall_percentage = round((total_present_sum / total_classes_sum * 100), 1) if total_classes_sum > 0 else 0.0
    low_attendance_count = sum(1 for r in records if r['is_low'])
    
    return render_template(
        'reports.html',
        classes=class_list,
        subjects=subject_list,
        students=students,
        records=records,
        selected_class=class_name,
        selected_subject=subject,
        selected_student=student_id,
        start_date=start_date,
        end_date=end_date,
        low_only=low_only,
        total_evaluated=total_evaluated,
        overall_percentage=overall_percentage,
        low_attendance_count=low_attendance_count
    )

@reports_bp.route('/reports/export')
@login_required
def export_csv():
    class_name = request.args.get('class_name', '').strip()
    subject = request.args.get('subject', '').strip()
    student_id = request.args.get('student_id', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    low_only = request.args.get('low_only') == '1'
    
    records = fetch_report_data(class_name, subject, student_id, start_date, end_date, low_only)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Roll Number',
        'Student Name',
        'Class',
        'Contact',
        'Subject Filter',
        'Total Classes',
        'Classes Present',
        'Classes Absent',
        'Attendance Percentage (%)',
        'Status / Warning'
    ])
    
    # Rows
    for r in records:
        status_label = "Low Attendance (<75%)" if r['is_low'] else "Good"
        writer.writerow([
            r['roll_number'],
            r['name'],
            r['class_name'],
            r['contact'],
            subject if subject else 'All Subjects',
            r['total_classes'],
            r['present_classes'],
            r['absent_classes'],
            f"{r['percentage']}%",
            status_label
        ])
        
    output.seek(0)
    filename = f"attendance_report_{datetime.date.today().isoformat()}.csv"
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
