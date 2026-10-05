import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from routes.auth import login_required
from db import query_db, execute_many

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance')
@login_required
def index():
    selected_class = request.args.get('class_name', '').strip()
    selected_subject = request.args.get('subject', '').strip()
    selected_date = request.args.get('date', '').strip()
    
    if not selected_date:
        selected_date = datetime.date.today().isoformat()
        
    # Get available classes
    classes = query_db("SELECT DISTINCT class_name FROM students ORDER BY class_name ASC")
    class_list = [c['class_name'] for c in classes]
    
    # Get available subjects from faculty and past attendance
    subjects_db = query_db("""
        SELECT DISTINCT subject FROM (
            SELECT subject FROM faculty WHERE subject IS NOT NULL AND subject != ''
            UNION
            SELECT subject FROM attendance WHERE subject IS NOT NULL AND subject != ''
        ) as sub ORDER BY subject ASC
    """)
    subject_list = [s['subject'] for s in subjects_db]
    
    # If no subject is chosen yet, choose the first available subject
    if not selected_subject and subject_list:
        selected_subject = subject_list[0]
        
    students = []
    already_marked = False
    
    if selected_class:
        # Fetch all students in the class
        students = query_db("""
            SELECT id, roll_number, name, class_name 
            FROM students 
            WHERE class_name = %s 
            ORDER BY roll_number ASC
        """, (selected_class,))
        
        # Check existing attendance for this class, subject, date
        existing_records = query_db("""
            SELECT student_id, status 
            FROM attendance 
            WHERE class_name = %s AND subject = %s AND date = %s
        """, (selected_class, selected_subject, selected_date))
        
        status_map = {r['student_id']: r['status'] for r in existing_records}
        if existing_records:
            already_marked = True
            
        for s in students:
            # If already marked, use that status; otherwise default to 'Present'
            s['status'] = status_map.get(s['id'], 'Present')
            s['is_existing'] = s['id'] in status_map
            
    return render_template(
        'attendance.html',
        classes=class_list,
        subjects=subject_list,
        selected_class=selected_class,
        selected_subject=selected_subject,
        selected_date=selected_date,
        students=students,
        already_marked=already_marked,
        today=datetime.date.today().isoformat()
    )

@attendance_bp.route('/attendance/save', methods=['POST'])
@login_required
def save():
    class_name = request.form.get('class_name', '').strip()
    subject = request.form.get('subject', '').strip()
    date = request.form.get('date', '').strip()
    marked_by = session.get('admin_name', 'Admin')
    
    if not class_name or not subject or not date:
        flash('Class, Subject, and Date are required to save attendance.', 'danger')
        return redirect(url_for('attendance.index'))
        
    # Find all students for this class
    students = query_db("SELECT id FROM students WHERE class_name = %s", (class_name,))
    if not students:
        flash(f"No students found in class '{class_name}'.", 'warning')
        return redirect(url_for('attendance.index', class_name=class_name, subject=subject, date=date))
        
    records_to_save = []
    for s in students:
        s_id = s['id']
        field_name = f"status_{s_id}"
        # Value should be 'Present' or 'Absent'
        status = request.form.get(field_name, 'Absent')
        if status not in ('Present', 'Absent'):
            status = 'Absent'
        records_to_save.append((s_id, date, class_name, subject, status, marked_by))
        
    if records_to_save:
        query = """
            INSERT INTO attendance (student_id, date, class_name, subject, status, marked_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                status = VALUES(status), 
                marked_by = VALUES(marked_by),
                updated_at = CURRENT_TIMESTAMP
        """
        try:
            execute_many(query, records_to_save)
            flash(f"Attendance for {class_name} ({subject}) on {date} recorded/updated successfully ({len(records_to_save)} students).", 'success')
        except Exception as e:
            flash(f"Error saving attendance: {str(e)}", 'danger')
            
    return redirect(url_for('attendance.index', class_name=class_name, subject=subject, date=date))
