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
├── pyproject.toml            # deps & project metadata (managed via uv)
├── uv.lock
├── app/
│   ├── __init__.py           # create_app() factory, registers blueprints
│   ├── data/store.py         # in-memory mock data + accessor
│   │                         #                       functions (DB swap point)
│   ├── rsvp/                 # /rsvp/<token> flow
│   ├── info/                 # schedule, food, seating, conversation questions
│   ├── photos/                # photo vault feature
│   └── admin/                 # organizer view
├── templates/                 # Jinja templates, mirror blueprint structure
├── static/                    # CSS/JS/images
└── run.py                     # entrypoint, calls create_app()
```
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
uv run python run.py                  # run the app
uv run flask --app app run --debug    # alt: run via Flask CLI
uv run pytest                         # run tests
```

## Testing

- Add tests under `tests/` using `pytest` + Flask's test client as routes are
  built. Run via `uv run pytest`. Don't introduce new test frameworks unless
  necessary.

## Privacy

This app will hold real personal data (names, dietary needs, housing
addresses, eventually photos). Never commit real guest data or photos to the
repo — use clearly fake placeholder data in code, fixtures, and examples.
