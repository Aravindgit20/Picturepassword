# Authentication Routes
# Login, register, authenticate, setup picture password

import secrets
import os
import base64
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from backend.user import User
from backend.auth_log import AuthLog
from backend.auth_session import AuthSession
from backend.password_reset_request import PasswordResetRequest
from backend.encryption_service import encryption_service
from backend.auth_service import auth_service
from backend.config import Config

auth_bp = Blueprint('auth', __name__)

def _user_image_dir(user_id):
    """Return the directory for storing a user's custom auth images"""
    # Two dirnames of the absolute path reach the project root (matching
    # backend/__init__.py). A third dirname resolves to the filesystem root,
    # which previously wrote custom images outside the static folder and 404'd.
    base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'frontend', 'static', 'images', 'user_images', str(user_id))
    os.makedirs(base, exist_ok=True)
    return base

def _get_auth_images_for_user(user_id):
    """Return auth image filenames for a user (custom if uploaded, else defaults)"""
    img_dir = _user_image_dir(user_id)
    images = []
    for i in range(4):
        fname = f'auth_{i}.jpg'
        if os.path.exists(os.path.join(img_dir, fname)):
            images.append(f'user_images/{user_id}/{fname}')
        else:
            images.append(Config.AUTH_IMAGES[i])
    return images


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        errors = auth_service.validate_registration(username, email, password)
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')

        password_hash = encryption_service.hash_password(password)

        if User.create_user(username, email, password_hash):
            flash('Registration successful! Please set up your picture password.', 'success')
            session['temp_username'] = username
            return redirect(url_for('auth.setup_picture_password'))
        else:
            flash('Username already exists! Please choose a different username.', 'error')
            return render_template('register.html')

    return render_template('register.html')


@auth_bp.route('/upload-setup-image', methods=['POST'])
def upload_setup_image():
    """Save a user's custom setup image to disk"""
    if 'temp_username' not in session:
        return jsonify({'success': False, 'message': 'Not in setup session'})

    user = User.get_user_by_username(session['temp_username'])
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'message': 'Invalid request data'})

    index = data.get('index')
    image_data = data.get('image_data', '')  # base64 data URL

    if index is None or not image_data:
        return jsonify({'success': False, 'message': 'Missing data'})

    # Validate index to prevent path traversal via crafted filenames (e.g. "../x")
    try:
        index = int(index)
    except (TypeError, ValueError):
        return jsonify({'success': False, 'message': 'Invalid image index'})
    if not 0 <= index <= 3:
        return jsonify({'success': False, 'message': 'Image index out of range'})

    try:
        # Strip data URL prefix
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]
        img_bytes = base64.b64decode(image_data)
        img_dir = _user_image_dir(user.id)
        fname = f'auth_{index}.jpg'
        with open(os.path.join(img_dir, fname), 'wb') as f:
            f.write(img_bytes)
        return jsonify({'success': True, 'filename': f'user_images/{user.id}/{fname}'})
    except Exception as e:
        print(f"Error saving image: {e}")
        return jsonify({'success': False, 'message': 'Failed to save image'})


@auth_bp.route('/setup-picture-password', methods=['GET', 'POST'])
def setup_picture_password():
    """Picture password setup"""
    if 'temp_username' not in session:
        flash('Please register first!', 'error')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({'success': False, 'message': 'Invalid request data'})
        coordinates = data.get('coordinates', [])

        if len(coordinates) != 4:
            return jsonify({'success': False, 'message': 'Please click on all 4 images'})

        user = User.get_user_by_username(session['temp_username'])
        if not user:
            return jsonify({'success': False, 'message': 'User not found'})

        # Use user-specific image names in coordinates
        auth_images = _get_auth_images_for_user(user.id)
        for i, coord in enumerate(coordinates):
            coord['image'] = auth_images[i]

        encrypted_coords = encryption_service.encrypt_coordinates(coordinates)
        if encrypted_coords and User.update_picture_password(user.id, encrypted_coords):
            session.pop('temp_username', None)
            return jsonify({'success': True, 'message': 'Picture password set successfully!'})
        else:
            return jsonify({'success': False, 'message': 'Failed to save picture password'})

    user = User.get_user_by_username(session['temp_username'])
    user_id = user.id if user else None
    auth_images = _get_auth_images_for_user(user_id) if user_id else Config.AUTH_IMAGES
    return render_template('setup_picture_password.html', auth_images=auth_images)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Picture password authentication"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()

        if not username:
            flash('Please enter your username!', 'error')
            return render_template('login.html')

        password = request.form.get('password', '').strip()
        if not password:
            flash('Password is required.', 'error')
            return render_template('login.html')

        user = User.get_user_by_username(username)
        if not user:
            flash('User not found!', 'error')
            return render_template('login.html')

        # Bug 1 fix: reject deactivated users
        if not user.is_active:
            flash('Account is deactivated. Contact an administrator.', 'error')
            return render_template('login.html')

        # Bug 3 fix: verify text password before starting picture auth
        if not encryption_service.verify_password(password, user.password_hash):
            flash('Invalid password.', 'error')
            return render_template('login.html')

        # Bug 9 fix: migrate legacy SHA-256 hash to bcrypt on successful login
        if not user.password_hash.startswith('$2'):
            new_hash = encryption_service.hash_password(password)
            User.update_password_hash(user.id, new_hash)

        # If picture password was reset by admin, redirect user to set a new one
        if not user.picture_password_data:
            flash('Your picture password has been reset. Please set up a new one.', 'warning')
            session['temp_username'] = username
            return redirect(url_for('auth.setup_picture_password'))

        session_token = secrets.token_urlsafe(32)
        if AuthSession.create_session(user.id, session_token):
            session['auth_session'] = session_token
            session['auth_user_id'] = user.id
            session['auth_username'] = username
            return redirect(url_for('auth.authenticate'))
        else:
            flash('Failed to start authentication session!', 'error')
            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/authenticate')
def authenticate():
    """Picture password authentication interface"""
    if 'auth_session' not in session:
        flash('Please start login process first!', 'error')
        return redirect(url_for('auth.login'))

    auth_session = AuthSession.get_session(session['auth_session'])
    if not auth_session:
        flash('Authentication session expired!', 'error')
        return redirect(url_for('auth.login'))

    user = User.get_user_by_username(session['auth_username'])
    auth_images = _get_auth_images_for_user(user.id) if user else Config.AUTH_IMAGES

    # Bug 13 fix: record server-side start time for this image
    AuthSession.update_image_start_time(session['auth_session'])

    return render_template('authenticate.html',
                           auth_images=auth_images,
                           current_image=auth_session['current_image_index'],
                           time_limit=Config.TIME_LIMIT_PER_IMAGE,
                           max_attempts=Config.MAX_WRONG_ATTEMPTS)


@auth_bp.route('/verify-click', methods=['POST'])
def verify_click():
    """Verify click coordinates during authentication"""
    if 'auth_session' not in session:
        return jsonify({'success': False, 'message': 'No active session'})

    auth_session = AuthSession.get_session(session['auth_session'])
    if not auth_session:
        return jsonify({'success': False, 'message': 'Session expired'})

    # Bug 13 fix: enforce server-side per-image time limit
    started = auth_session.get('image_started_at')
    if started:
        if isinstance(started, str):
            started = datetime.fromisoformat(started)
        elapsed = (datetime.now() - started).total_seconds()
        if elapsed > Config.TIME_LIMIT_PER_IMAGE:
            AuthSession.delete_session(session['auth_session'])
            session.pop('auth_session', None)
            session.pop('auth_user_id', None)
            session.pop('auth_username', None)
            return jsonify({'success': False, 'expired': True,
                            'message': 'Time limit exceeded. Please log in again.',
                            'redirect': url_for('auth.login')})

    click_data = request.get_json(silent=True)
    if not click_data:
        return jsonify({'success': False, 'message': 'Invalid request data'})
    x = click_data.get('x')
    y = click_data.get('y')
    x_pct = click_data.get('x_pct')
    y_pct = click_data.get('y_pct')
    image_name = click_data.get('image')

    user = User.get_user_by_username(session['auth_username'])
    if not user or not user.picture_password_data:
        return jsonify({'success': False, 'message': 'User data not found'})

    stored_coords = encryption_service.decrypt_coordinates(user.picture_password_data)
    if not stored_coords:
        return jsonify({'success': False, 'message': 'Invalid stored coordinates'})

    current_index = auth_session['current_image_index']
    auth_images = _get_auth_images_for_user(user.id)

    if current_index >= len(auth_images):
        return jsonify({'success': False, 'message': 'Authentication complete'})

    if auth_service.validate_click(stored_coords, x, y, image_name, current_index, x_pct, y_pct):
        next_index = current_index + 1
        AuthSession.update_session_progress(session['auth_session'], next_index)
        AuthSession.reset_wrong_attempts(session['auth_session'])
        # Reset server-side timer for the next image
        AuthSession.update_image_start_time(session['auth_session'])

        if next_index >= len(auth_images):
            AuthLog.log_attempt(user.id, True, request.remote_addr, request.headers.get('User-Agent'))
            AuthSession.delete_session(session['auth_session'])
            session.pop('auth_session', None)
            session.pop('auth_user_id', None)
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True, 'message': 'Authentication successful!',
                            'redirect': url_for('auth.dashboard')})
        else:
            return jsonify({'success': True, 'message': 'Correct! Continue to next image.',
                            'next_image': next_index})
    else:
        # Wrong click — increment attempt counter
        wrong_attempts = AuthSession.increment_wrong_attempts(session['auth_session'])
        remaining = Config.MAX_WRONG_ATTEMPTS - wrong_attempts

        if wrong_attempts >= Config.MAX_WRONG_ATTEMPTS:
            # Lock out — delete session
            AuthLog.log_attempt(user.id, False, request.remote_addr, request.headers.get('User-Agent'))
            AuthSession.delete_session(session['auth_session'])
            session.pop('auth_session', None)
            session.pop('auth_user_id', None)
            session.pop('auth_username', None)
            return jsonify({'success': False, 'locked': True,
                            'message': 'Too many wrong attempts. Please try again.',
                            'redirect': url_for('auth.login')})
        else:
            return jsonify({'success': False, 'message': f'Wrong location! {remaining} attempt(s) remaining.',
                            'wrong_attempts': wrong_attempts,
                            'remaining': remaining})


@auth_bp.route('/request-reset', methods=['GET', 'POST'])
def request_reset():
    """User requests a picture password reset (requires admin approval)"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        reason = request.form.get('reason', '').strip()

        user = User.get_user_by_username(username)
        if not user:
            flash('Username not found!', 'error')
            return render_template('request_reset.html')

        if PasswordResetRequest.has_pending_request(user.id):
            flash('You already have a pending reset request. Please wait for admin approval.', 'warning')
            return render_template('request_reset.html')

        if PasswordResetRequest.create_request(user.id, username, reason):
            return render_template('request_reset.html', submitted=True, username=username)
        else:
            flash('Failed to submit request. Please try again.', 'error')

    return render_template('request_reset.html', submitted=False)


@auth_bp.route('/timeout')
def timeout():
    """Handle authentication timeout"""
    if 'auth_session' in session:
        AuthSession.delete_session(session['auth_session'])
        session.pop('auth_session', None)
        session.pop('auth_user_id', None)
        session.pop('auth_username', None)

    flash('Authentication timed out! Please try again.', 'warning')
    return redirect(url_for('auth.login'))


@auth_bp.route('/dashboard')
def dashboard():
    """User dashboard after successful authentication"""
    if 'user_id' not in session:
        flash('Please log in first!', 'error')
        return redirect(url_for('auth.login'))

    from datetime import datetime
    user = User.get_user_by_id(session['user_id'])
    all_logs = AuthLog.get_user_logs(session['user_id'], 1000)
    recent_logs = all_logs[:10]
    successful_logins = sum(1 for l in all_logs if l['success'])
    last_login = all_logs[1] if len(all_logs) > 1 else None
    now = datetime.now().strftime('%A, %d %B %Y  %H:%M')

    return render_template('dashboard.html',
                           username=session.get('username'),
                           user=user,
                           logs=recent_logs,
                           successful_logins=successful_logins,
                           last_login=last_login,
                           now=now)


@auth_bp.route('/logout')
def logout():
    """Logout user — clear only user-auth keys so an admin session survives."""
    for key in ('user_id', 'username', 'auth_session', 'auth_user_id', 'auth_username', 'temp_username'):
        session.pop(key, None)
    flash('You have been logged out successfully!', 'success')
    return redirect(url_for('main.index'))
