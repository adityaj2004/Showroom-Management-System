# Northstar — Showroom OS

A new, independently implemented showroom management system inspired by the *functional requirements* of the public [Excelr Project – Tarandeep Singh](https://gitlab.com/taran2312/Excelr_Project-Tarandeep-Singh). Original source code, artwork and branding were **not** copied. The original repository did not display a reuse license during review.

![Modules](https://img.shields.io/badge/modules-7-4F46E5) ![Backend](https://img.shields.io/badge/API-FastAPI-059669) ![DB](https://img.shields.io/badge/DB-SQLite-0369A1)

## What is implemented

- **Modern responsive admin UI:** dark navigation, KPI dashboards, revenue trend, sales activity, global shortcuts, searchable paginated tables, modal forms, mobile navigation, accessible buttons and form labels.
- **Inventory:** vehicles across showrooms, VIN uniqueness, status, filters, mileage, price, location, edit/delete safeguards.
- **CRM:** customer records, search, edit, activity-linked deletion safeguards.
- **Sales:** create pending sale ⇒ atomically reserve vehicle; manager completion ⇒ sold; cancellation ⇒ available; edit pending sale; invoice IDs; discounts; payment method; approval permissions.
- **Test drives:** schedule, edit, complete, no-show, cancel, feedback; one-hour booking conflict checks; unavailable vehicle blocked on create **and edit**.
- **Showrooms:** create/edit/delete locations; prevent deletion while stock assigned.
- **Staff:** Admin / Manager / Sales roles, invite-create members, deactivation, safeguards against deleting the final admin; public registration disabled by default.
- **Account:** login, logout, profile, password change and session revocation.
- **Security:** Argon2id password hashes, 12-hour random opaque session token in HttpOnly SameSite=Strict cookies, server-side session revocation, CSRF header checks, role authorization **on the API**, input schema validation, security headers / CSP, no default credentials, limited sign-in attempts, audit event history, and origin checks.
- **Testing:** API and authorization / sales-transition / booking-conflict tests in `tests/`.

### Technology

Python 3.11+, FastAPI, SQLAlchemy, SQLite, plain modern HTML/CSS/JavaScript. **This intentionally differs from the reference project's Spring Boot/React/MySQL stack.** Its advantage is fast installation, an entirely self-hosted single-process application, and easier verification. Database persists across restarts. No external APIs, CDN, or JS package installation needed.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env           # Windows: copy .env.example .env
python run.py
```

Visit **http://127.0.0.1:8000**. On first launch, look in the terminal for the random **NORTHSTAR FIRST-ADMIN SETUP TOKEN**. Use that token on the initial setup screen to create your own administrator password (minimum 12 characters with lowercase, uppercase, and a digit). You can optionally preload demo data (3 showrooms, 12 vehicles, 6 customers, 5 sales, 4 test drives). The token is invalid once the first administrator is created.

After login, the application uses one origin for both its UI and API; **no separate frontend process** is necessary. Your SQLite database is at `data/showroom.db` (excluded from the ZIP).

### Using Docker

```bash
cp .env.example .env
# Change HOST in .env if needed; Compose sets the correct container bind host.
docker compose up --build
```

Open http://127.0.0.1:8000. The database persists in the named Docker volume.

### Run tests

```bash
pip install -r requirements-dev.txt
pytest -q
# Optional UI smoke tests with Node.js 20+ (no npm packages required):
node --test tests/ui.test.cjs
```

## Key permissions

| Action | ADMIN | MANAGER | SALES |
| --- | :---: | :---: | :---: |
| Read business information | ✓ | ✓ | ✓ |
| Create/edit customers, test drives, pending sales | ✓ | ✓ | ✓ |
| Create/edit vehicles, close sales, delete customers/test drives | ✓ | ✓ | — |
| View staff directory | ✓ | ✓ | — |
| Manage showrooms and staff, delete non-completed sales | ✓ | — | — |

## API routes

`GET /api/health`, `GET /api/setup-status` are public. `POST /api/auth/bootstrap` sets up the first administrator. `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`, and `PUT /api/auth/change-password` manage authentication. `POST /api/auth/register` is disabled by default. Logged-in endpoints: `/api/dashboard`, `/api/vehicles`, `/api/customers`, `/api/sales`, `/api/test-drives`, `/api/showrooms`, `/api/users`, `/api/audit`. Resource endpoints support listing with `q`, `page`, `limit`, GET/POST for collections, PUT/DELETE for `/{id}`, and PATCH status transitions on vehicles, sales and test drives. Listing responses return `{items, total, page, pages, limit}`.

Mutating authenticated requests must supply an `X-CSRF-Token` header obtained from `/api/auth/me` or login. Cookies are sent automatically on same-origin calls.

## Deployment and important limitations

1. **Use HTTPS**, set `COOKIE_SECURE=true`, set `ALLOWED_HOSTS` to your domain, and use a properly configured reverse proxy and firewall. Never expose an unauthenticated initial setup page to the internet; create the first administrator locally or set `BOOTSTRAP_TOKEN` to a long random value. Keep `.env` private.
2. SQLite is appropriate for local / modest office operation; a high-traffic multi-instance deployment should use a server DB, DB migrations, transactional row-level locking, and shared rate-limit storage. The default SQLite write lock plus conditional updates prevent simultaneous claims on one vehicle within a single database.
3. Authentication is cookie based, not JWT. There is no email delivery, password reset, SMS, document uploads, PDF invoicing, accounting or payment processing integration.
4. Test-drive collision checks are performed at the application layer. For heavy concurrent multi-worker scheduling, add database-level exclusion constraints or equivalent serializable transaction / locking protections.
5. The intentionally fictional demonstration dataset has no business or customer records from the reference repository. Delete it before production usage.
6. The UI was smoke-checked in Chromium using mocked API responses (desktop, mobile, and create-vehicle form). The Python API is tested independently, but the environment blocked navigation to the live local server, so full browser-to-server E2E testing is not claimed. This is a working foundation, **not a certified production release**; perform complete browser-to-server E2E testing, penetration testing, backups / restore drills, multi-user load testing and deployment QA before using it for real business.
