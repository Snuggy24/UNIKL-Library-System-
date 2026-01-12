# UNIKL Library Management System

A secure library management system built with Django, implementing OWASP security best practices.

## Features

- **User Registration & Login** - Secure email-based authentication with audit logging
- **Role-Based Access Control (RBAC)** - Admin, Librarian, and Student roles
- **Book Management** - Browse, search, borrow, return, and reserve books
- **User Profile** - View and edit personal information
- **Audit Log** - Admin-only view of login attempts and system activities

## Security Features (OWASP Compliant)

| Security Requirement | Implementation |
|---------------------|----------------|
| Input Validation | Django ORM (SQL injection prevention), form validators |
| Authentication | Argon2 password hashing, strong password rules |
| Session Security | HttpOnly cookies, session timeout, CSRF protection |
| Access Control | RBAC with role checks, no IDOR vulnerabilities |
| Error Handling | Custom error pages (400, 403, 404, 500) - no stack traces |
| Sensitive Data | Password hashing, environment variables for secrets |
| File Upload | MIME validation, size limits, secure filenames |
| Logging | Security event logging without sensitive data |
| Output Encoding | Django template auto-escaping (XSS prevention) |

## Installation

### Prerequisites
- Python 3.10+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd library_management
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   # Copy example file
   cp .env.example .env
   
   # Edit .env and set your SECRET_KEY
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (Admin)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Main Site: http://127.0.0.1:8000/
   - Admin Panel: http://127.0.0.1:8000/admin/

## Repository Structure

```text
library_management/
├── accounts/           # User authentication, profiles, & audit logs
│   ├── migrations/     # Database migrations
│   ├── templates/      # App-specific templates
│   ├── admin.py        # Admin panel configuration
│   ├── models.py       # User & AuditLog models
│   ├── views.py        # Auth & Profile views
│   └── forms.py        # Crispy forms definitions
├── books/              # Book management (CRUD)
│   ├── migrations/     # Database migrations
│   ├── templates/      # App-specific templates
│   ├── admin.py        # Admin panel configuration
│   ├── models.py       # Book, Borrowing, Reservation models
│   └── views.py        # Book catalog & transaction views
├── library_project/    # Project configuration
│   ├── settings.py     # Main settings (Security, Apps, DB)
│   ├── urls.py         # Main URL routing
│   ├── validators.py   # Custom security validators
│   └── wsgi.py         # WSGI entry point
├── templates/          # Global templates & Error pages
│   ├── admin/          # Admin panel overrides
│   ├── errors/         # Custom 404, 500, 403 pages
│   └── base.html       # Main application layout
├── static/             # Static assets (CSS, JS, Images)
├── media/              # User uploads (Profile pics, Book covers)
├── screenshots/        # Documentation screenshots
├── logs/               # Security audit logs
├── .env.example        # Environment variables template
├── requirements.txt    # Python dependencies list
├── manage.py           # Django management script
├── README.md           # Project documentation
└── TECHNICAL_REPORT.md # Detailed security report
```

## User Roles

| Role | Permissions |
|------|-------------|
| Admin | Full access, manage users, view audit logs, access admin panel |
| Librarian | Manage books, process loans |
| Student | Browse books, borrow/return, manage profile |

## API Endpoints

### Authentication
- `GET /accounts/login/` - Login page
- `GET /accounts/register/` - Registration page
- `GET /accounts/logout/` - Logout
- `GET /accounts/profile/` - View profile
- `GET /accounts/profile/edit/` - Edit profile
- `GET /accounts/audit-log/` - Audit log (Admin only)

### Books
- `GET /` - Book listing
- `GET /book/<id>/` - Book detail
- `POST /book/<id>/borrow/` - Borrow book
- `POST /borrow/<id>/return/` - Return book
- `POST /book/<id>/reserve/` - Reserve book
- `GET /my-books/` - User's borrowed books

## Testing

### Security Testing Tools
- **Static Analysis**: `bandit -r .` (install with `pip install bandit`)
- **Dependency Scanning**: `safety check` (install with `pip install safety`)
- **Dynamic Testing**: OWASP ZAP

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Set a strong `SECRET_KEY`
3. Enable HTTPS/TLS
4. Configure proper `ALLOWED_HOSTS`
5. Use a production WSGI server (e.g., Gunicorn)

## Dependencies
- **Backend Framework**: Django 6.0
- **Frontend**: Bootstrap 5.3, Django Templates
- **Security**: 
  - `argon2-cffi` (Password Hashing)
  - `python-dotenv` (Configuration)
  - `python-magic-bin` (File Validation)
- **Utilities**: `Pillow` (Image processing)
- **Forms**: `django-crispy-forms`, `crispy-bootstrap5`

## System Screenshots

| Page | Screenshot |
|------|------------|
| **Home Page** | ![Home Page](library_management/home_page.png) |
| **Login Page** | ![Login Page](library_management/login_page.png) |
| **Admin Dashboard** | ![Admin Dashboard](library_management/admin_dashboard.png) |
| **User Profile** | ![User Profile](library_management/user_profile.png) |
> **Note**: Please save screenshots of your running application into the `screenshots/` folder with the filenames above to populate this section.

## License

This project is for educational purposes - UNIKL Secure Software Development course.
