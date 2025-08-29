from flask import Flask, render_template, request, redirect, flash, session, url_for
import sqlite3, os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure random key

# Path to the SQLite database
DATABASE = os.path.join('data', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def role_required(*roles):
    """Decorator to restrict access to users with specified roles."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in.", "error")
                return redirect(url_for('login'))
            if session.get('role') not in roles:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash("Please fill in both fields.", "error")
            return render_template('login.html')

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ? AND password = ?",
            (username, password)
        ).fetchone()
        conn.close()

        if not user:
            flash("Invalid username or password.", "error")
            return render_template('login.html')

        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']

        # Optional: update last_login if column exists
        conn = get_db_connection()
        try:
            conn.execute("UPDATE users SET last_login = datetime('now') WHERE id = ?", (user['id'],))
            conn.commit()
        except sqlite3.OperationalError:
            pass
        conn.close()

        flash("Login successful!", "success")
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form.get('role')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        repassword = request.form.get('repassword')

        if password != repassword:
            flash("Passwords do not match.", "error")
            return render_template('register.html')

        conn = get_db_connection()
        existing = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()
        if existing:
            flash("Username or email already exists.", "error")
            conn.close()
            return render_template('register.html')

        conn.execute(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
            (username, password, email, role)
        )
        conn.commit()
        conn.close()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in.", "error")
        return redirect(url_for('login'))

    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('projects'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))
    else:
        return render_template('dashboard.html')

# Admin: Create & List Projects
@app.route('/projects', methods=['GET', 'POST'])
@role_required('admin')
def projects():
    conn = get_db_connection()
    user_id = session['user_id'] # Get the logged-in user's ID

    if request.method == 'POST':
        # ... (rest of the POST logic is the same)
        title = request.form.get('title')
        description = request.form.get('description')
        deadline = request.form.get('deadline')
        assign_input = request.form.get('assigned_to', '').strip()

        # ... (logic to get assigned_to user_id)
        if assign_input.isdigit():
            assigned_to = int(assign_input)
        else:
            user = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (assign_input,)
            ).fetchone()
            if not user:
                flash(f"No user found with username '{assign_input}'.", "error")
                conn.close()
                return redirect(url_for('projects'))
            assigned_to = user['id']

        # Add `created_by` column and its value to the INSERT statement
        conn.execute(
            "INSERT INTO projects (title, description, deadline, assigned_to, created_by) VALUES (?, ?, ?, ?, ?)",
            (title, description, deadline, assigned_to, user_id)
        )
        conn.commit()
        flash("Project created successfully!", "success")

    # Filter projects by the `created_by` columna
    projects = conn.execute("SELECT * FROM projects WHERE created_by = ?", (user_id,)).fetchall()
    conn.close()
    return render_template('admin_dashboard.html', projects=projects)
# Admin: Edit Project
@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_project(project_id):
    conn = get_db_connection()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        deadline = request.form.get('deadline')
        assign_input = request.form.get('assigned_to', '').strip()

        if assign_input.isdigit():
            assigned_to = int(assign_input)
        else:
            user = conn.execute(
                "SELECT id FROM users WHERE username = ?",
                (assign_input,)
            ).fetchone()
            if not user:
                flash(f"No user found with username '{assign_input}'.", "error")
                conn.close()
                return redirect(url_for('edit_project', project_id=project_id))
            assigned_to = user['id']

        conn.execute(
            "UPDATE projects SET title = ?, description = ?, deadline = ?, assigned_to = ? WHERE id = ?",
            (title, description, deadline, assigned_to, project_id)
        )
        conn.commit()
        conn.close()
        flash("Project updated successfully!", "success")
        return redirect(url_for('projects'))

    project = conn.execute(
        "SELECT * FROM projects WHERE id = ?",
        (project_id,)
    ).fetchone()
    conn.close()
    return render_template('edit_project.html', project=project)

# Student: View Tasks & Projects
@app.route('/student_dashboard')
@role_required('student')
def student_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    tasks = conn.execute(
        "SELECT * FROM projects WHERE assigned_to = ?", (user_id,)
    ).fetchall()
    projects = conn.execute("SELECT * FROM projects").fetchall()
    conn.close()
    return render_template('student_dashboard.html', tasks=tasks, projects=projects)

# Student: Update Task Progress
@app.route('/update_task/<int:task_id>', methods=['GET', 'POST'])
@role_required('student')
def update_task(task_id):
    conn = get_db_connection()
    task = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (task_id,)
    ).fetchone()
    if not task:
        conn.close()
        flash("Task not found.", "error")
        return redirect(url_for('student_dashboard'))

    if request.method == 'POST':
        new_progress = request.form.get('progress')
        if new_progress is None:
            flash("Progress value is missing.", "error")
            conn.close()
            return redirect(url_for('update_task', task_id=task_id))

        try:
            prog = int(new_progress)
            if prog < 0 or prog > 100:
                raise ValueError
        except ValueError:
            flash("Please enter a valid number between 0 and 100.", "error")
            conn.close()
            return redirect(url_for('update_task', task_id=task_id))

        conn.execute(
            "UPDATE projects SET progress = ? WHERE id = ?",
            (prog, task_id)
        )
        conn.commit()
        conn.close()
        flash("Task progress updated!", "success")
        return redirect(url_for('student_dashboard'))

    conn.close()
    return render_template('update_task.html', task=task)

# Project Feedback: View & Submit
@app.route('/project/<int:project_id>/feedback', methods=['GET', 'POST'])
@role_required('student', 'admin')
def project_feedback(project_id):
    conn = get_db_connection()
    project = conn.execute(
        "SELECT * FROM projects WHERE id = ?", (project_id,)
    ).fetchone()
    if not project:
        conn.close()
        flash("Project not found.", "error")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        comments = request.form.get('comments')
        user_id = session['user_id']
        conn.execute(
            "INSERT INTO feedback (project_id, user_id, comments) VALUES (?, ?, ?)",
            (project_id, user_id, comments)
        )
        conn.commit()
        flash("Feedback submitted!", "success")

    feedbacks = conn.execute(
        "SELECT f.comments, f.created_at, u.username "
        "FROM feedback f JOIN users u ON f.user_id = u.id "
        "WHERE f.project_id = ?",
        (project_id,)
    ).fetchall()
    conn.close()
    return render_template('feedback.html', project=project, feedbacks=feedbacks)

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
