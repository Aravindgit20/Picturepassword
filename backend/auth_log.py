# Authentication Log Model - MySQL version

from typing import List, Dict
from database.db_manager import DatabaseManager

def _fmt(dt):
    """Convert datetime object to string safely"""
    if dt is None:
        return None
    return dt.strftime('%Y-%m-%d %H:%M:%S') if hasattr(dt, 'strftime') else str(dt)

class AuthLog:

    @staticmethod
    def log_attempt(user_id: int, success: bool, ip_address: str = None, user_agent: str = None) -> bool:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'INSERT INTO auth_logs (user_id, success, ip_address, user_agent) VALUES (%s, %s, %s, %s)',
                    (user_id, success, ip_address, user_agent)
                )
            return True
        except Exception as e:
            print(f"Error logging authentication attempt: {e}")
            return False

    @staticmethod
    def get_user_logs(user_id: int, limit: int = 50) -> List[Dict]:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT attempt_time, success, ip_address FROM auth_logs WHERE user_id = %s ORDER BY attempt_time DESC LIMIT %s',
                    (user_id, limit)
                )
                rows = cursor.fetchall()
            return [{'attempt_time': _fmt(r[0]), 'success': bool(r[1]), 'ip_address': r[2]} for r in rows]
        except Exception as e:
            print(f"Error getting user logs: {e}")
            return []

    @staticmethod
    def get_all_logs(limit: int = 100) -> List[Dict]:
        try:
            with DatabaseManager.get_cursor() as cursor:
                cursor.execute(
                    'SELECT al.attempt_time, al.success, al.ip_address, u.username, al.user_id FROM auth_logs al JOIN users u ON al.user_id = u.id ORDER BY al.attempt_time DESC LIMIT %s',
                    (limit,)
                )
                rows = cursor.fetchall()
            return [{'attempt_time': _fmt(r[0]), 'success': bool(r[1]), 'ip_address': r[2], 'username': r[3], 'user_id': r[4]} for r in rows]
        except Exception as e:
            print(f"Error getting all logs: {e}")
            return []
