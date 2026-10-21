# Password Reset Request Model - MySQL version

from typing import Optional, List
from database.db_manager import DatabaseManager

class PasswordResetRequest:

    @staticmethod
    def create_request(user_id: int, username: str, reason: str = '') -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM password_reset_requests WHERE user_id = %s AND status = 'pending'",
                    (user_id,)
                )
                if cursor.fetchone():
                    return False
                cursor.execute(
                    'INSERT INTO password_reset_requests (user_id, username, reason) VALUES (%s, %s, %s)',
                    (user_id, username, reason)
                )
            return True
        except Exception as e:
            print(f"Error creating reset request: {e}")
            return False

    @staticmethod
    def get_pending_requests() -> List[dict]:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id, user_id, username, reason, requested_at FROM password_reset_requests WHERE status = 'pending' ORDER BY requested_at ASC"
                )
                rows = cursor.fetchall()
            return [{'id': r[0], 'user_id': r[1], 'username': r[2], 'reason': r[3],
                     'requested_at': r[4].strftime('%Y-%m-%d %H:%M:%S') if r[4] and hasattr(r[4], 'strftime') else r[4]} for r in rows]
        except Exception as e:
            print(f"Error getting pending requests: {e}")
            return []

    @staticmethod
    def approve_request(request_id: int) -> Optional[int]:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    "SELECT user_id FROM password_reset_requests WHERE id = %s AND status = 'pending'",
                    (request_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                user_id = row[0]
                cursor.execute(
                    "UPDATE password_reset_requests SET status = 'approved', resolved_at = NOW() WHERE id = %s",
                    (request_id,)
                )
            return user_id
        except Exception as e:
            print(f"Error approving request: {e}")
            return None

    @staticmethod
    def deny_request(request_id: int) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    "UPDATE password_reset_requests SET status = 'denied', resolved_at = NOW() WHERE id = %s",
                    (request_id,)
                )
            return True
        except Exception as e:
            print(f"Error denying request: {e}")
            return False

    @staticmethod
    def has_pending_request(user_id: int) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM password_reset_requests WHERE user_id = %s AND status = 'pending'",
                    (user_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            print(f"Error checking pending request: {e}")
            return False
