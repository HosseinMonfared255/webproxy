"""
Database models and utilities using SQLite.
Stores file metadata, download tokens, and their expiration status.
"""
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from contextlib import contextmanager

from config import DATABASE_PATH, TOKEN_EXPIRATION, SECRET_KEY


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database with required tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Files table - stores file metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_id TEXT UNIQUE NOT NULL,
                file_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                mime_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Download tokens table - stores secure download tokens
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS download_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT UNIQUE NOT NULL,
                unique_id TEXT NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (unique_id) REFERENCES files(unique_id)
            )
        """)
        
        # Create indexes for faster lookups
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_unique_id ON files(unique_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_token ON download_tokens(token)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tokens_expires ON download_tokens(expires_at)")
        
        conn.commit()


def save_file_metadata(unique_id: str, file_id: str, file_name: str, 
                       file_type: str, file_size: int, user_id: int,
                       mime_type: Optional[str] = None) -> bool:
    """Save file metadata to database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO files 
                (unique_id, file_id, file_name, file_type, file_size, user_id, mime_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (unique_id, file_id, file_name, file_type, file_size, user_id, mime_type))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error saving file metadata: {e}")
            return False


def get_file_metadata(unique_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve file metadata by unique_id."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE unique_id = ?", (unique_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def generate_secure_token(unique_id: str) -> str:
    """Generate a secure, time-limited download token."""
    # Generate random token
    random_part = secrets.token_urlsafe(32)
    timestamp = datetime.now().timestamp()
    
    # Create token with hash for verification
    token_data = f"{unique_id}:{timestamp}:{random_part}"
    token_hash = hashlib.sha256(f"{token_data}:{SECRET_KEY}".encode()).hexdigest()[:16]
    token = f"{random_part}_{token_hash}"
    
    # Calculate expiration time
    expires_at = datetime.now() + timedelta(seconds=TOKEN_EXPIRATION)
    
    # Store token in database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO download_tokens (token, unique_id, expires_at)
            VALUES (?, ?, ?)
        """, (token, unique_id, expires_at))
        conn.commit()
    
    return token


def validate_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a download token.
    Returns file info if valid, None if invalid/expired/used.
    Marks token as used after validation.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get token info
        cursor.execute("""
            SELECT * FROM download_tokens 
            WHERE token = ? AND used = 0 AND expires_at > ?
        """, (token, datetime.now()))
        token_row = cursor.fetchone()
        
        if not token_row:
            return None
        
        unique_id = token_row['unique_id']
        
        # Get file metadata
        cursor.execute("SELECT * FROM files WHERE unique_id = ?", (unique_id,))
        file_row = cursor.fetchone()
        
        if not file_row:
            return None
        
        # Mark token as used (one-time use)
        cursor.execute("""
            UPDATE download_tokens SET used = 1 WHERE token = ?
        """, (token,))
        conn.commit()
        
        return dict(file_row)


def cleanup_expired_tokens():
    """Remove expired tokens from database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM download_tokens WHERE expires_at < ?", (datetime.now(),))
        conn.commit()


def delete_file_metadata(unique_id: str) -> bool:
    """Delete file metadata (used when user cancels)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM files WHERE unique_id = ?", (unique_id,))
            cursor.execute("DELETE FROM download_tokens WHERE unique_id = ?", (unique_id,))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting file metadata: {e}")
            return False


# Initialize database on module import
init_db()
