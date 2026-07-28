# The Lidholm-Wedding Everything App

A Flask web app built as the digital hub for our wedding. Guests scan a personal
QR code to RSVP (attendance, dietary needs, plus-ones, housing) via a unique
link, then browse the day's schedule, menu, and seating info.

## Running locally

With [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Create a `.env` file in the repo root (it's gitignored, so this is local-only)
with the following variables:

```bash
FLASK_ENV=development
HOST=0.0.0.0
PORT=5000
APP_NAME=The Wedding App
```

Then, from the repo root, run:

```bash
uv run python app/main.py
```

The app will be available at `http://localhost:5000` (or whatever `HOST`/`PORT`
you configured).

### Linting & tests

```bash
uv run ruff check .          # lint
uv run ruff format --check . # format check
uv run pytest                # unit tests
```

With Docker:

```bash
./run.sh
```
