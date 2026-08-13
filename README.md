# The Lidholm-Wedding Everything App

A Flask web app built as the digital hub for our wedding. Guests scan a personal
QR code to RSVP (attendance, dietary needs, plus-ones, housing) via a unique
link, then browse the day's schedule, menu, and seating info.

## Running locally

With [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

Copy `.env.example` to `.env` (`make env-init`) and edit the values as needed.

Then, from the repo root, run:

```bash
uv run python src/main.py
```

The app will be available at `http://localhost:5000` (or whatever `HOST`/`PORT`
you configured).

### Linting & tests

```bash
uv run ruff check .             # lint
uv run ruff format --check .    # format check
uv run mypy .                   # type check
uv run pytest                   # unit tests
uv run djlint . --profile=jinja # HTML template linting
```

Or via the Makefile: `make lint`, `make fmt-check`, `make check` (mypy),
`make test`, `make html-lint`, or `make ci` to run all of them together. Run
`make help` for the full list of targets.

With Docker Compose:

```bash
./run.sh
```

Or via the Makefile: `make run` (or `make dev` for development mode).
