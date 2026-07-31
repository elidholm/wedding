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
- **Configuration**: read from environment variables and centralized in
  `src/core/config.py`'s `Config` (a `pydantic_settings.BaseSettings`
  subclass). Field defaults use `os.getenv(...)` explicitly (rather than
  relying on `BaseSettings`'s own automatic env-loading), and a single
  module-level `config = Config()` instance is created once and imported
  everywhere it's needed (`from core.config import config`) — treat it as
  an app-wide singleton, not something to re-instantiate per request.
  `.env` itself is gitignored — never commit real values. `Config` uses
  lowercase field names, so `src/main.py` copies each field into
  `app.config[...]` under the matching uppercase key (Flask's
  `from_object()` only picks up uppercase attributes, so it can't be used
  directly here).
- **Data storage**: no real database yet. Use in-memory Python data structures
  behind a small data-access layer (see below) so it's a localized swap later.
  Do not introduce a DB/ORM unless explicitly instructed.
- **Photo uploads**: no real file storage yet. Track photo-vault state
  (remaining count, "taken" status) as metadata only — do not implement real
  upload/storage unless explicitly instructed.

## Project Structure

The project uses a small package-per-concern layout under `src/`: shared
app setup lives in `src/core/`, and each feature's blueprint lives in its
own flat module under `src/routes/`. This is the **current, actual**
convention (see below for how blueprints may evolve further as features
grow):

```text
wedding/
├── .github/
│   ├── copilot-instructions.md
│   ├── dependabot.yml
│   └── workflows/ci.yml         # ruff/mypy/pytest/djlint/stylelint/
│                                 #   markdownlint/shellcheck+shfmt/taplo/
│                                 #   actionlint, one job per tool
├── src/
│   ├── __init__.py               # intentionally empty (no logic here)
│   ├── core/
│   │   ├── __init__.py           # intentionally empty (no logic here)
│   │   ├── config.py             # Config(BaseSettings): APP_NAME/
│   │   │                         #   FLASK_ENV/HOST/PORT/SECRET_KEY from
│   │   │                         #   .env; exports a `config` singleton
│   │   └── logging.py            # setup_logging(): rich-based logging
│   │                             #   handler, called once from main.py
│   ├── main.py                    # builds the module-level `app = Flask(
│   │                              #   ...)` singleton directly (no
│   │                              #   create_app() factory), registers
│   │                              #   all blueprints, defines `main()`
│   │                              #   which calls `app.run(...)`
│   ├── routes/
│   │   ├── home.py                 # `home` blueprint: "/" and "/home"
│   │   ├── rsvp.py                  # `rsvp` blueprint: "/" (GET renders
│   │   │                            #   search form, POST looks up and
│   │   │                            #   redirects) + "/<int:guest_id>"
│   │   └── contact.py                # `contact` blueprint: "/"
│   ├── templates/
│   │   ├── base.html                  # shared layout, extended via
│   │   │                              #   {% block %}
│   │   ├── home.html
│   │   ├── contact.html
│   │   ├── rsvp.html
│   │   └── rsvp_guest.html
│   └── static/
│       └── favicon.png
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # puts src/ on sys.path for flat imports
│   ├── core/
│   │   └── test_config.py         # mirrors src/core/config.py
│   └── test_main.py               # mirrors src/main.py; covers the app
│                                  #   singleton + every registered route
├── Makefile                      # `make help` lists all shortcuts
├── Dockerfile                    # container image for running the app
├── docker-compose.yml            # local dev stack (single `web` service)
├── run.sh                        # rebuild + launch the app in Docker
├── .editorconfig                 # shfmt reads this (2-space indent for
│                                 #      *.sh) — shfmt has no TOML config
│                                 #      support, so don't add a .shfmt.toml
├── .taplo.toml                   # array_auto_collapse = false, so taplo
│                                 #      keeps pyproject.toml's multi-line
│                                 #      dependency arrays instead of
│                                 #      collapsing them to one line
├── pyproject.toml                # deps & project metadata (managed via uv)
└── uv.lock
```

**Blueprint pattern:** `src/routes/` is a package, but each feature is
still just a single flat module inside it (e.g. `routes/rsvp.py`) that
defines `bp = Blueprint(...)` and its route(s) directly in that one file —
there's no per-feature subpackage (e.g. no `routes/rsvp/routes.py` split)
yet. If a feature area grows enough to warrant splitting further (multiple
route files, helpers, or its own mock data), promote it to its own
subpackage under `routes/` following the empty-`__init__.py` convention
already used elsewhere: an `__init__.py` that stays completely empty (no
`Blueprint(...)` instantiation, no imports) and a `routes.py` that defines
the blueprint and views. Don't introduce this extra structure prematurely
for a feature that's still a single small file.

**Important — flat imports & no logic in `__init__.py`:**

- Modules under `src/` import each other with flat, non-package-qualified
  paths rooted at `src/` (e.g. `from core.config import config`, `from
  routes.rsvp import bp`), not `from src.core.config import ...`. This only
  resolves correctly because the app is always launched as `uv run python
  src/main.py` (or `make run-local`) from the repo root, which puts `src/`
  itself (not the repo root) at the front of `sys.path`. Do not "fix" these
  to package-style imports, and do not run the app via `python -m src.main`
  or similar — mixing both import styles can cause Python to load the same
  module twice under different names, silently breaking blueprint
  registration.
- Every `__init__.py` under `src/` (including `src/core/__init__.py`) must
  stay completely empty — no `Blueprint(...)` instantiation, no imports.
  Define blueprints and routes in the feature's own module under
  `src/routes/` instead.

Keep routes thin: they call into data-layer / service functions rather than
embedding business logic directly.

## Mock Data Layer Rules (planned — not yet implemented)

There is no `data/store.py` or any data-access layer in the codebase yet;
`src/routes/rsvp.py` currently only renders templates and redirects based on
a raw form-submitted `guest_id` — no real lookup against invitee data. Once
real invitee/RSVP data is needed, follow this convention:

- All fake/in-memory data should live in `src/data/store.py`, never
  scattered across route files.
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

## Commands

Prefer the `Makefile` shortcuts (`make help` lists all of them); the
underlying `uv`/`docker` commands are shown alongside for reference:

```bash
uv add <package>       # add a runtime dependency (no Makefile shortcut)
uv add --dev <package> # add a dev dependency (no Makefile shortcut)
make install       # uv sync --all-extras --dev
make fmt           # uv run ruff format .
make fmt-check     # uv run ruff format --check .
make lint          # uv run ruff check .
make lint-fix      # uv run ruff check --fix .
make check         # uv run mypy .  (type check)
make test          # uv run pytest
make html-lint      # uv run djlint . --profile=jinja
make ci             # fmt-check + lint + check + test + html-lint
                    #   (full pre-push / CI-parity gate)
make run-local      # uv run python src/main.py  (run directly, no Docker)
make run            # ./run.sh  (tear down + rebuild + run via Docker Compose)
make dev            # ./run.sh -d  (same, in development mode)
make docker         # docker compose build
make docker-up      # docker compose up -d
make docker-down    # docker compose down --remove-orphans
make docker-logs    # docker compose logs -f
make clean          # remove __pycache__/.ruff_cache/.pytest_cache
```

First-time setup: create a `.env` file in the repo root (gitignored) with
`FLASK_ENV`, `HOST`, `PORT`, `APP_NAME`, and `SECRET_KEY` — see `README.md`
for an example.

## Running via Docker

The app can also be run containerized via Docker Compose:

```bash
make run          # or: ./run.sh
# or manually:
docker compose up -d --build
```

`run.sh` tears down any existing containers, rebuilds and starts fresh ones,
waits for the app to respond, then prints the `http://localhost:5000/` link.
The `Dockerfile` runs the container as a non-root `appuser` — never remove
the `USER` directive or revert to running as root.

## Testing

- Tests live under `tests/` as `unittest.TestCase` classes (see existing
  `tests/core/test_config.py`, `tests/test_main.py` for the style), run via
  **pytest** (`uv run pytest` / `make test`) — pytest natively collects
  `unittest.TestCase` subclasses, so both conventions coexist by design.
- Directory/file naming mirrors `src/`'s package structure: `src/core/
  config.py` → `tests/core/test_config.py`, `src/main.py` →
  `tests/test_main.py` (which also covers every registered blueprint's
  routes, since `main.py` is where they're all wired together).
- `tests/conftest.py` puts `src/` on `sys.path` so tests can use the same
  flat-import style as the app itself (`from core.config import config`).
  Keep this in sync if `src/` is ever renamed or moved again.
- Keep new tests small and focused (one behavior per test method, with a
  docstring). Don't introduce a new test framework — pytest is the runner,
  `unittest.TestCase` is the authoring style for this project.

## Privacy

This app will hold real personal data (names, dietary needs, housing
addresses, eventually photos). Never commit real guest data or photos to the
repo — use clearly fake placeholder data in code, fixtures, and examples.
