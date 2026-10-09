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

| Variable         | Purpose                                                                                            |
| ---------------- | -------------------------------------------------------------------------------------------------- |
| `FLASK_ENV`      | `development` or `production`; controls Flask debug mode.                                          |
| `HOST`           | Host address the app binds to (default `0.0.0.0`).                                                 |
| `PORT`           | Port the app binds to (default `5000`).                                                            |
| `SECRET_KEY`     | Flask session secret — set to a random value, never commit a real one.                             |
| `ADMIN_PASSWORD` | Password required to log in to the `/admin` area — set to a random value, never commit a real one. |
| `LOG_LEVEL`      | Logging verbosity (e.g. `INFO`, `DEBUG`).                                                          |
| `GOOGLEMAPS_KEY` | Optional Google Maps embed API key; the venue map on the home page is skipped if unset.            |

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

### Responsive-layout tests

`tests/test_responsive.py` renders the real pages in headless Chromium at 320/375/768/1440px and asserts that nothing forces the document wider than the viewport, so the site can't silently regress into needing horizontal scrolling on a phone. It also writes a screenshot of every page/width combination for eyeballing.

These tests need a browser binary, which isn't installed by `make install`:

```bash
uv run playwright install chromium
```

Without it the whole module is skipped, so `make test` still passes on a machine that hasn't run the above. Screenshots go to `tests/screenshots/` by default; override with `WEDDING_SCREENSHOT_DIR=/some/path`.

### Staging E2E tests

`tests/e2e/test_staging.py` uses Playwright against an external, disposable
container. It covers public navigation, mobile layout/menu interaction, RSVP
lookup and saved responses, and admin authentication. It uses the existing fake
RSVP invitee `123456`, not real guest data. The selected browser and admin
credentials are required when `E2E_BASE_URL` is set; browser installation failures fail the suite.
Without that URL these tests are skipped by the normal unit-test run.

Run the same staging setup locally (after installing dependencies):

```bash
uv run playwright install --with-deps chromium
docker build -t wedding-staging:local .
export SECRET_KEY="$(openssl rand -hex 32)"
export ADMIN_PASSWORD="$(openssl rand -hex 32)"
docker run --detach --name wedding-staging \
  --publish 127.0.0.1:5000:5000 \
  --tmpfs /app/storage:rw,uid=1000,gid=1000,mode=0700 \
  --env SECRET_KEY --env ADMIN_PASSWORD \
  --env FLASK_ENV=production \
  --env DB_URL=sqlite:////app/storage/staging.db \
  --env PYTHONPATH=/app/src \
  --workdir /app/src wedding-staging:local \
  flask --app main run --host=0.0.0.0 --port=5000 --no-debugger --no-reload
curl --fail --silent --show-error --retry 30 --retry-delay 2 \
  --retry-connrefused --retry-all-errors --max-time 2 --retry-max-time 90 \
  http://127.0.0.1:5000/api/v1/health
E2E_BASE_URL=http://127.0.0.1:5000 E2E_ADMIN_PASSWORD="$ADMIN_PASSWORD" \
  uv run pytest tests/e2e
docker logs wedding-staging
docker rm --force wedding-staging
unset SECRET_KEY ADMIN_PASSWORD
```

Always remove the staging container after testing, including after a failure.
SQLite storage is temporary and discarded with the container; RSVP state is
in-memory. Screenshots of the final browser state go to
`/tmp/wedding-e2e-results`; override with `E2E_ARTIFACT_DIR`. Only run this
mutating suite against disposable staging, never production.

`E2E_BROWSER` selects `chromium` (the default), `firefox`, or `webkit`.
Install the selected engine with `uv run playwright install --with-deps firefox`
and set `E2E_BROWSER=firefox` on the pytest command to reproduce that matrix leg.
Each engine runs every staging test, including layout checks at 320, 375, 768,
and 1440 pixels; CD uses an isolated container and uniquely named diagnostic
artifact for each engine.

### CSS

The custom stylesheet lives in `src/static/css/style.css` and is linked *after* Bootstrap so it can override Bootstrap's CSS custom properties (`--bs-*`) — the palette and typography are set that way rather than by recompiling Bootstrap's Sass. Theme values are defined as custom properties in the `:root` block at the top of the file. Lint it with:

```bash
npx stylelint "**/*.css"   # config: .stylelintrc.json
```

## Pre-commit hooks

`make install` installs [pre-commit](https://pre-commit.com/) hooks (configured in `.pre-commit-config.yaml`) that automatically run fast, file-scoped checks (ruff lint/format, trailing whitespace, end-of-file fixer, TOML/YAML validation) on every commit. If you skipped `make install`, you can install them separately with:

```bash
uv run pre-commit install
```

These hooks are a fast first line of defense — they don't replace running `make ci` before pushing, since `make ci` covers more (mypy, tests, djlint, shellcheck, taplo, css, lockfile check).

## Continuous integration & deployment

Three GitHub Actions workflows run automatically:

- **[CI - Quality Checks and Tests](.github/workflows/ci.yml)** — on every PR to
  `master`, daily, and on manual dispatch. A `changes` job selects relevant
  lint/type-check jobs (ruff, mypy, djlint, stylelint, markdownlint-cli2,
  shellcheck/shfmt, taplo, and actionlint). The Python test matrix runs the full
  unit suite with the 85% coverage gate on Python 3.12, 3.13, and 3.14, installing
  Chromium so responsive tests execute rather than skip. Any application,
  template, static asset, test, dependency, Python-version, or CI workflow
  change triggers this matrix. External staging tests run in CD, not against
  the unit-test app.
- **[Security - Secrets and Code Analysis](.github/workflows/security.yml)** —
  on every PR to `master` and weekly:
  [Gitleaks](https://github.com/gitleaks/gitleaks) checks committed secrets and
  [CodeQL](https://codeql.github.com/) analyzes Python vulnerabilities.
- **[CD - Build, E2E Test and Publish](.github/workflows/cd.yml)** — on push to
  `master` and on `v*.*.*` tags: builds once and saves the image as an immutable
  workflow artifact. Each staging matrix job loads it, starts an isolated container with
  generated credentials and temporary SQLite storage, waits for health, and
  runs the complete E2E suite on Chromium, Firefox, or WebKit. All three engines
  must pass to unlock GHCR
  publication of that same image, without rebuilding (tagged `latest`, by
  branch, by tag, and by commit SHA). Only the publish job has package-write
  permission. Shared concurrency cancels superseded deliveries across all
  branches/tags, preventing an older in-flight run from publishing after its
  successor. Container cleanup and diagnostic uploads run even on test failure;
  test results, screenshots, and container logs are retained for seven days.
  Staging is ephemeral on the Actions runner; publication to GHCR does not
  deploy the app to a live hosting environment.

Both test matrices disable fail-fast so one failing leg does not cancel the
remaining coverage. Job names include their Python version or browser to make
failures easy to identify. The stable `Pytest Results` check gathers all Python
matrix results and fails on any failed or cancelled suite, or an unexpected
skip. It passes intentional change-filter skips only when change detection
succeeds. `Staging Pytest Results` requires every browser suite to succeed
before publication. If branch protection requires the previous
`Python tests (pytest)` check or individual versioned checks, update it to
require `Pytest Results` after merging; workflow changes do not update
repository rules.

`Dependabot` (`.github/dependabot.yml`) opens weekly PRs to keep both Python dependencies (via `uv`) and GitHub Actions up to date.

## License

Licensed under the [Apache License 2.0](LICENSE).
