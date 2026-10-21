# User Model - MySQL version

from typing import Optional, List
from pymysql import IntegrityError
from database.db_manager import DatabaseManager

class User:
    def __init__(self, id=None, username=None, email=None, password_hash=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.picture_password_data = None
        self.created_at = None
        self.is_active = True

    @staticmethod
    def _row_to_user(row):
        """Build a User object from a fetched row (shared by all lookups)."""
        user = User()
        user.id, user.username, user.email, user.password_hash, user.picture_password_data, _created_at, user.is_active = row
        user.created_at = _created_at.strftime('%Y-%m-%d %H:%M:%S') if _created_at and hasattr(_created_at, 'strftime') else _created_at
        return user

    @staticmethod
    def create_user(username: str, email: str, password_hash: str) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)',
                    (username, email, password_hash)
                )
            return True
        except IntegrityError:
            return False
        except Exception as e:
            print(f"Error creating user: {e}")
            return False

    @staticmethod
    def get_user_by_username(username: str) -> Optional['User']:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT id, username, email, password_hash, picture_password_data, created_at, is_active FROM users WHERE username = %s',
                    (username,)
                )
                row = cursor.fetchone()
            return User._row_to_user(row) if row else None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None

    @staticmethod
    def get_user_by_id(user_id: int) -> Optional['User']:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT id, username, email, password_hash, picture_password_data, created_at, is_active FROM users WHERE id = %s',
                    (user_id,)
                )
                row = cursor.fetchone()
            return User._row_to_user(row) if row else None
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None

    @staticmethod
    def update_picture_password(user_id: int, encrypted_coordinates: str) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'UPDATE users SET picture_password_data = %s WHERE id = %s',
                    (encrypted_coordinates, user_id)
                )
            return True
        except Exception as e:
            print(f"Error updating picture password: {e}")
            return False

    @staticmethod
    def update_password_hash(user_id: int, new_hash: str) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'UPDATE users SET password_hash = %s WHERE id = %s',
                    (new_hash, user_id)
                )
            return True
        except Exception as e:
            print(f"Error updating password hash: {e}")
            return False

    @staticmethod
    def get_all_users() -> List['User']:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT id, username, email, password_hash, picture_password_data, created_at, is_active FROM users ORDER BY created_at DESC'
                )
                rows = cursor.fetchall()
            return [User._row_to_user(row) for row in rows]
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []

    @staticmethod
    def delete_user(user_id: int) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                # Delete all related records first (foreign key order matters)
                cursor.execute('DELETE FROM password_reset_requests WHERE user_id = %s', (user_id,))
                cursor.execute('DELETE FROM auth_logs WHERE user_id = %s', (user_id,))
                cursor.execute('DELETE FROM auth_sessions WHERE user_id = %s', (user_id,))
                cursor.execute('DELETE FROM users WHERE id = %s', (user_id,))
            return True
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False

    @staticmethod
    def reset_picture_password(user_id: int) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute('UPDATE users SET picture_password_data = NULL WHERE id = %s', (user_id,))
            return True
        except Exception as e:
            print(f"Error resetting picture password: {e}")
            return False

    @staticmethod
    def toggle_user_status(user_id: int) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute('UPDATE users SET is_active = NOT is_active WHERE id = %s', (user_id,))
            return True
        except Exception as e:
            print(f"Error toggling user status: {e}")
            return False
