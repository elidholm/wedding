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
  (loaded with `python-dotenv`) and centralized in `src/config.py`'s
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

The project currently uses flat, single-file modules under `src/` rather
than a package-per-feature layout — this is the **current, actual**
convention (see below for how this may evolve as features grow):

```text
wedding/
├── .github/
│   ├── copilot-instructions.md
│   ├── dependabot.yml
│   └── workflows/ci.yml        # lint (ruff/djlint/stylelint/markdownlint/
│                                #   shellcheck+shfmt/taplo/actionlint) + pytest
├── src/
│   ├── __init__.py              # intentionally empty (no logic here)
│   ├── config.py                # AppConfig (pydantic):
│   │                            #      HOST/PORT/FLASK_ENV/APP_NAME from .env
│   ├── web_server.py            # create_app(config) factory; defines the
│   │                            #      "/" home route inline and registers
│   │                            #      the rsvp blueprint
│   ├── main.py                   # entrypoint: run via `make run-local`
│   │                            #      (`uv run python src/main.py`)
│   ├── rsvp.py                   # `rsvp` blueprint: flat module defining
│   │                            #      `bp` + its route(s) directly (no
│   │                            #      package/routes.py split — see below)
│   ├── templates/
│   │   ├── base.html             # shared layout, extended via {% block %}
│   │   ├── home.html
│   │   └── rsvp.html
│   └── static/
│       └── favicon.png
├── tests/
│   ├── conftest.py               # puts src/ on sys.path for flat imports
│   ├── test_config.py
│   └── test_web_server.py
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

**Blueprint pattern (current vs. future):** each feature area today is a
single flat module (e.g. `rsvp.py`) that defines `bp = Blueprint(...)` and
its route(s) directly in that one file — there is no `main/` or `rsvp/`
package with a separate `routes.py` yet. If a feature area grows enough to
warrant splitting (e.g. multiple route files, helpers, or its own mock
data), promote it to a package following the empty-`__init__.py` +
`routes.py` convention already established for `src/__init__.py`: an
`__init__.py` that stays completely empty (no `Blueprint(...)`
instantiation, no imports) and a `routes.py` that defines the blueprint and
views. Don't introduce this extra structure prematurely for a feature
that's still a single small file.

**Important — flat imports & no logic in `__init__.py`:**

- Modules under `src/` import each other with flat, non-package-qualified
  paths (e.g. `from config import AppConfig`, `from rsvp import bp`), not
  `from src.config import ...`. This only resolves correctly because the
  app is always launched as `uv run python src/main.py` (or `make
  run-local`) from the repo root, which puts `src/` itself (not the repo
  root) at the front of `sys.path`. Do not "fix" these to package-style
  imports, and do not run the app via `python -m src.main` or similar —
  mixing both import styles can cause Python to load the same module twice
  under different names, silently breaking blueprint registration.
- Every `__init__.py` under `src/` must stay completely empty — no
  `Blueprint(...)` instantiation, no imports. Define blueprints and routes
  in the feature's own module (or `routes.py`, once/if a feature is
  promoted to a package) instead.

Keep routes thin: they call into data-layer / service functions rather than
embedding business logic directly.

## Mock Data Layer Rules (planned — not yet implemented)

There is no `data/store.py` or any data-access layer in the codebase yet;
`rsvp.py` currently just renders a static template. Once real invitee/RSVP
data is needed, follow this convention:

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
make test          # uv run pytest
make check         # fmt-check + lint + test (pre-push / CI-parity gate)
make run-local      # uv run python src/main.py  (run directly, no Docker)
make run            # ./run.sh  (tear down + rebuild + run via Docker Compose)
make docker         # docker compose build
make docker-up      # docker compose up -d
make docker-down    # docker compose down --remove-orphans
make docker-logs    # docker compose logs -f
make clean          # remove __pycache__/.ruff_cache/.pytest_cache
```

First-time setup: create a `.env` file in the repo root (gitignored) with
`FLASK_ENV`, `HOST`, `PORT`, and `APP_NAME` — see `README.md` for an example.

## Running via Docker

The app can also be run containerized via Docker Compose:

```bash
make run          # or: ./run.sh
# or manually:
docker compose up -d --build
```

`run.sh` tears down any existing containers, rebuilds and starts fresh ones,
waits for the app to respond, then prints the `http://localhost:5000/` link.
The `Dockerfile` runs the container as a fixed-UID (1000) non-root user —
never remove the `USER` directive or revert to running as root.

## Testing

- Tests live under `tests/` as `unittest.TestCase` classes (see existing
  `tests/test_config.py`, `tests/test_web_server.py` for the style), run via
  **pytest** (`uv run pytest` / `make test`) — pytest natively collects
  `unittest.TestCase` subclasses, so both conventions coexist by design.
- Directory/file naming mirrors `src/` directly: `src/<name>.py` →
  `tests/test_<name>.py` (no `unit/`/`component/` subdirectories for this
  project).
- `tests/conftest.py` puts `src/` on `sys.path` so tests can use the same
  flat-import style as the app itself (`from config import AppConfig`).
  Keep this in sync if `src/` is ever renamed or moved again.
- Keep new tests small and focused (one behavior per test method, with a
  docstring). Don't introduce a new test framework — pytest is the runner,
  `unittest.TestCase` is the authoring style for this project.

## Privacy

This app will hold real personal data (names, dietary needs, housing
addresses, eventually photos). Never commit real guest data or photos to the
repo — use clearly fake placeholder data in code, fixtures, and examples.
