# Agent Guide (daily_stock_analysis)

Python 3.10+ project for daily AI-assisted stock analysis.

## Repo Map

- Entrypoints: `main.py` (CLI + scheduler), `webui.py` (WebUI), `test_env.py` (env verification)
- Core: `src/` (pipeline/config/analyzers/notification/storage), `data_provider/` (market data)
- CI: `.github/workflows/ci.yml` (syntax + flake8 severe), Docker build in CI

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

- `.env` is loaded by `src/config.py` (`setup_env()`); do not commit secrets.
- Proxy note: `src/config.py` auto-sets `NO_PROXY` for domestic market-data domains.

## Run (Dev)

```bash
python main.py                    # full run
python main.py --schedule         # scheduled mode
python main.py --stocks 600519,AAPL,hk00700
python main.py --market-review
python main.py --dry-run          # fetch/save only (no AI)
python main.py --webui            # start WebUI + run
python main.py --webui-only       # start WebUI only
```

## Build / Lint / Test

```bash
# Format
python -m black .
python -m isort .

# Lint
python -m flake8 .

# CI-like "blocking" lint (matches `.github/workflows/ci.yml` intent)
python -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Syntax check
python -m compileall -q .
```

Docker (optional):

```bash
docker build -t stock-analysis:test -f docker/Dockerfile .
docker run --rm stock-analysis:test python -c "print('Docker OK')"
```

### Tests

There is no dedicated `tests/` directory currently. Use `test_env.py`:

```bash
python test_env.py
python test_env.py --config
python test_env.py --db
python test_env.py --fetch
python test_env.py --llm
python test_env.py --notify
```

Pytest config exists in `setup.cfg` (`[tool:pytest]`). If/when tests are added:

```bash
pytest                              # all tests
pytest path/to/test_file.py          # single file
pytest path/to/test_file.py::test_x  # single test
pytest -k "keyword"                  # filter by substring
```

## Cursor / Copilot Rules

- No `.cursor/rules/` rules found.
- No `.cursorrules` file found.
- No `.github/copilot-instructions.md` found.

If those are added later, treat them as higher priority than this file.

## Code Style Guidelines

Formatting:
- Black, line length 120 (see `pyproject.toml`); keep generated markdown readable.

Imports:
- isort (profile black). Group as stdlib, third-party, first-party.
- First-party modules: `src`, `data_provider`, `bot`.
- Avoid circular imports (common hotspots: `src/config.py`, `src/notification.py`, `src/core/*`).

Types:
- Add type hints for public APIs and non-trivial logic.
- Prefer `Optional[T]` where used in the file; keep style consistent per file.
- Use dataclasses for config-like structs (pattern: `src/config.py`).

Naming:
- `snake_case` for modules/functions/vars, `CapWords` for classes, `UPPER_SNAKE_CASE` for constants.
- Prefer explicit names over abbreviations.

Logging:
- Use `logger = logging.getLogger(__name__)`.
- `info` for progress, `warning` for recoverable issues, `exception` to include stack traces.
- Keep `print()` mostly in CLI utilities (`test_env.py`).

Errors & resilience:
- The pipeline should keep going when one stock/provider fails.
- At system boundaries catch exceptions, log context (stock code, provider, channel), and return structured failures.
- Avoid hard failures on transient external issues; use retries/backoff and circuit-breaker patterns where present.

Config & secrets:
- Add settings to `src/config.py:Config` and load via `_load_from_env()`.
- Never hardcode tokens/keys; do not commit `.env`.

External I/O:
- Set timeouts for HTTP calls; avoid unbounded waits.
- When adding a new data source, integrate via `data_provider/` and support fallback.

Filesystem:
- Write runtime outputs under `data/`, `logs/`, `reports/`, `analysis_history/`.
- Use `mkdir(parents=True, exist_ok=True)`.

CI/workflows:
- Changes to `.github/workflows/*` are security sensitive; keep minimal and review carefully.
