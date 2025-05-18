from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') or os.urandom(24)

DATABASE = 'journal.db'
APP_PASSWORD = os.getenv('APP_PASSWORD')
GF_PASSWORD = os.getenv('GF_PASSWORD')


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == APP_PASSWORD or password == GF_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Incorrect password, try again.')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


def login_required(f):
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    entries = conn.execute('SELECT * FROM entries ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('index.html', entries=entries)


@app.route('/new', methods=['GET', 'POST'])
@login_required
def new_entry():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if title and content:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO entries (title, content, created_at) VALUES (?, ?, ?)',
                (title, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            )
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        else:
            return render_template('new.html', error="Both title and content are required.")
    return render_template('new.html')


@app.route('/delete/<int:entry_id>')
@login_required
def delete_entry(entry_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM entries WHERE id = ?', (entry_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
