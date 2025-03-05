import sqlite3
import os

# Path to the SQLite database file using os.path.join()
db_path = os.path.join('data', 'database.db')

# Ensure the data directory exists
os.makedirs('data', exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create the users table with fields: id, username, password, email, and role
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL
)
''')

conn.commit()
conn.close()
print("Database and users table created successfully!")
