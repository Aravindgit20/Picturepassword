# Authentication Service
# Handles authentication logic and validation

from backend.config import Config
from backend.encryption_service import encryption_service

class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def validate_click(stored_coords, click_x, click_y, image_name, current_index, click_x_pct=None, click_y_pct=None):
        """
        Validate if a click matches stored coordinates.
        Uses percentage-based matching when available (scale-independent),
        falls back to pixel-based matching with tolerance.
        """
        if current_index >= len(stored_coords):
            return False
        
        expected = stored_coords[current_index]
        
        # Image name must match
        if image_name != expected['image']:
            return False
        
        # Prefer percentage-based comparison (scale-independent, more accurate)
        if click_x_pct is not None and click_y_pct is not None and 'x_pct' in expected:
            pct_tolerance = 0.05  # 5% of image dimension
            return (abs(click_x_pct - expected['x_pct']) <= pct_tolerance and
                    abs(click_y_pct - expected['y_pct']) <= pct_tolerance)
        
        # Fallback: pixel tolerance
        tolerance = Config.CLICK_TOLERANCE
        # Guard against missing pixel coordinates (e.g. client sent only pct)
        # to avoid a TypeError comparing None to an int.
        if click_x is None or click_y is None or 'x' not in expected or 'y' not in expected:
            return False
        return (abs(click_x - expected['x']) <= tolerance and
                abs(click_y - expected['y']) <= tolerance)
    
    @staticmethod
    def validate_email(email):
        """Basic email validation"""
        return '@' in email and '.' in email
    
    @staticmethod
    def validate_registration(username, email, password):
        """Validate registration data"""
        errors = []
        
        if not username or not username.strip():
            errors.append('Username is required')
        
        if not email or not email.strip():
            errors.append('Email is required')
        elif not AuthService.validate_email(email):
            errors.append('Invalid email format')
        
        if not password or not password.strip():
            errors.append('Password is required')
        
        return errors


# Global instance
auth_service = AuthService()
