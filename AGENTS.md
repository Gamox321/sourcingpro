# SourcingPro — Project Conventions

## Stack
- **Framework:** Django 5.2
- **Database:** PostgreSQL 17
- **Frontend:** Django Templates + HTMX + Bootstrap 5 (SB Admin 2)
- **Auth:** Custom User model (email as username), extends django.contrib.auth

## Project Structure
```
sourcingpro/
├── config/              # Django project settings
├── apps/
│   ├── accounts/        # Auth, Users, Roles
│   ├── audit/           # Audit log (bitacora)
│   ├── clients/         # Clients & Cost Centers
│   ├── inventory/       # Assets, Types, Assignments
│   ├── kanban/          # Kanban board
│   ├── notifications/   # Internal + email notifications
│   ├── processes/       # 4 process types + Tasks
│   └── workers/         # Worker registry
├── static/              # Global static files
├── templates/           # Global templates
├── media/               # User uploads
├── manage.py
└── requirements.txt
```

## Commands
```powershell
# Activate venv
.\venv\Scripts\activate

# Run dev server
& ".\venv\Scripts\python.exe" manage.py runserver

# Make migrations
& ".\venv\Scripts\python.exe" manage.py makemigrations <app_name>

# Apply migrations
& ".\venv\Scripts\python.exe" manage.py migrate

# Bootstrap admin
& ".\venv\Scripts\python.exe" manage.py bootstrap_admin

# Seed clients & cost centers
& ".\venv\Scripts\python.exe" manage.py seed_clients

# Seed notification configs (15 events × 2 channels)
& ".\venv\Scripts\python.exe" manage.py seed_notifications

# Seed demo data (users, workers, processes, assets)
& ".\venv\Scripts\python.exe" manage.py seed_demo

# Full bootstrap sequence (order matters!)
# 1. & ".\venv\Scripts\python.exe" manage.py bootstrap_admin
# 2. & ".\venv\Scripts\python.exe" manage.py seed_clients
# 3. & ".\venv\Scripts\python.exe" manage.py seed_notifications
# 4. & ".\venv\Scripts\python.exe" manage.py seed_demo

# Run checks
& ".\venv\Scripts\python.exe" manage.py check

# Shell
& ".\venv\Scripts\python.exe" manage.py shell
```

## Conventions
- All apps live under `apps/` package with `apps.` prefix in INSTALLED_APPS
- Model db_table matches DDL table names (e.g., `usuario`, `rol`, `proceso`)
- All text in Spanish (admin, validation messages, templates)
- Integer PKs (no UUIDs)
- Manual state machine: CharField with choices + clean() validation
- Audit logging via Django signals on tracked models
- Jefatura role scoped to assigned cost centers only
- Session expiry: hard 8h cut-off (SESSION_SAVE_EVERY_REQUEST=False)
- Login field: email (username field removed)

## Roles
| Codename | Display Name |
|---|---|
| administrador | Administrador |
| rrhh | RRHH |
| jefatura | Jefatura |
| ti | TI |
| prevencion | Prevención de Riesgos |
| finanzas | Finanzas |
| logistica | Logística |

## Key Decisions
1. Email-based login (no username field)
2. M2M User-Role via through model (UserRole)
3. Password validators: 8+ chars, upper, lower, digit, special
4. Failed login attempts tracked but never block (progressive warning)
5. Password reset link valid for 24h, single use
6. Temporary password forced change on first login
7. SB Admin 2 template for admin layout
8. Console email backend in dev, SMTP in production (.env)
