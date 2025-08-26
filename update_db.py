import sqlite3
import os

DATABASE = os.path.join('data', 'database.db')

def create_tables(conn):
    cursor = conn.cursor()
    # Create the users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        role TEXT NOT NULL
    )
    ''')
    # Create the projects table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        deadline DATE,
        progress INTEGER DEFAULT 0,
        assigned_to INTEGER,
        FOREIGN KEY (assigned_to) REFERENCES users(id)
    )
    ''')
    # Create the feedback table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        comments TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()

def add_column_if_not_exists(conn, table_name, column_name, column_definition):
    """
    Check if a column exists in the table; add it if missing.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    if column_name not in columns:
        print(f"Adding column '{column_name}' to '{table_name}'")
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
        conn.commit()

def update_schema():
    # Ensure the data directory exists
    os.makedirs('data', exist_ok=True)
    conn = sqlite3.connect(DATABASE)
    
    # Create tables if they don't exist
    create_tables(conn)
    
    # Add the 'last_login' column to 'users' table if it doesn't exist.
    add_column_if_not_exists(conn, 'users', 'last_login', 'DATETIME')
    
    conn.close()
    print("Database schema updated successfully!")

if __name__ == '__main__':
    update_schema()
