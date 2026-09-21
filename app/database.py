import sqlite3
from app.config import DB_PATH


def connect():
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys = ON')
    con.execute('PRAGMA journal_mode = WAL')
    con.execute('PRAGMA busy_timeout = 5000')
    return con


def init_db():
    con = connect()
    con.executescript('''
    CREATE TABLE IF NOT EXISTS students (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      college TEXT, degree TEXT, branch TEXT,
      year INTEGER, semester INTEGER, location TEXT,
      cgpa REAL, tenth REAL, twelfth REAL, backlogs INTEGER DEFAULT 0,
      target_role TEXT, career_goal TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS skills (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
      name TEXT NOT NULL, level TEXT, score REAL,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS projects (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
      name TEXT NOT NULL, description TEXT, technologies TEXT,
      github_url TEXT, live_url TEXT,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS certifications (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
      name TEXT NOT NULL, platform TEXT, issuer TEXT, url TEXT,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS academics (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
      term TEXT NOT NULL, cgpa REAL, attendance REAL, backlogs INTEGER DEFAULT 0,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS coding (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
      platform TEXT, problems_solved INTEGER DEFAULT 0, easy INTEGER DEFAULT 0,
      medium INTEGER DEFAULT 0, hard INTEGER DEFAULT 0, rating REAL,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS performance (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
      category TEXT NOT NULL, score REAL, note TEXT,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
      title TEXT NOT NULL, impact TEXT, priority TEXT DEFAULT 'HIGH', completed INTEGER DEFAULT 0,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS analyses (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
      overall REAL, summary TEXT, gaps TEXT, roadmap TEXT, score_breakdown TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS resume_analyses (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL,
      filename TEXT NOT NULL, resume_score REAL, result_json TEXT,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_skills_student ON skills(student_id);
    CREATE INDEX IF NOT EXISTS idx_projects_student ON projects(student_id);
    CREATE INDEX IF NOT EXISTS idx_tasks_student ON tasks(student_id);
    CREATE INDEX IF NOT EXISTS idx_analyses_student ON analyses(student_id, created_at);
    CREATE TABLE IF NOT EXISTS learning_progress (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, title TEXT NOT NULL,
      completed INTEGER DEFAULT 0, completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(student_id, title), FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS project_progress (
      id INTEGER PRIMARY KEY AUTOINCREMENT, student_id INTEGER NOT NULL, title TEXT NOT NULL,
      completed INTEGER DEFAULT 0, file_name TEXT, file_path TEXT, completed_at TEXT DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(student_id, title), FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
    );
    CREATE INDEX IF NOT EXISTS idx_learning_progress_student ON learning_progress(student_id);
    CREATE INDEX IF NOT EXISTS idx_project_progress_student ON project_progress(student_id);
    ''')
    con.execute('UPDATE skills SET score = score / 10.0 WHERE score > 10')
    con.execute('UPDATE performance SET score = score / 10.0 WHERE score > 10')
    con.commit(); con.close()
