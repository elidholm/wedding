# Copilot Instructions

Guidance for GitHub Copilot (and other AI coding agents) working in this
repository. Follow these conventions for every change.

## What This Project Is

A Flask + Jinja web application acting as the central hub for a wedding.
Guests get a personal QR code (on their invite) linking to a unique RSVP page
identified by a token/slug, e.g. `/rsvp/<token>`. The site also hosts day-of
information (schedule, food/menu, seating, conversation-starter questions) and
a "digital disposable camera" photo vault feature used at the reception (each
guest gets a limited number of photo "shots").

## Tech Stack & Constraints

- **Backend & frontend**: Python + Flask, server-rendered.
- **Templating**: Jinja2. Avoid heavy JS frameworks — plain templates + minimal
  CSS/JS unless a feature genuinely requires more.
- **Dependency & project management**: [uv](https://docs.astral.sh/uv/) only.
  Dependencies live in `pyproject.toml` (+ `uv.lock`). Never use `pip install`,
  `venv`, or `requirements.txt` directly — always go through `uv`.
- **Configuration**: read from environment variables via a `.env` file
  (loaded with `python-dotenv`) and centralized in `app/config.py`'s
  `AppConfig` (a pydantic `BaseModel`). `.env` itself is gitignored — never
  commit real values. `AppConfig` uses lowercase field names, so `create_app`
  copies each field into `app.config[...]` under the matching uppercase key
  (Flask's `from_object()` only picks up uppercase attributes, so it can't be
  used directly here).
- **Data storage**: no real database yet. Use in-memory Python data structures
  behind a small data-access layer (see below) so it's a localized swap later.
  Do not introduce a DB/ORM unless explicitly instructed.
- **Photo uploads**: no real file storage yet. Track photo-vault state
  (remaining count, "taken" status) as metadata only — do not implement real
  upload/storage unless explicitly instructed.

## Project Structure

Use the Flask application-factory pattern with one blueprint per feature area:

```text
wedding/
├── .github/copilot-instructions.md
├── pyproject.toml              # deps & project metadata (managed via uv)
├── uv.lock
├── app/
│   ├── __init__.py             # intentionally empty (no logic in __init__ files)
│   ├── config.py               # AppConfig (pydantic):
│   │                           #      HOST/PORT/FLASK_ENV/APP_NAME from .env
│   ├── web_server.py           # create_app(config) factory
│   ├── main.py                 # entrypoint: run via `uv run python app/main.py`
│   ├── data/store.py           # in-memory mock data + accessor
│   │                           #                       functions (DB swap point)
│   ├── main/                   # landing/home page blueprint
│   │   ├── __init__.py         # intentionally empty
│   │   └── routes.py           # defines `bp` and the index route rendering
│   │                           #                             templates/index.html
│   ├── rsvp/                   # /rsvp/<token> flow
│   ├── info/                   # schedule, food, seating, conversation questions
│   ├── photos/                 # photo vault feature
│   ├── admin/                  # organizer view
│   ├── templates/              # Jinja templates, mirror blueprint structure
│   └── static/                 # CSS/JS/images
├── Dockerfile                  # container image for running the app
├── docker-compose.yml          # local dev stack (single `web` service)
└── run.sh                      # rebuild + launch the app in Docker
```

Each feature blueprint follows the `main/` pattern: a package whose
`__init__.py` stays **empty** (no logic, no imports — this is a strict
project rule, see below) and whose `routes.py` defines both the `Blueprint`
instance and its views, registered in `create_app()`.

**Important — flat imports & no logic in `__init__.py`:**

- Modules under `app/` import each other with flat, non-package-qualified
  paths (e.g. `from config import AppConfig`, `from main.routes import bp`),
  not `from app.config import ...`. This only resolves correctly because the
  app is always launched as `uv run python app/main.py` from the repo root,
  which puts `app/` itself (not the repo root) at the front of `sys.path`.
  Do not "fix" these to package-style imports, and do not run the app via
  `python -m app.main` or similar — mixing both import styles can cause
  Python to load the same module twice under different names, silently
  breaking blueprint registration.
- Every `__init__.py` under `app/` (including `app/__init__.py` and
  `app/main/__init__.py`) must stay completely empty — no `Blueprint(...)`
  instantiation, no imports. Define blueprints and routes in `routes.py`
  instead.

Keep routes thin: they call into data-layer / service functions rather than
embedding business logic directly.

## Mock Data Layer Rules

- All fake/in-memory data lives in `app/data/store.py`, never scattered
  across route files.
- Expose data via functions (`get_invitee(token)`, `save_rsvp(token, data)`,
  `decrement_photo_count(token)`, etc.), not raw dict imports, so swapping in
  a real database later stays localized.
- Seed a handful of clearly fake invitees/tokens for local dev and testing.

## Feature Guidance

- **RSVP** (`/rsvp/<token>`): show the invitee's name; form for attendance,
  dietary restrictions, plus-ones, housing needs. Validate server-side.
- **Day-of info**: schedule/timeline, food/menu, seating chart lookup,
  table-specific conversation-starter questions.
- **Photo vault** (`/photos/<token>`): fixed allowance (10 shots) per
  invitee; decrement a counter on "capture" — metadata only, no real files.
- **Admin view**: list invitees, view RSVP responses/stats, manage mock
  invitee list. Not production-grade auth yet, but don't leave it fully open
  — add at least a basic guard, and flag any gaps as TODOs.

## Coding Style

- Follow PEP 8; clear, descriptive names.
- Small, focused functions; keep blueprint boundaries clean.
- DRY templates: a `base.html` layout with `{% block %}`s and reusable
  partials for repeated UI (nav, cards, etc.).

## Commands (always via uv)

```bash
uv sync                               # install/sync dependencies
uv add <package>                      # add a runtime dependency
uv add --dev <package>                # add a dev dependency (e.g. pytest)
uv run python app/main.py             # run the app (must run from repo root)
uv run pytest                         # run tests
uv run ruff check .                   # lint
uv run ruff format --check .          # format check
```

First-time setup: create a `.env` file in the repo root (gitignored) with
`FLASK_ENV`, `HOST`, `PORT`, and `APP_NAME` — see `README.md` for an example.

## Running via Docker

The app can also be run containerized via Docker Compose:

```bash
./run.sh          # tears down old containers, rebuilds, and prints the link
# or manually:
docker compose up -d --build
```

`run.sh` tears down any existing containers, rebuilds and starts fresh ones,
waits for the app to respond, then prints the `http://localhost:5000/` link.
The compose setup bind-mounts the repo for live code reload and runs Flask's
dev server — not production-grade, fine for this stage of the project.

## Testing

- Add tests under `tests/` using `pytest` + Flask's test client as routes are
  built. Run via `uv run pytest`. Don't introduce new test frameworks unless
  necessary.

## Privacy

This app will hold real personal data (names, dietary needs, housing
addresses, eventually photos). Never commit real guest data or photos to the
repo — use clearly fake placeholder data in code, fixtures, and examples.
