# Student Attendance Management System

A production-ready Student Attendance Management System built with **Flask**, **MySQL**, and modern **HTML5, CSS3, and JavaScript**.

---

## ⚡ 1-Click Automated Setup & Run

The project includes smart setup scripts for both **Linux** and **Windows** that automatically:
1. Detect and install Python 3 and virtual environment if missing.
2. Detect, install, and start MySQL/MariaDB server if missing.
3. Install all required dependencies from `requirements.txt`.
4. Automatically create the database (`student_attendance_db`), execute the table schema, and seed default admin and sample data.
5. Launch the application and open the browser!

### On Linux / macOS
Open your terminal in the project directory and run:
```bash
./setup_and_run.sh
```
*(Or `bash setup_and_run.sh`)*

### On Windows
You can use either:
1. **Command Prompt / Double-Click**:
   - Simply double-click `setup_and_run.bat` in File Explorer, or run in cmd:
     ```cmd
     setup_and_run.bat
     ```
2. **PowerShell**:
   - Right-click `setup_and_run.ps1` and select "Run with PowerShell", or run:
     ```powershell
     .\setup_and_run.ps1
     ```

---

## 🔑 Default Admin Credentials

- **URL**: [http://localhost:5000](http://localhost:5000)
- **Username**: `admin`
- **Password**: `admin123`

---

## 🌟 Modules & Features

### 5.1 Admin Login
- **Access Control**: Secure session-based authentication guarding all operational routes with `@login_required`.
- **MySQL Validation**: Passwords hashed securely using Werkzeug's `generate_password_hash` (PBKDF2/SHA-256) and verified against MySQL `admins` table.
- **Navigation**: Seamless redirect to the Admin Dashboard upon login, supporting `next` URL redirection.
- **Error Handling**: Contextual, auto-dismissible flash alerts for invalid username or password attempts.

### 5.2 Student Management
- **Record Creation**: Administrator can register students with Roll Number, Full Name, Class/Section, and Contact information.
- **Data Maintenance**: In-place editing of student details via modal dialogs.
- **Record Deletion**: Safe deletion of student records with foreign-key cascade removal of related attendance history.
- **Searchable Directory**: Real-time client-side instant search across name, roll number, or contact, combined with class filter dropdown.

### 5.3 Faculty Management
- **Onboarding**: Register faculty members with unique Faculty ID, Full Name, Department, Assigned Subject, Email, and Phone number.
- **Profile Updates**: Edit faculty subject and contact details.
- **Offboarding**: Remove faculty members when they leave the institution.
- **Consolidated Roster**: Unified view of teaching staff with real-time search and department filtering.

### 5.4 Attendance Management
- **Daily Logging**: Select Class, Subject, and Date to generate roll sheets with Present/Absent radio toggles.
- **Database Persistence**: Stored in MySQL with student ID, date, class, subject, and marker name.
- **Corrections Support**: Built with MySQL `INSERT ... ON DUPLICATE KEY UPDATE` to automatically update existing records when corrections are made without duplication.
- **High Efficiency**: Includes one-click **"✅ Mark All Present"** and **"❌ Mark All Absent"** controls.

### 5.5 Attendance Report & Analytics
- **Custom Reporting**: Filter attendance records by Class, Subject, Individual Student, or Date Range.
- **Automated Calculation**: Automatically computes Total Sessions, Attended, Absent, and Attendance Percentage (`%`).
- **Low-Attendance Monitoring**: Highlights at-risk students with attendance under **75%** with animated warning badges.
- **Data Export**:
  - 📥 **Export to CSV**: Instant download of formatted attendance spreadsheets.
  - 🖨️ **Print Report**: Print-optimized stylesheet concealing navigation controls and formatting data cleanly.

---

## 🛠️ Manual Installation (Alternative)

If you prefer to set up manually without the automated scripts:

```bash
# 1. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate.bat

# 2. Install requirements
pip install -r requirements.txt

# 3. Configure .env if your MySQL credentials differ
# (Default: root with blank password connecting via socket or localhost)

# 4. Initialize Database & Seed
python setup_db.py

# 5. Run the server
python app.py
```

### Running Automated Tests
```bash
python -m unittest discover -s tests -v
```
