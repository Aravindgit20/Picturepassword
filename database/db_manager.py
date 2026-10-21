# Database Manager
# Handles database initialization and connections (MySQL via PyMySQL)

import os
import warnings
from contextlib import contextmanager
import pymysql
import pymysql.cursors

# MySQL connection config — credentials read from environment variables
MYSQL_CONFIG = {
    'host':        os.environ.get('MYSQL_HOST', 'localhost'),
    'user':        os.environ.get('MYSQL_USER', 'root'),
    'password':    os.environ.get('MYSQL_PASSWORD', 'Mydatabase123'),
    'database':    os.environ.get('MYSQL_DATABASE', 'picture_password_auth'),
    'port':        int(os.environ.get('MYSQL_PORT', 3306)),
    'charset':     'utf8mb4',
    'cursorclass': pymysql.cursors.Cursor,
}

_required_env = ['MYSQL_PASSWORD', 'MYSQL_HOST', 'MYSQL_USER', 'MYSQL_DATABASE']
for _var in _required_env:
    if not os.environ.get(_var):
        warnings.warn(
            f"Environment variable {_var} is not set; using default value.",
            stacklevel=2
        )

class DatabaseManager:
    """Manages MySQL database connections and initialization"""

    @staticmethod
    def get_connection():
        """Get MySQL database connection"""
        conn = pymysql.connect(**MYSQL_CONFIG)
        return conn

    @staticmethod
    @contextmanager
    def get_cursor():
        """Context manager yielding a cursor and guaranteeing cleanup.

        Commits on normal exit, rolls back on an exception, and always closes
        the cursor and connection. This fixes the previous connection leak where
        an exception skipped the close() calls and left connections open.
        """
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def init_database():
        """Initialize the database with required tables"""
        try:
            conn = DatabaseManager.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    picture_password_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    success BOOLEAN NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS auth_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    session_token VARCHAR(255) UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME DEFAULT NULL,
                    current_image_index INT DEFAULT 0,
                    wrong_attempts INT DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            # Add image_started_at column if it doesn't exist (safe migration)
            try:
                cursor.execute(
                    "ALTER TABLE auth_sessions ADD COLUMN image_started_at DATETIME DEFAULT NULL"
                )
                conn.commit()
            except Exception:
                pass  # Column already exists — safe to ignore

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_reset_requests (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    username VARCHAR(50) NOT NULL,
                    reason TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at DATETIME DEFAULT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

            conn.commit()
            cursor.close()
            conn.close()
            print("MySQL database initialized successfully!")

        except Exception as e:
            print(f"Warning: Could not initialize database on startup: {e}")
            print("Make sure MySQL is running and accessible.")

    @staticmethod
    def migrate_database():
        """No-op: kept for compatibility"""
        pass


# Initialize database on module import
try:
    DatabaseManager.init_database()
except Exception as e:
    print(f"Warning: Database init failed: {e}")
