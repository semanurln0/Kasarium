# For Developers

Setup, testing, and deployment guide for Kasarium.

## Project Layout

```
project_codes/
  django/           # Django project (kasarium settings, manage.py)
  frontend/         # Static files, templates
  scripts/          # Data import and utilities
  tests/            # Test suite (pytest)
```

## Local Development Setup

### 1. Environment

Create and activate virtual environment:

```powershell
python -m venv .venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Requirements

Install the project dependencies from `requirements.txt`:

```powershell
pip install -r requirements.txt
```

**Requirements List:**

| Package         | Version    | Purpose                   |
| --------------- | ---------- | ------------------------- |
| Django          | >=4.2,<5.0 | Web framework             |
| pandas          | >=2.1      | Data processing (Phase 1) |
| openpyxl        | >=3.1      | Excel file handling       |
| python-dateutil | >=2.9      | Date utilities            |
| Pillow          | >=12.0     | Image handling            |
| psycopg2-binary | >=2.9      | PostgreSQL adapter        |
| python-dotenv   | >=1.0      | Environment variables     |
| whitenoise      | >=6.6      | Static files serving      |
| gunicorn        | >=21.2     | Production WSGI server    |
| pytest          | (latest)   | Test runner               |
| pytest-django   | >=4.12     | Django test integration   |

**Note:** `requirements.txt` is the source of truth for local and CI installs.

### 3. Database Setup

Run migrations:

```powershell
python project_codes\django\manage.py migrate --settings=kasarium.settings.dev
```

### 4. Run Tests

Set PYTHONPATH and run pytest:

```powershell
cmd /c "set PYTHONPATH=%CD%\project_codes\django&& .venv\Scripts\python.exe -m pytest -q"
```

Expected: **112 tests pass**.

### 5. Run Development Server

```powershell
python run.py
```

Browser opens automatically at `http://127.0.0.1:8000`.

### 6. Local Validation Summary

The current local workflow is verified with:

```powershell
python P2_main_project.py --check
python project_codes\django\manage.py check --settings=kasarium.settings.dev
pytest project_codes\tests -q
```

Expected: all checks pass on localhost with the seeded SQLite dev database.

## Key Commands

- **Check environment:** `python P2_main_project.py --check`
- **Import Phase 1 data:** `python project_codes\django\manage.py import_phase1_data --settings=kasarium.settings.dev`
- **Django shell:** `python project_codes\django\manage.py shell --settings=kasarium.settings.dev`
- **Create superuser:** `python project_codes\django\manage.py createsuperuser --settings=kasarium.settings.dev`

## Contributing

1. Create a feature branch from `main`.
2. Test changes locally: `pytest` must pass (112/112).
3. Update `docs/CHECKLIST.md` if adding new planned features.
4. Include test results in pull request description.
5. Keep changes focused; coordinate with maintainers for major refactors.

## Settings

- **Dev:** `kasarium.settings.dev` (SQLite, DEBUG=True)
- **Test:** `kasarium.settings.test` (SQLite :memory:, for pytest)
- **Prod:** `kasarium.settings.prod` (Postgres, gunicorn, whitenoise)

---



## Production Deployment

### Required Environment Variables

| Variable          | Description                                                      | Example                                     |
| ----------------- | ---------------------------------------------------------------- | ------------------------------------------- |
| `SECRET_KEY`    | Django secret key (long random string)                           | `django-secret-...`                       |
| `DEBUG`         | Must be `False` in production                                  | `False`                                   |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames                                | `yourdomain.com,www.yourdomain.com`       |
| `DB_NAME`       | PostgreSQL database name                                         | `kasarium`                                |
| `DB_USER`       | PostgreSQL user                                                  | `kasarium`                                |
| `DB_PASSWORD`   | PostgreSQL password                                              | `strongpassword`                          |
| `DB_HOST`       | PostgreSQL host                                                  | `localhost`                               |
| `DB_PORT`       | PostgreSQL port                                                  | `5432`                                    |
| `DATABASE_URL`  | (Optional) Full Postgres URL (overrides DB_* vars on Render.com) | `postgresql://user:pass@host:5432/dbname` |

Set these in a `.env` file or as environment variables.

### Deploy Steps

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set settings module
$Env:DJANGO_SETTINGS_MODULE = 'kasarium.settings.prod'

# 3. Run database migrations
python project_codes\django\manage.py migrate

# 4. Seed roles (one-time, idempotent)
python project_codes\django\manage.py seed_roles

# 5. Collect static files
python project_codes\django\manage.py collectstatic --noinput

# 6. Create a superuser (first deploy only)
python project_codes\django\manage.py createsuperuser
```

### Running the Application Server

**Linux/macOS (gunicorn):**

```bash
gunicorn kasarium.wsgi:application --bind 0.0.0.0:8000 --workers 4 --chdir project_codes/django
```

**Windows (waitress):**

> **Note:** Gunicorn is not supported on Windows. Use waitress instead.

```powershell
pip install waitress
waitress-serve --port=8000 --call kasarium.wsgi:application
```

### Importing Phase 1 Data (Production)

```powershell
# Generate merged CSV
python P1_database_check.py

# Import into production database (idempotent)
$Env:DJANGO_SETTINGS_MODULE = 'kasarium.settings.prod'
python project_codes\django\manage.py import_phase1_data
```

### Deployment on Render.com

1. Push code to `main` or create a release branch.
2. Render auto-deploys via webhook.
3. Set environment variables in Render dashboard (SECRET_KEY, ALLOWED_HOSTS, DATABASE_URL, etc.).
4. Render runs migrations and collectstatic automatically (configure in `render.yaml` if needed).

### Online Shop (Production)

The shop is available at `/shop/`. Customers can:

- Browse catalog anonymously
- Add items to session-based cart
- Register/login with email to place Cash-on-Delivery orders
- View order history at `/shop/orders/`

Admin/Staff users are blocked from customer-facing views by role-based permissions.
