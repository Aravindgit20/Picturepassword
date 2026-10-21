# Picture Password Authentication System

A Flask web application implementing picture-based authentication using spatial memory and visual recognition.

## Quick Start

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Start MySQL** and make sure it's running on localhost:3306.

**3. Set environment variables** (optional — defaults shown):
```
set MYSQL_HOST=localhost
set MYSQL_USER=root
set MYSQL_PASSWORD=your_mysql_password
set MYSQL_DATABASE=picture_password_auth
set ADMIN_PASSWORD=admin123
set SECRET_KEY=your-secret-key
```

**4. Run the app**
```bash
python app.py
```

**Access Points:**
- Main App: http://localhost:8000
- Admin Panel: http://localhost:8000/admin (password: `admin123` by default)

## How It Works

1. **Register** — create account with username, email, and password
2. **Setup Picture Password** — click a memorable spot on each of 4 images
3. **Login** — enter username + password, then click the same spots on the images
4. **Security** — 2 wrong clicks locks the session; 10-second timer per image

## Architecture

```
project/
├── backend/
│   ├── config.py          # App configuration
│   ├── models/            # Database models (User, AuthSession, AuthLog, PasswordResetRequest)
│   ├── routes/            # Flask blueprints (auth, admin, main)
│   └── services/          # Auth logic and encryption (bcrypt + Fernet)
├── database/
│   ├── db_manager.py      # MySQL connection via PyMySQL
│   └── encryption.key     # Fernet encryption key (auto-generated)
├── frontend/
│   ├── css/               # Stylesheets
│   ├── js/                # JavaScript
│   ├── images/            # Auth images, decoys, user uploads
│   └── *.html             # Jinja2 templates
├── tests/                 # pytest test suite
├── app.py                 # Entry point
└── requirements.txt
```

## Tech Stack

- **Backend**: Flask + PyMySQL
- **Database**: MySQL
- **Security**: bcrypt (passwords) + Fernet (coordinates) + Flask-WTF (CSRF)
- **Frontend**: Bootstrap 5, Vanilla JS

## Testing

```bash
pytest tests/ -v
```
