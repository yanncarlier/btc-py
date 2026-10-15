# AGENTS.md - Agentic Coding Guidelines for Python 3 Projects

## Overview
This document provides guidelines for AI coding agents working in this Python 3 codebase. Adjust the specifics (package names, paths, dependency manager) to match the actual project before use. Examples assume a `src/` layout with `pyproject.toml`, but note the alternative commands where tooling might differ (pip vs poetry vs uv).

## Environment Setup

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

# Install the project in editable mode with dev dependencies
pip install -e ".[dev]"

# --- If using Poetry instead ---
poetry install

# --- If using uv instead ---
uv sync
```

## Build/Lint/Test Commands

### Running the project
```bash
# Run a module/script
python3 -m package_name

# Run a specific entry point defined in pyproject.toml
package-name-cli --help
```

### Testing
```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_module.py

# Run a specific test function
pytest tests/test_module.py::test_function_name

# Run tests matching a keyword expression
pytest -k "parse and not slow"

# Run with coverage
pytest --cov=package_name --cov-report=term-missing

# Run only tests marked as fast (assuming custom markers are configured)
pytest -m "not slow"

# Show print output and stop at first failure
pytest -s -x
```

### Linting, Formatting, and Type Checking
```bash
# Format code
ruff format .
# or, if using black
black .

# Lint (and auto-fix what's safe to fix)
ruff check . --fix

# Type check
mypy src/
# or
pyright

# Check formatting without modifying files (use in CI)
ruff format --check .
```

### Security & Dependency Hygiene
```bash
# Check for known vulnerabilities in dependencies
pip-audit

# Check for outdated dependencies
pip list --outdated

# Scan for common security issues in source (e.g., hardcoded secrets, unsafe calls)
bandit -r src/
```

### Cleaning
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
rm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info
```

## Code Style Guidelines

### Imports and Dependencies
- Follow PEP 8 import ordering: standard library, then third-party, then local/first-party, each group separated by a blank line. `ruff` (or `isort`) enforces this automatically.
- Prefer explicit imports over wildcard imports (`from module import specific_thing`, not `from module import *`).
- Use absolute imports within the package rather than relative imports where practical, except for tightly-coupled sibling modules.
- Example:
```python
import json
import os
from pathlib import Path

import httpx
from pydantic import BaseModel

from package_name.config import Settings
from package_name.models import Record
```

### Naming Conventions
- **Functions/variables**: `snake_case` (e.g., `parse_config`, `retry_count`)
- **Classes**: `PascalCase` (e.g., `RequestHandler`, `ConnectionPool`)
- **Constants**: `SCREAMING_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT_SECONDS`)
- **Modules/packages**: short, lowercase, `snake_case` if multi-word (e.g., `request_handler.py`). This holds for anything Python imports — kebab-case is not a valid Python identifier, so `All_address_types.py` is wrong, not `all-address-types.py`.
- **Directories and non-importable files**: lowercase `kebab-case` (e.g., `api/`, `gen/`, `net/`), named by role rather than by project.
- **"Private" attributes/methods**: prefix with a single underscore (`_internal_state`); use double-underscore name mangling (`__attr`) only when actually needed to avoid subclass collisions.
- Avoid single-letter variable names outside short comprehensions or loop counters.

### Type Hints
- Add type hints to all public function signatures (parameters and return types) at minimum; prefer hinting internal functions too.
- Use `from __future__ import annotations` (or target Python 3.10+) to allow modern union syntax (`str | None`) without runtime cost.
- Use `Optional[T]` / `T | None` explicitly rather than relying on an implicit default of `None`.
- Run a type checker (`mypy` or `pyright`) as part of CI; don't silently ignore type errors with blanket `# type: ignore` — scope ignores narrowly and explain why.
- Example:
```python
def load_config(path: str | Path) -> Config:
    """Load and validate configuration from the given path."""
    ...
```

### Error Handling
- Raise specific, meaningful exceptions rather than bare `Exception`; define custom exception classes for domain errors.
- Never use a bare `except:`; catch specific exception types, or `except Exception` only at a genuine top-level boundary (e.g., a request handler) where you log and re-raise or convert.
- Don't silently swallow exceptions — at minimum, log them with context.
- Use `raise ... from err` to preserve exception chains when re-raising as a different type.
- Example:
```python
class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


def load_config(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"config file not found: {path}")

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as err:
        raise ConfigError(f"invalid JSON in {path}: {err}") from err

    return Config(**data)
```

### Code Structure and Patterns
- Prefer early returns / guard clauses over deeply nested conditionals.
- Keep functions small and single-purpose; extract helpers once a function does more than one clear thing.
- Separate pure logic (no I/O, no side effects) from I/O and orchestration code to make testing easier.
- Prefer composition over inheritance; avoid deep class hierarchies unless the domain genuinely calls for it.
- Use dataclasses or `pydantic.BaseModel` for structured data instead of loose dicts, especially at module boundaries.
- Example:
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Summary:
    total: int
    valid_count: int
    errors: list[str]


def process_batch(records: list[Record]) -> Summary:
    if not records:
        raise ValueError("at least one record is required")

    validated = [r for r in records if r.is_valid()]
    errors = [r.error for r in records if not r.is_valid() and r.error]

    return Summary(total=len(records), valid_count=len(validated), errors=errors)
```

### Serialization and Data Validation
- Use `pydantic` (v2) for request/response models, config schemas, and any data crossing a boundary (API, file, environment).
- Use descriptive, stable field names for external formats; use `Field(alias=...)` if the external name differs from the idiomatic Python name.
- Use `Optional[T] = None` (or `T | None = None`) for genuinely optional fields, with explicit defaults rather than relying on implicit ones.
- Example:
```python
from pydantic import BaseModel, Field


class RequestPayload(BaseModel):
    id: str
    items: list[str]
    priority: int | None = Field(default=None, ge=0, le=10)
```

### Async Code (if applicable)
- Be explicit about the async framework in use (`asyncio`, `anyio`, `trio`) and don't mix concurrency primitives from different ecosystems.
- Never call blocking I/O (e.g., `requests`, synchronous file reads) inside an `async def` without offloading it (`asyncio.to_thread`, `run_in_executor`).
- Always `await` coroutines — a coroutine created but never awaited is a silent bug; enable `asyncio` debug mode or a linter rule to catch this.
- Prefer `async with` / `async for` for resources with async context managers/iterators.

### Testing Guidelines
- Write unit tests for all public functions and non-trivial private logic.
- Use descriptive test names that state the scenario and expectation (e.g., `test_parses_valid_config_with_all_fields`, `test_rejects_empty_input`).
- Follow Arrange/Act/Assert structure within tests.
- Test both success paths and failure/edge cases (empty input, boundary values, malformed data).
- Use `pytest` fixtures for shared setup instead of duplicating setup code; scope fixtures appropriately (`function`, `module`, `session`).
- Use `pytest.mark.parametrize` for testing multiple input/output combinations without duplicating test bodies.
- Mock external services/APIs in unit tests (`unittest.mock`, `pytest-mock`, or `respx`/`httpx` mocking for HTTP); keep true integration tests separate and clearly marked.
- Example:
```python
import pytest

from package_name.processing import process_batch, Record


def test_processes_valid_batch_successfully():
    records = [Record(id="1", value=42)]

    summary = process_batch(records)

    assert summary.total == 1
    assert summary.valid_count == 1


def test_rejects_empty_batch():
    with pytest.raises(ValueError, match="at least one record"):
        process_batch([])


@pytest.mark.parametrize(
    "value,expected_valid",
    [(0, True), (-1, False), (100, True)],
)
def test_record_validity_boundaries(value: int, expected_valid: bool):
    record = Record(id="1", value=value)

    assert record.is_valid() == expected_valid
```

### Documentation
- Add docstrings to all public modules, classes, and functions (Google or NumPy style — pick one and stay consistent).
- Include argument descriptions, return value description, and raised exceptions for non-trivial public functions.
- Keep docstring examples runnable/accurate; consider `doctest` for simple cases.
- Example:
```python
def load_config(path: Path) -> Config:
    """Load and validate configuration from disk.

    Args:
        path: Path to the configuration file.

    Returns:
        The parsed and validated Config object.

    Raises:
        ConfigError: If the file is missing or contains invalid JSON.
    """
    ...
```

### File Organization
- Use a `src/package_name/` layout to avoid accidental imports of the working directory instead of the installed package.
- Keep `__init__.py` files thin — re-export the public API, avoid heavy logic at import time.
- One logical concern per module; avoid large "utils.py" or "helpers.py" files that accumulate unrelated code.
- Keep tests in a top-level `tests/` directory mirroring the `src/` package structure.

### Performance Considerations
- Choose data structures deliberately (`dict`/`set` for O(1) lookups, `list` for ordered sequences, `collections.deque` for queue-like use).
- Avoid unnecessary copies of large data structures; use generators/iterators for large or streaming data instead of materializing full lists.
- Prefer list/dict/set comprehensions over manual loops where equally clear, but don't sacrifice readability for micro-optimization.
- Profile before optimizing (`cProfile`, `py-spy`, `line_profiler`) rather than guessing at bottlenecks.

### Dependency and Version Management
- Pin dependency versions (or version ranges) in `pyproject.toml`; use a lockfile (`poetry.lock`, `uv.lock`, or `requirements.txt` generated via `pip-compile`) for reproducible installs.
- State the minimum supported Python version explicitly (`requires-python = ">=3.10"`) and keep CI testing against it.
- Justify any new dependency, especially ones with native extensions, large transitive trees, or known maintenance concerns.
- Re-run `pip-audit` after any dependency update.

## Security Best Practices
- Never commit secrets, API keys, or credentials; use environment variables or a secrets manager, and add `.env` to `.gitignore`.
- Validate and sanitize all external input (user input, file contents, API responses) before use.
- Avoid `eval()`, `exec()`, and `pickle.loads()` on untrusted data.
- Use parameterized queries for any SQL; never build queries via string formatting/concatenation.
- Use `subprocess.run([...], shell=False)` with a list of arguments rather than `shell=True` with a string, to avoid shell injection.

## Common Patterns

### CLI Tool Structure
```python
import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Description of what this tool does")
    parser.add_argument("input", help="Input file path")
    parser.add_argument("-o", "--output", help="Optional output path")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    try:
        result = process(args.input)
    except ConfigError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(result)
    else:
        print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### API Handler Structure (example using FastAPI)
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class Request(BaseModel):
    items: list[str]


class Response(BaseModel):
    processed: int


@router.post("/process", response_model=Response)
async def process_handler(req: Request) -> Response:
    if not req.items:
        raise HTTPException(status_code=400, detail="items required")

    try:
        result = await process_request(req)
    except ProcessingError as err:
        raise HTTPException(status_code=500, detail=str(err)) from err

    return Response(processed=result.count)
```

## Final Checklist Before Committing
1. `pytest` passes (with coverage if configured).
2. `ruff check .` (or your linter) is clean.
3. `ruff format --check .` (or `black --check .`) passes.
4. `mypy src/` (or `pyright`) reports no new errors.
5. `pip-audit` shows no new vulnerabilities.
6. No secrets, credentials, or sensitive data committed.
7. Public API docstrings updated if signatures or behavior changed.

## Getting Help
- Run `python3 -m pydoc package_name` for local documentation browsing.
- Check `pyproject.toml` for dependency, tool configuration, and entry point information.
- Refer to the project's `README.md` for architecture and usage context.
