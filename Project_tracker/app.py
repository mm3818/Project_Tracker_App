from flask import Flask, render_template, request, redirect, flash, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a secure key

# Path to the SQLite database file
DATABASE = os.path.join('data', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows dictionary-like access to rows
    return conn

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Retrieve form data
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash("Please fill in both fields.", "error")
            return redirect(url_for('login'))

        conn = get_db_connection()
        # For security, use password hashing in production
        user = conn.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?',
            (username, password)
        ).fetchone()
        conn.close()

        if user is None:
            flash("Invalid username or password.", "error")
            return redirect(url_for('login'))
        else:
            session['user_id'] = user['id']
            session['username'] = user['username']
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

        # Check if passwords match
        if password != repassword:
            flash("Passwords do not match.", "error")
            return redirect(url_for('register'))

        conn = get_db_connection()
        # Check if user with same username or email already exists
        existing_user = conn.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username, email)
        ).fetchone()
        if existing_user:
            flash("Username or email already exists.", "error")
            conn.close()
            return redirect(url_for('register'))

        # Insert new user into the database (in production, hash the password)
        conn.execute(
            "INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)",
            (username, password, email, role)
        )
        conn.commit()
        conn.close()

        flash("Registration successful! Please login.", "success")
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash("Please login to access the dashboard.", "error")
        return redirect(url_for('login'))
    return f"Welcome {session['username']}! This is your dashboard."

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
