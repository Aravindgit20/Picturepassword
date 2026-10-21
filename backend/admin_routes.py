# Admin Routes
# Admin dashboard and user management

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from backend.user import User
from backend.auth_log import AuthLog
from backend.password_reset_request import PasswordResetRequest
from backend.config import Config

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Decorator to protect admin routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to access the admin panel.', 'warning')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if session.get('admin_logged_in'):
        return redirect(url_for('admin.admin'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == Config.ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.admin'))
        else:
            flash('Incorrect admin password!', 'error')
    
    return render_template('admin.html', view='login')


@admin_bp.route('/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Logged out of admin panel.', 'success')
    return redirect(url_for('admin.admin_login'))


@admin_bp.route('/')
@admin_required
def admin():
    """Admin dashboard"""
    users = User.get_all_users()
    logs = AuthLog.get_all_logs(50)
    reset_requests = PasswordResetRequest.get_pending_requests()
    return render_template('admin.html', view='dashboard', users=users, logs=logs, reset_requests=reset_requests)


@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    if User.delete_user(user_id):
        flash('User deleted successfully!', 'success')
    else:
        flash('Failed to delete user!', 'error')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/reset-password/<int:user_id>', methods=['POST'])
@admin_required
def admin_reset_password(user_id):
    if User.reset_picture_password(user_id):
        flash('Picture password reset successfully! User needs to set up a new one.', 'success')
    else:
        flash('Failed to reset picture password!', 'error')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/approve-reset/<int:request_id>', methods=['POST'])
@admin_required
def approve_reset(request_id):
    user_id = PasswordResetRequest.approve_request(request_id)
    if user_id and User.reset_picture_password(user_id):
        flash('Reset request approved. User can now set up a new picture password.', 'success')
    else:
        flash('Failed to approve reset request!', 'error')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/deny-reset/<int:request_id>', methods=['POST'])
@admin_required
def deny_reset(request_id):
    if PasswordResetRequest.deny_request(request_id):
        flash('Reset request denied.', 'success')
    else:
        flash('Failed to deny reset request!', 'error')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/toggle-status/<int:user_id>', methods=['POST'])
@admin_required
def admin_toggle_status(user_id):
    if User.toggle_user_status(user_id):
        flash('User status updated successfully!', 'success')
    else:
        flash('Failed to update user status!', 'error')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/user-details/<int:user_id>')
@admin_required
def admin_user_details(user_id):
    user = User.get_user_by_id(user_id)
    if not user:
        flash('User not found!', 'error')
        return redirect(url_for('admin.admin'))
    
    user_logs = AuthLog.get_user_logs(user_id, 100)
    
    cued_points = None
    if user.picture_password_data:
        from backend.encryption_service import encryption_service
        cued_points = encryption_service.decrypt_coordinates(user.picture_password_data)
    
    return render_template('admin.html', view='user_details', user=user, logs=user_logs, cued_points=cued_points, click_tolerance=Config.CLICK_TOLERANCE)
