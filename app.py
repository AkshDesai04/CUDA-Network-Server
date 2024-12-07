import os
import sqlite3
import random
from flask import Flask, request, render_template, jsonify
from threading import Thread
import socket

app = Flask(__name__)

# Constants
DATABASE = 'logs.db'
OUTPUT_DIR = 'outputs'
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize the database and ensure correct schema
def setup_database():
    conn = get_db_connection()

    # Check and create necessary tables
    with conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS sessions (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id TEXT NOT NULL,
                            port INTEGER NOT NULL
                        )''')

        try:
            conn.execute('ALTER TABLE logs ADD COLUMN message TEXT NOT NULL')
        except sqlite3.OperationalError:
            pass

        conn.execute('''CREATE TABLE IF NOT EXISTS logs (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            session_id INTEGER NOT NULL,
                            message TEXT NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS files (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            session_id INTEGER NOT NULL,
                            file_name TEXT NOT NULL,
                            file_content TEXT NOT NULL,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                        )''')

    conn.close()


# Log activity in the database
def log_activity(session_id, message, username=None, ip_address=None):
    conn = get_db_connection()
    if username and ip_address:
        message = f"Username: {username}, IP: {ip_address} - {message}"
    conn.execute('INSERT INTO logs (session_id, message) VALUES (?, ?)', (session_id, message))
    conn.commit()
    conn.close()


# Compile and run CUDA code
def compile_and_run(user_id, session_id, output_file):
    try:
        # Simulate compiling and running the CUDA code
        log_activity(session_id, f"Compiling and running CUDA code for user {user_id}")
        with open(output_file, 'w') as f:
            f.write(f"CUDA program output for user {user_id}\n")
            f.write("Simulation complete!")
        log_activity(session_id, f"Output written to {output_file}")
    except Exception as e:
        log_activity(session_id, f"Error: {str(e)}")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create_session', methods=['POST'])
def create_session():
    user_id = str(random.randint(1000, 9999))  # Unique user ID for session
    port = random.randint(8000, 9000)  # Generate a unique port for the user

    # Create session in the database
    conn = get_db_connection()
    cursor = conn.execute('INSERT INTO sessions (user_id, port) VALUES (?, ?)', (user_id, port))
    conn.commit()
    session_id = cursor.lastrowid  # Get the session ID
    conn.close()

    # Log the session creation with IP and MAC address if possible
    ip_address = request.remote_addr
    log_activity(session_id, f"Created new session for user {user_id} on port {port}", username=None, ip_address=ip_address)

    # Create a directory for the user session
    user_output_dir = os.path.join(OUTPUT_DIR, f"user_{user_id}")
    if not os.path.exists(user_output_dir):
        os.makedirs(user_output_dir)

    # Start a background thread to compile and run CUDA code for this user
    output_file = os.path.join(user_output_dir, 'output.txt')
    thread = Thread(target=compile_and_run, args=(user_id, session_id, output_file))
    thread.start()

    # Return port and user ID
    return render_template('session_created.html', user_id=user_id, port=port)


@app.route('/submit_username', methods=['POST'])
def submit_username():
    user_id = request.form['user_id']
    username = request.form['username']
    
    # Get session ID from the database
    conn = get_db_connection()
    cursor = conn.execute('SELECT id FROM sessions WHERE user_id = ?', (user_id,))
    session = cursor.fetchone()
    session_id = session['id'] if session else None
    conn.close()

    # Log the username submission
    if session_id:
        ip_address = request.remote_addr
        log_activity(session_id, "User submitted their username", username=username, ip_address=ip_address)
        return render_template('output.html', username=username, session_id=session_id)
    else:
        return "Session not found", 404


@app.route('/view_output/<user_id>')
def view_output(user_id):
    output_file = os.path.join(OUTPUT_DIR, f"user_{user_id}", 'output.txt')
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            content = f.read()
        return render_template('output.html', output=content)
    else:
        return "Output not yet available. Please refresh the page.", 404


# Start Flask app
if __name__ == '__main__':
    setup_database()  # Ensure database tables are created
    app.run(host='0.0.0.0', port=5000, debug=True)