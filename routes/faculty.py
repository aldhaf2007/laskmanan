from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth import login_required
from db import query_db, execute_db

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/faculty')
@login_required
def index():
    search = request.args.get('search', '').strip()
    dept_filter = request.args.get('department', '').strip()
    
    query = "SELECT * FROM faculty WHERE 1=1"
    params = []
    
    if search:
        query += " AND (name LIKE %s OR faculty_id LIKE %s OR subject LIKE %s OR email LIKE %s)"
        pattern = f"%{search}%"
        params.extend([pattern, pattern, pattern, pattern])
        
    if dept_filter:
        query += " AND department = %s"
        params.append(dept_filter)
        
    query += " ORDER BY department ASC, name ASC"
    faculty_list = query_db(query, tuple(params))
    
    departments = query_db("SELECT DISTINCT department FROM faculty ORDER BY department ASC")
    department_list = [d['department'] for d in departments if d['department']]
    
    return render_template(
        'faculty.html',
        faculty_list=faculty_list,
        departments=department_list,
        search=search,
        selected_dept=dept_filter
    )

@faculty_bp.route('/faculty/add', methods=['POST'])
@login_required
def add():
    faculty_id = request.form.get('faculty_id', '').strip()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    subject = request.form.get('subject', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    
    if not faculty_id or not name or not department or not subject:
        flash('Faculty ID, Name, Department, and Subject are required fields.', 'danger')
        return redirect(url_for('faculty.index'))
        
    existing = query_db("SELECT id FROM faculty WHERE faculty_id = %s", (faculty_id,), one=True)
    if existing:
        flash(f"Faculty member with ID '{faculty_id}' already exists.", 'danger')
        return redirect(url_for('faculty.index'))
        
    try:
        execute_db(
            "INSERT INTO faculty (faculty_id, name, department, subject, email, phone) VALUES (%s, %s, %s, %s, %s, %s)",
            (faculty_id, name, department, subject, email, phone)
        )
        flash(f"Faculty member '{name}' onboarded successfully.", 'success')
    except Exception as e:
        flash(f"Error onboarding faculty: {str(e)}", 'danger')
        
    return redirect(url_for('faculty.index'))

@faculty_bp.route('/faculty/edit/<int:fac_id>', methods=['POST'])
@login_required
def edit(fac_id):
    faculty_id = request.form.get('faculty_id', '').strip()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    subject = request.form.get('subject', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    
    if not faculty_id or not name or not department or not subject:
        flash('Faculty ID, Name, Department, and Subject are required fields.', 'danger')
        return redirect(url_for('faculty.index'))
        
    existing = query_db("SELECT id FROM faculty WHERE faculty_id = %s AND id != %s", (faculty_id, fac_id), one=True)
    if existing:
        flash(f"Faculty ID '{faculty_id}' is already used by another faculty member.", 'danger')
        return redirect(url_for('faculty.index'))
        
    try:
        execute_db(
            "UPDATE faculty SET faculty_id = %s, name = %s, department = %s, subject = %s, email = %s, phone = %s WHERE id = %s",
            (faculty_id, name, department, subject, email, phone, fac_id)
        )
        flash(f"Faculty '{name}' details updated successfully.", 'success')
    except Exception as e:
        flash(f"Error updating faculty: {str(e)}", 'danger')
        
    return redirect(url_for('faculty.index'))

@faculty_bp.route('/faculty/delete/<int:fac_id>', methods=['POST'])
@login_required
def delete(fac_id):
    fac = query_db("SELECT name, faculty_id FROM faculty WHERE id = %s", (fac_id,), one=True)
    if not fac:
        flash("Faculty record not found.", 'danger')
        return redirect(url_for('faculty.index'))
        
    try:
        execute_db("DELETE FROM faculty WHERE id = %s", (fac_id,))
        flash(f"Faculty member '{fac['name']}' ({fac['faculty_id']}) removed successfully.", 'info')
    except Exception as e:
        flash(f"Error removing faculty: {str(e)}", 'danger')
        
    return redirect(url_for('faculty.index'))
