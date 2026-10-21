# Authentication Session Model - MySQL version

from datetime import datetime, timedelta
from typing import Optional, Dict
from database.db_manager import DatabaseManager

class AuthSession:

    @staticmethod
    def create_session(user_id: int, session_token: str) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute('DELETE FROM auth_sessions WHERE user_id = %s', (user_id,))
                expires_at = datetime.now() + timedelta(minutes=10)
                cursor.execute(
                    'INSERT INTO auth_sessions (user_id, session_token, expires_at) VALUES (%s, %s, %s)',
                    (user_id, session_token, expires_at)
                )
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False

    @staticmethod
    def get_session(session_token: str) -> Optional[Dict]:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT user_id, current_image_index, created_at, expires_at, wrong_attempts, image_started_at FROM auth_sessions WHERE session_token = %s AND expires_at > NOW()',
                    (session_token,)
                )
                row = cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'current_image_index': row[1],
                    'created_at': row[2],
                    'expires_at': row[3],
                    'wrong_attempts': row[4] if row[4] is not None else 0,
                    'image_started_at': row[5],
                }
            return None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None

    @staticmethod
    def increment_wrong_attempts(session_token: str) -> int:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'UPDATE auth_sessions SET wrong_attempts = COALESCE(wrong_attempts, 0) + 1 WHERE session_token = %s',
                    (session_token,)
                )
                cursor.execute('SELECT wrong_attempts FROM auth_sessions WHERE session_token = %s', (session_token,))
                row = cursor.fetchone()
            return row[0] if row else 0
        except Exception as e:
            print(f"Error incrementing wrong attempts: {e}")
            return 0

    @staticmethod
    def reset_wrong_attempts(session_token: str) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'UPDATE auth_sessions SET wrong_attempts = 0 WHERE session_token = %s',
                    (session_token,)
                )
            return True
        except Exception as e:
            print(f"Error resetting wrong attempts: {e}")
            return False

    @staticmethod
    def update_session_progress(session_token: str, image_index: int) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'UPDATE auth_sessions SET current_image_index = %s WHERE session_token = %s',
                    (image_index, session_token)
                )
            return True
        except Exception as e:
            print(f"Error updating session progress: {e}")
            return False

    @staticmethod
    def update_image_start_time(session_token: str) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                # Use the application clock (datetime.now()) instead of MySQL NOW()
                # so the elapsed-time check in verify_click compares two values
                # from the same clock — avoids timezone mismatch bugs.
                cursor.execute(
                    'UPDATE auth_sessions SET image_started_at = %s WHERE session_token = %s',
                    (datetime.now(), session_token)
                )
            return True
        except Exception as e:
            print(f"Error updating image start time: {e}")
            return False

    @staticmethod
    def delete_session(session_token: str) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute('DELETE FROM auth_sessions WHERE session_token = %s', (session_token,))
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
