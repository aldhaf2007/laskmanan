import unittest
from app import create_app
from db import query_db, execute_db

class AttendanceSystemTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def login_admin(self, username='admin', password='admin123'):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    # 5.1 Admin Login Tests
    def test_01_access_control_redirects_unauthenticated_users(self):
        """Unauthenticated requests must be redirected to /login."""
        protected_urls = ['/', '/dashboard', '/students', '/faculty', '/attendance', '/reports']
        for url in protected_urls:
            response = self.client.get(url, follow_redirects=False)
            self.assertEqual(response.status_code, 302, f"Failed to redirect unauthenticated request to {url}")
            self.assertIn('/login', response.headers['Location'])

    def test_02_invalid_login_error_handling(self):
        """Invalid credentials should show error message and not authenticate."""
        response = self.login_admin('admin', 'wrongpassword')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid username or password', response.data)

    def test_03_valid_login_and_logout(self):
        """Valid credentials should authenticate and redirect to dashboard."""
        response = self.login_admin('admin', 'admin123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Administrative Dashboard', response.data)

        # Test Logout
        logout_resp = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'logged out', logout_resp.data)

    # 5.2 Student Management Tests
    def test_04_student_crud_and_directory(self):
        """Test adding, listing, editing, and deleting student records."""
        self.login_admin('admin', 'admin123')

        # 1. Add Student
        test_roll = 'TEST2026001'
        # Clean up any leftover from previous test
        execute_db("DELETE FROM students WHERE roll_number = %s", (test_roll,))

        add_resp = self.client.post('/students/add', data={
            'roll_number': test_roll,
            'name': 'Test Student Alpha',
            'class_name': 'TEST-CLASS',
            'contact': '+91 9998887770'
        }, follow_redirects=True)
        self.assertIn(b'added successfully', add_resp.data)

        # 2. Verify in Directory View
        view_resp = self.client.get('/students?search=Test+Student+Alpha')
        self.assertIn(b'Test Student Alpha', view_resp.data)
        self.assertIn(b'TEST2026001', view_resp.data)

        # 3. Edit Student
        student = query_db("SELECT id FROM students WHERE roll_number = %s", (test_roll,), one=True)
        self.assertIsNotNone(student)
        edit_resp = self.client.post(f'/students/edit/{student["id"]}', data={
            'roll_number': test_roll,
            'name': 'Test Student Updated',
            'class_name': 'TEST-CLASS',
            'contact': '+91 9998887771'
        }, follow_redirects=True)
        self.assertIn(b'updated successfully', edit_resp.data)

        updated_student = query_db("SELECT name, contact FROM students WHERE id = %s", (student["id"],), one=True)
        self.assertEqual(updated_student['name'], 'Test Student Updated')

        # 4. Delete Student
        del_resp = self.client.post(f'/students/delete/{student["id"]}', follow_redirects=True)
        self.assertIn(b'deleted successfully', del_resp.data)
        check_deleted = query_db("SELECT id FROM students WHERE id = %s", (student["id"],), one=True)
        self.assertIsNone(check_deleted)

    # 5.3 Faculty Management Tests
    def test_05_faculty_crud_and_directory(self):
        """Test onboarding, editing, and offboarding faculty members."""
        self.login_admin('admin', 'admin123')

        test_fac_id = 'FACTEST99'
        execute_db("DELETE FROM faculty WHERE faculty_id = %s", (test_fac_id,))

        # 1. Onboard
        add_resp = self.client.post('/faculty/add', data={
            'faculty_id': test_fac_id,
            'name': 'Dr. Test Professor',
            'department': 'Testing Dept',
            'subject': 'Software Quality Assurance',
            'email': 'prof.test@institution.edu',
            'phone': '+91 9112233445'
        }, follow_redirects=True)
        self.assertIn(b'onboarded successfully', add_resp.data)

        # 2. View in consolidated roster
        view_resp = self.client.get('/faculty?search=FACTEST99')
        self.assertIn(b'Dr. Test Professor', view_resp.data)
        self.assertIn(b'Software Quality Assurance', view_resp.data)

        # 3. Edit
        fac = query_db("SELECT id FROM faculty WHERE faculty_id = %s", (test_fac_id,), one=True)
        self.assertIsNotNone(fac)
        edit_resp = self.client.post(f'/faculty/edit/{fac["id"]}', data={
            'faculty_id': test_fac_id,
            'name': 'Dr. Test Professor Senior',
            'department': 'Advanced Testing Dept',
            'subject': 'Software Quality Assurance',
            'email': 'prof.senior@institution.edu',
            'phone': '+91 9112233445'
        }, follow_redirects=True)
        self.assertIn(b'updated successfully', edit_resp.data)

        # 4. Delete / Offboard
        del_resp = self.client.post(f'/faculty/delete/{fac["id"]}', follow_redirects=True)
        self.assertIn(b'removed successfully', del_resp.data)
        check_fac = query_db("SELECT id FROM faculty WHERE id = %s", (fac["id"],), one=True)
        self.assertIsNone(check_fac)

    # 5.4 Attendance Management Tests (Logging & Corrections)
    def test_06_daily_attendance_logging_and_corrections(self):
        """Test daily attendance marking and subsequent correction updates."""
        self.login_admin('admin', 'admin123')

        # Create temporary student
        test_roll = 'TESTATT001'
        execute_db("DELETE FROM students WHERE roll_number = %s", (test_roll,))
        execute_db("INSERT INTO students (roll_number, name, class_name, contact) VALUES (%s, %s, %s, %s)",
                   (test_roll, 'Attendance Test Student', 'ATT-CLASS', 'test@test.com'))
        student = query_db("SELECT id FROM students WHERE roll_number = %s", (test_roll,), one=True)

        date_str = '2026-09-20'
        subject_name = 'Systems Architecture'

        # 1. Mark Attendance as Present
        save_resp = self.client.post('/attendance/save', data={
            'class_name': 'ATT-CLASS',
            'subject': subject_name,
            'date': date_str,
            f'status_{student["id"]}': 'Present'
        }, follow_redirects=True)
        self.assertIn(b'recorded/updated successfully', save_resp.data)

        rec = query_db("SELECT status FROM attendance WHERE student_id = %s AND date = %s AND subject = %s",
                       (student['id'], date_str, subject_name), one=True)
        self.assertIsNotNone(rec)
        self.assertEqual(rec['status'], 'Present')

        # 2. Correction: Change from Present to Absent on same date and subject
        correct_resp = self.client.post('/attendance/save', data={
            'class_name': 'ATT-CLASS',
            'subject': subject_name,
            'date': date_str,
            f'status_{student["id"]}': 'Absent'
        }, follow_redirects=True)
        self.assertIn(b'recorded/updated successfully', correct_resp.data)

        rec_updated = query_db("SELECT status FROM attendance WHERE student_id = %s AND date = %s AND subject = %s",
                               (student['id'], date_str, subject_name), one=True)
        self.assertEqual(rec_updated['status'], 'Absent')

        # Clean up
        execute_db("DELETE FROM students WHERE id = %s", (student['id'],))

    # 5.5 Attendance Reports & CSV Export Tests
    def test_07_attendance_reports_and_csv_export(self):
        """Test automated calculation, low-attendance alert, and CSV export."""
        self.login_admin('admin', 'admin123')

        # 1. View Reports page
        resp = self.client.get('/reports')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Attendance Reports & Analytics', resp.data)
        self.assertIn(b'Average Attendance', resp.data)

        # 2. Filter by low attendance only
        resp_low = self.client.get('/reports?low_only=1')
        self.assertEqual(resp_low.status_code, 200)
        self.assertIn(b'Showing Low Attendance Students Only', resp_low.data)

        # 3. CSV Export
        export_resp = self.client.get('/reports/export')
        self.assertEqual(export_resp.status_code, 200)
        self.assertEqual(export_resp.mimetype, 'text/csv')
        self.assertIn('attachment;filename=attendance_report_', export_resp.headers['Content-Disposition'])
        csv_content = export_resp.data.decode('utf-8')
        self.assertIn('Roll Number,Student Name,Class,Contact', csv_content)
        self.assertIn('Attendance Percentage (%)', csv_content)

    def test_08_duplicate_validations(self):
        """Test duplicate roll number and duplicate faculty ID validations."""
        self.login_admin('admin', 'admin123')

        # Try to add existing roll number CSE2024001
        dup_student = self.client.post('/students/add', data={
            'roll_number': 'CSE2024001',
            'name': 'Duplicate Person',
            'class_name': 'CSE-A',
            'contact': 'dup@test.com'
        }, follow_redirects=True)
        self.assertIn(b'already exists', dup_student.data)

        # Try to onboard duplicate faculty FAC001
        dup_fac = self.client.post('/faculty/add', data={
            'faculty_id': 'FAC001',
            'name': 'Duplicate Prof',
            'department': 'CSE',
            'subject': 'Math'
        }, follow_redirects=True)
        self.assertIn(b'already exists', dup_fac.data)

    def test_09_api_students_by_class(self):
        """Test the JSON API returning students by class."""
        self.login_admin('admin', 'admin123')
        resp = self.client.get('/api/students-by-class?class_name=CSE-A')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(len(data) > 0)
        self.assertEqual(data[0]['class_name'], 'CSE-A')

if __name__ == '__main__':
    unittest.main()
