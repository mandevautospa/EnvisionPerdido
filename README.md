# EnvisionPerdido

EnvisionPerdido is an automation toolkit for collecting, classifying, reviewing, and publishing community calendar events for Envision Perdido.

## Current project scope

The repository currently covers:

- scraping event data from supported sources, including the Perdido Chamber site and Wren Haven
- normalizing event records and applying venue and tag taxonomy helpers
- classifying events with the trained SVM model in `data/artifacts/`
- generating review-ready CSV output and email summaries
- uploading approved events to a WordPress site running EventON
- running health checks against the WordPress calendar
- optionally regenerating event descriptions with OpenAI
- supporting retraining, maintenance, and debugging workflows for the pipeline

## Primary entry points

### Main pipeline

```bash
python scripts/automated_pipeline.py
```

Runs the end-to-end scrape -> normalize -> classify -> review -> upload preparation flow.

### Manual uploader

```bash
python scripts/wordpress_uploader.py
```

Uploads prepared events to WordPress after review.

### Health check

```bash
python scripts/health_check.py
```

Checks WordPress API access, upcoming EventON events, and the public calendar page.

### Optional description enhancement

```bash
python scripts/regenerate_descriptions.py --sync --top-n 100 --min-confidence 0.75
```

Uses OpenAI to improve selected event descriptions when `OPENAI_API_KEY` is configured.

## Recommended workflows

### Docker workflow

Build the image from the repository root:

```bash
docker compose build
```

Run the main pipeline:

```bash
docker compose run --rm pipeline
```

Run the health check:

```bash
docker compose run --rm pipeline python scripts/health_check.py
```

Run the uploader:

```bash
docker compose run --rm pipeline python scripts/wordpress_uploader.py
```

Docker Compose reads environment variables from the root `.env` file.

### Local Python workflow

Create a virtual environment and install dependencies:

```bash
python3 -m venv .venvEnvisionPerdido
. .venvEnvisionPerdido/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

On Windows:

```powershell
py -3 -m venv .venvEnvisionPerdido
.\.venvEnvisionPerdido\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Environment configuration

The repository currently uses two configuration patterns:

- **Docker runs**: `docker compose` loads the root `.env` file.
- **Local Python runs**: scripts import `scripts/env_loader.py`, which prefers environment variables already present in the shell and also checks machine-local secrets files. On Windows, you can copy `scripts/windows/env.ps1.example` to `scripts/windows/env.ps1`.

For local shell-based runs, set or export at least:

- `SMTP_SERVER`
- `SMTP_PORT`
- `SENDER_EMAIL`
- `EMAIL_PASSWORD`
- `RECIPIENT_EMAIL`

Also set these when `AUTO_UPLOAD=true`:

- `WP_SITE_URL`
- `WP_USERNAME`
- `WP_APP_PASSWORD`

Useful optional variables:

- `AUTO_UPLOAD`
- `SITE_TIMEZONE`
- `HEALTH_SEND_OK`
- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_USE_BATCH`
- `OPENAI_TOP_N`
- `OPENAI_MIN_CONFIDENCE`

Start from `.env.example` for Docker-style configuration.

## Validation and development commands

The Makefile includes the main repo commands:

```bash
make setup
make verify
make test
make lint
make dry-run
make run-pipeline
make run-uploader
make regenerate-descriptions-dry-run
make regenerate-descriptions-sync
make regenerate-descriptions
```

Notes:

- `make verify` expects `.env` plus the model artifacts in `data/artifacts/`.
- `pytest.ini` currently scopes default test discovery to `tests/unit`.
- `make lint` currently runs `ruff check scripts/`.

## Repository layout

```text
EnvisionPerdido/
├── data/            Training data, artifacts, cache, and image mappings
├── docs/            Project, deployment, and integration documentation
├── plugins/         WordPress plugin code used by the calendar integration
├── scripts/         Pipeline, scraping, ML, maintenance, and support scripts
├── skills/          Local reusable Copilot skills for env, Docker, pipeline, upload, and health-check tasks
├── tests/           Unit, integration, smoke, and development tests
├── Dockerfile       Container image definition
├── docker-compose.yml
├── Makefile
└── requirements.txt
```

## Documentation

Useful docs in `docs/`:

- [`INDEX.md`](docs/INDEX.md) - documentation index
- [`QUICKSTART.md`](docs/QUICKSTART.md) - user-oriented quick start
- [`PROJECT_STRUCTURE.md`](docs/PROJECT_STRUCTURE.md) - repository organization
- [`WORDPRESS_INTEGRATION_GUIDE.md`](docs/WORDPRESS_INTEGRATION_GUIDE.md) - WordPress/EventON workflow
- [`AUTOMATION_SETUP.md`](docs/AUTOMATION_SETUP.md) - automation setup guidance
- [`CI_CD_GUIDE.md`](docs/CI_CD_GUIDE.md) - CI and validation details
- [`CONTRIBUTING.md`](docs/CONTRIBUTING.md) - contribution workflow
- [`CRITICAL_ISSUES.md`](docs/CRITICAL_ISSUES.md) - known risks and open issues

## Notes

- The trained classifier artifacts are committed under `data/artifacts/` and are required for the main pipeline.
- Output files are written under `output/` during local runs and under mounted volumes during containerized runs.
- The repo also includes maintenance and debugging utilities under `scripts/maintenance/` and `scripts/devTooling/` that are outside the main publish pipeline.
