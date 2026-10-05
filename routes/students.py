from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from routes.auth import login_required
from db import query_db, execute_db

students_bp = Blueprint('students', __name__)

@students_bp.route('/students')
@login_required
def index():
    search = request.args.get('search', '').strip()
    class_filter = request.args.get('class_name', '').strip()
    
    query = "SELECT * FROM students WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE %s OR roll_number LIKE %s OR contact LIKE %s)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern])
        
    if class_filter:
        query += " AND class_name = %s"
        params.append(class_filter)
        
    query += " ORDER BY class_name ASC, roll_number ASC"
    students = query_db(query, tuple(params))
    
    # Get distinct classes for filter dropdown
    classes = query_db("SELECT DISTINCT class_name FROM students ORDER BY class_name ASC")
    class_list = [c['class_name'] for c in classes]
    
    return render_template(
        'students.html',
        students=students,
        classes=class_list,
        search=search,
        selected_class=class_filter
    )

@students_bp.route('/students/add', methods=['POST'])
@login_required
def add():
    roll_number = request.form.get('roll_number', '').strip()
    name = request.form.get('name', '').strip()
    class_name = request.form.get('class_name', '').strip()
    contact = request.form.get('contact', '').strip()
    
    if not roll_number or not name or not class_name or not contact:
        flash('All fields (Roll Number, Name, Class, Contact) are required.', 'danger')
        return redirect(url_for('students.index'))
        
    # Check if roll_number already exists
    existing = query_db("SELECT id FROM students WHERE roll_number = %s", (roll_number,), one=True)
    if existing:
        flash(f"Student with Roll Number '{roll_number}' already exists!", 'danger')
        return redirect(url_for('students.index'))
        
    try:
        execute_db(
            "INSERT INTO students (roll_number, name, class_name, contact) VALUES (%s, %s, %s, %s)",
            (roll_number, name, class_name, contact)
        )
        flash(f"Student '{name}' ({roll_number}) added successfully.", 'success')
    except Exception as e:
        flash(f"Error adding student: {str(e)}", 'danger')
        
    return redirect(url_for('students.index'))

@students_bp.route('/students/edit/<int:student_id>', methods=['POST'])
@login_required
def edit(student_id):
    roll_number = request.form.get('roll_number', '').strip()
    name = request.form.get('name', '').strip()
    class_name = request.form.get('class_name', '').strip()
    contact = request.form.get('contact', '').strip()
    
    if not roll_number or not name or not class_name or not contact:
        flash('All fields are required.', 'danger')
        return redirect(url_for('students.index'))
        
    # Check unique roll number if changed
    existing = query_db("SELECT id FROM students WHERE roll_number = %s AND id != %s", (roll_number, student_id), one=True)
    if existing:
        flash(f"Roll Number '{roll_number}' is already assigned to another student.", 'danger')
        return redirect(url_for('students.index'))
        
    try:
        execute_db(
            "UPDATE students SET roll_number = %s, name = %s, class_name = %s, contact = %s WHERE id = %s",
            (roll_number, name, class_name, contact, student_id)
        )
        flash(f"Student '{name}' updated successfully.", 'success')
    except Exception as e:
        flash(f"Error updating student: {str(e)}", 'danger')
        
    return redirect(url_for('students.index'))

@students_bp.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
def delete(student_id):
    student = query_db("SELECT name, roll_number FROM students WHERE id = %s", (student_id,), one=True)
    if not student:
        flash("Student not found.", 'danger')
        return redirect(url_for('students.index'))
        
    try:
        execute_db("DELETE FROM students WHERE id = %s", (student_id,))
        flash(f"Student '{student['name']}' ({student['roll_number']}) deleted successfully.", 'info')
    except Exception as e:
        flash(f"Error deleting student: {str(e)}", 'danger')
        
    return redirect(url_for('students.index'))

@students_bp.route('/api/students-by-class')
@login_required
def api_students_by_class():
    class_name = request.args.get('class_name', '').strip()
    if not class_name:
        return jsonify([])
    students = query_db("SELECT id, roll_number, name, class_name FROM students WHERE class_name = %s ORDER BY roll_number ASC", (class_name,))
    return jsonify(students)
