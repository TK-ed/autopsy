# Contributing to Mr. Autopsy

Thank you for considering contributing to **Mr. Autopsy**! 🎉

Contributions of all kinds are welcome, including bug fixes, new log parsers, anomaly detection improvements, documentation updates, and feature ideas.

## Prerequisites

Mr. Autopsy uses **uv** for Python dependency management and reproducible environments.

Install `uv` if you do not have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/TK-ed/autopsy.git
cd autopsy
```

### 2. Set up the development environment

Install dependencies and create the virtual environment:

```bash
uv sync
```

This will:

* Create a project virtual environment
* Install dependencies from `uv.lock`
* Install the project in editable mode

## Running the Project

Run the CLI using:

```bash
uv run autopsy --help
```

## Running Tests

Run the complete test suite:

```bash
uv run pytest -v
```

The pytest configuration automatically includes the project root in the Python path, so imports work correctly without additional setup.

## Linting and Formatting

Check code quality:

```bash
uv run ruff check .
```

Format code:

```bash
uv run ruff format .
```

Before submitting changes, run:

```bash
uv run ruff format .
uv run ruff check .
uv run pytest -v
```

## Project Structure

```text
autopsy/
├── autopsy/
│   ├── correlate/     # Timeline building and event correlation
│   ├── detect/        # Anomaly detection algorithms
│   ├── ingest/        # Log input sources
│   ├── parsers/       # Log format parsers
│   ├── report/        # Report generation
│   ├── utils/         # Shared utilities
│   └── cli.py         # CLI entry point
├── tests/             # Test suite
├── pyproject.toml     # Project configuration
└── uv.lock            # Locked dependencies
```

## Coding Guidelines

* Keep functions small and focused.
* Add tests for new functionality.
* Follow existing naming and project conventions.
* Avoid unnecessary dependencies.
* Prefer clear and maintainable code over premature optimization.

## Commit Messages

Use Conventional Commits where possible.

Examples:

```text
feat: add nginx log parser
fix: handle malformed json logs
docs: improve contributing guide
test: add anomaly detection tests
refactor: simplify timeline processing
chore: update dependencies
```

## Pull Requests

Before opening a pull request:

* Ensure all tests pass.
* Ensure Ruff checks pass.
* Keep changes focused and easy to review.
* Explain the motivation behind the change.
* Include relevant test coverage.

## Reporting Bugs

When reporting a bug, include:

* Operating system
* Python version
* Mr. Autopsy version or commit hash
* Command that caused the issue
* Expected behavior
* Actual behavior
* Error logs or stack trace

Please remove sensitive information from logs before sharing.

## Feature Requests

For feature requests, describe:

* The problem being solved.
* Why the current behavior is insufficient.
* Your proposed solution.

## Areas for Contribution

Contributions are especially welcome in:

* New log parsers
* Additional anomaly detectors
* Incident correlation improvements
* Report formats
* Performance improvements
* Documentation
* Test coverage

Thank you for helping improve Mr. Autopsy!
