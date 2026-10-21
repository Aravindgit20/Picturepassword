# Main Application Entry Point
# Picture Password Authentication System

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Initialize database (creates tables if they don't exist)
from database import db_manager

# Create Flask app using factory pattern
from backend import create_app

app = create_app()

if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs('frontend/template', exist_ok=True)
    os.makedirs('frontend/static/css', exist_ok=True)
    os.makedirs('frontend/static/js', exist_ok=True)
    os.makedirs('frontend/static/images', exist_ok=True)

    print("Starting Picture Password Authentication System")
    print("Available at: http://localhost:8000")
    print("Admin panel: http://localhost:8000/admin")

    app.run(debug=True, host='127.0.0.1', port=8000)
