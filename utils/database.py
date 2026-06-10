import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'jobs.db')

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT UNIQUE,
            description TEXT,
            source TEXT,
            score INTEGER,
            recommendation TEXT,
            resume_path TEXT,
            cover_letter_path TEXT,
            status TEXT DEFAULT 'new',
            date_found TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_job(job: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO jobs 
            (title, company, location, url, description, source, date_found)
            VALUES (:title, :company, :location, :url, :description, :source, :date_found)
        ''', job)
        conn.commit()
    finally:
        conn.close()

def get_unscored_jobs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs WHERE score IS NULL')
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs

def update_job_score(job_id: int, score: int, recommendation: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE jobs SET score = ?, recommendation = ? WHERE id = ?
    ''', (score, recommendation, job_id))
    conn.commit()
    conn.close()

def get_all_jobs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM jobs ORDER BY score DESC, date_found DESC')
    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs

def update_job_status(job_id: int, status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))
    conn.commit()
    conn.close()

def is_duplicate(title: str, company: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM jobs 
        WHERE LOWER(title) = LOWER(?) AND LOWER(company) = LOWER(?)
    ''', (title, company))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0