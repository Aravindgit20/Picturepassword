# Backend Package
# Picture Password Authentication System

import os
import sys
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from backend.config import Config

csrf = CSRFProtect()

def create_app():
    """Application factory pattern"""
    # Resolve correct base dir whether frozen or not
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    template_dir = os.path.join(base, 'frontend', 'template')
    static_dir = os.path.join(base, 'frontend', 'static')

    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir)

    app.config.from_object(Config)

    # Register blueprints
    from backend.main_routes import main_bp
    from backend.auth_routes import auth_bp
    from backend.admin_routes import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Bug 10 fix: enable CSRF protection on all state-changing forms
    csrf.init_app(app)

    return app
