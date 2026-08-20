# The Lidholm-Wedding Everything App

<p align="center">
    <a href="https://github.com/elidholm/wedding/actions/workflows/ci.yml"><img align="center" src="https://github.com/elidholm/wedding/actions/workflows/ci.yml/badge.svg" alt="github actions"></a>
    <a href="https://github.com/zricethezav/gitleaks-action"><img align="center" src="https://img.shields.io/badge/protected%20by-gitleaks-blue" alt="gitleaks badge"></a>
    <a href="https://github.com/elidholm/wedding/issues"><img align="center" src="https://img.shields.io/github/issues/elidholm/wedding" alt="open issues"></a>
    <a href="https://github.com/elidholm/wedding/commits/master"><img align="center" src="https://img.shields.io/github/commit-activity/m/elidholm/wedding" alt="commit frequency"></a>
</p>

---

A Flask web app built as the digital hub for our wedding. Guests scan a personal QR code to RSVP via a unique link, then browse the day's schedule, seating, table info, and contact details. Currently implemented pages:

- **Home** (`/`) — landing page, with an optional embedded Google Maps view of
  the venue.
- **RSVP** (`/rsvp`) — guest lookup and RSVP form.
- **Itinerary** (`/itinerary`) — the day's schedule.
- **Seating** (`/seating`) — table seating info.
- **Table info** (`/tables/<table_name>`) — per-table detail pages.
- **Contact** (`/contact`) — contact details for the wedding couple/toastmasters.

The API endpoints are also available for programmatic access behind a `/api/v<x>` prefix:

- **Health check** (`/api/v1/health`) — used by Docker's `HEALTHCHECK` and `run.sh`.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (manages the Python version, virtual environment, and dependencies — see `.python-version`/`pyproject.toml` for the exact Python version pinned).
- [Docker](https://docs.docker.com/get-docker/) + Docker Compose, only if you want to run the app containerized instead of directly with `uv`.

## Getting started

1. Clone the repo and install dependencies:

   ```bash
   make install
   ```

   This runs `uv sync --all-extras --dev` and installs the project's [pre-commit](https://pre-commit.com/) hooks (see [Pre-commit hooks](#pre-commit-hooks) below).

2. Create your local `.env` file from the template:

   ```bash
   make env-init
   ```

   This copies `.env.example` to `.env` (without overwriting an existing one) — edit the values as needed. See [Configuration](#configuration) below for what each variable does.

3. Wedding-specific content (app name, venue, contact info) lives in `src/config.yml`, not `.env` — edit that file with your own details. The checked-in version contains placeholder data.

## Running locally

Directly with `uv` (no Docker):

```bash
make run-local
# equivalent to: uv run python src/main.py
```

The app will be available at `http://localhost:5000` (or whatever `HOST`/`PORT` you configured in `.env`).

With Docker Compose, via `run.sh`:

```bash
make run    # ./run.sh        — tear down, rebuild, and start fresh containers
make dev    # ./run.sh -d     — same, but with file-watch/live-reload enabled
make stop   # ./run.sh -s     — stop and remove containers
```

`run.sh` also supports being called directly (`./run.sh -h` for usage), and runs a few pre-flight checks (Docker running, required files present) before building anything. Other Docker-related shortcuts:

```bash
make docker       # docker compose build
make docker-up    # docker compose up -d
make docker-down  # docker compose down --remove-orphans
make docker-logs  # docker compose logs -f
make shell        # open a shell in the running app container
```

## Configuration

Environment variables (see `.env.example` for the template):

| Variable         | Purpose                                                                                 |
| ---------------- | --------------------------------------------------------------------------------------- |
| `FLASK_ENV`      | `development` or `production`; controls Flask debug mode.                               |
| `HOST`           | Host address the app binds to (default `0.0.0.0`).                                      |
| `PORT`           | Port the app binds to (default `5000`).                                                 |
| `SECRET_KEY`     | Flask session secret — set to a random value, never commit a real one.                  |
| `LOG_LEVEL`      | Logging verbosity (e.g. `INFO`, `DEBUG`).                                               |
| `GOOGLEMAPS_KEY` | Optional Google Maps embed API key; the venue map on the home page is skipped if unset. |

Any of these can also be set directly in `src/config.yml` — environment variables take precedence and override the YAML file's values at startup (see `Config.load` in `src/core/config.py`).

Wedding-specific content (`app_name`, `wedding_couple_contact`, `toast_master_contact`, `venue`) is only configurable via `src/config.yml`, since it's structured data rather than simple scalars.

## Linting, type-checking & tests

```bash
uv run ruff check .                                                     # lint
uv run ruff format --check .                                            # format check
uv run mypy .                                                           # type check
uv run pytest --cov=src --cov-report=term-missing --cov-fail-under=85   # tests + coverage
uv run djlint . --profile=jinja                                         # HTML/Jinja template lint
uv run shellcheck *.sh                                                  # shell script lint
uv run taplo lint                                                       # TOML lint
uv sync --locked                                                        # verify uv.lock is up to date
```

Or via the Makefile — each check has its own target (`make lint`, `make fmt-check`, `make check`, `make test`, `make html-lint`, `make shell-lint`, `make toml-lint`, `make lock-check`), and:

```bash
make ci  # runs every check above together — the same gate CI runs
```

Run `make help` for the full list of targets (including `make fmt`/ `make lint-fix` for auto-fixing, and `make clean` to remove regenerable caches).

## Pre-commit hooks

`make install` installs [pre-commit](https://pre-commit.com/) hooks (configured in `.pre-commit-config.yaml`) that automatically run fast, file-scoped checks (ruff lint/format, trailing whitespace, end-of-file fixer, TOML/YAML validation) on every commit. If you skipped `make install`, you can install them separately with:

```bash
uv run pre-commit install
```

These hooks are a fast first line of defense — they don't replace running `make ci` before pushing, since `make ci` covers more (mypy, tests, djlint, shellcheck, taplo, lockfile check).

## Continuous integration & deployment

Three GitHub Actions workflows run automatically:

- **[`ci.yml`](.github/workflows/ci.yml)** — on every PR to `master` and weekly on a schedule. A `changes` job detects which file types changed and only runs the relevant lint/type-check/test jobs (Python lint via ruff, type-check via mypy, tests via pytest with coverage, HTML/Jinja via djlint, CSS via stylelint, Markdown via markdownlint-cli2, shell via shellcheck + shfmt, TOML via taplo, and the workflow files themselves via actionlint).
- **[`security.yml`](.github/workflows/security.yml)** — on every PR to `master` and weekly on a schedule: [Gitleaks](https://github.com/gitleaks/gitleaks) scans for accidentally committed secrets, and [CodeQL](https://codeql.github.com/) statically analyzes the Python code for vulnerabilities.
- **[`docker-publish.yml`](.github/workflows/docker-publish.yml)** — on push to `master` and on `v*.*.*` tags: builds the production Docker image and publishes it to the GitHub Container Registry (tagged `latest`, by branch, by tag, and by commit SHA).

`Dependabot` (`.github/dependabot.yml`) opens weekly PRs to keep both Python dependencies (via `uv`) and GitHub Actions up to date.

## License

Licensed under the [Apache License 2.0](LICENSE).
