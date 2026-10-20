import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("SQLITE_DB_PATH", "app.db")

def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    Configures row factory, WAL mode, and enforces foreign key constraints.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

def init_db():
    """
    Executes database schema setup.
    Creates all necessary tables if they do not exist.
    """
    logger.info(f"Initializing database at {DB_PATH}")
    conn = get_db_connection()
    try:
        with conn:
            # 1. Users Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'student',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 2. Authors Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS authors (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    bio TEXT,
                    era TEXT
                )
            """)

            # 3. Books Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author_id TEXT,
                    file_path TEXT, -- Nullable (can refer to a source book with no PDF)
                    uploaded_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE SET NULL,
                    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
                )
            """)

            # 4. Book Authors Many-to-Many junction table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS book_authors (
                    book_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    PRIMARY KEY (book_id, author_id),
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                    FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE CASCADE
                )
            """)

            # 5. Note Projects Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS note_projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    document_id TEXT, -- Nullable (thematic projects)
                    teacher_id TEXT,  -- References authors(id) representing the Ustadz/teacher
                    created_by TEXT NOT NULL,
                    is_public INTEGER NOT NULL DEFAULT 1,
                    forked_from_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES books(id) ON DELETE SET NULL,
                    FOREIGN KEY (teacher_id) REFERENCES authors(id) ON DELETE SET NULL,
                    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (forked_from_id) REFERENCES note_projects(id) ON DELETE SET NULL
                )
            """)


            # 6. Commits Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS commits (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    parent_commit_id TEXT,
                    author_id TEXT NOT NULL,
                    commit_message TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES note_projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (parent_commit_id) REFERENCES commits(id) ON DELETE SET NULL,
                    FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # 7. Branches Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS branches (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    head_commit_id TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES note_projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (head_commit_id) REFERENCES commits(id) ON DELETE CASCADE,
                    UNIQUE(project_id, name)
                )
            """)

            # 8. Highlights Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS highlights (
                    id TEXT PRIMARY KEY,
                    commit_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    start_offset INTEGER NOT NULL,
                    end_offset INTEGER NOT NULL,
                    color_code TEXT DEFAULT 'yellow',
                    extracted_text TEXT NOT NULL,
                    FOREIGN KEY (commit_id) REFERENCES commits(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES books(id) ON DELETE CASCADE
                )
            """)

            # 9. Scholarly Reviews Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scholarly_reviews (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    commit_id TEXT NOT NULL,
                    scholar_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    comments TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES note_projects(id) ON DELETE CASCADE,
                    FOREIGN KEY (commit_id) REFERENCES commits(id) ON DELETE CASCADE,
                    FOREIGN KEY (scholar_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)

            # 10. Book Pages (Extracted Text Cache)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS book_pages (
                    id TEXT PRIMARY KEY,
                    book_id TEXT NOT NULL,
                    page_number INTEGER NOT NULL,
                    content TEXT,
                    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
                    UNIQUE(book_id, page_number)
                )
            """)

            # 11. AI Configs Table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS ai_configs (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    model_type TEXT NOT NULL, -- 'online' (e.g. OpenAI/Gemini) or 'local'
                    provider TEXT,
                    api_key TEXT,
                    is_active INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise e
    finally:
        conn.close()
