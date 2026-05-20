# Contributing to py-autotask

Thanks for your interest in contributing! This document covers the basics for
getting set up and submitting changes.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/ -q
```

Linting and type checks are configured via pre-commit:

```bash
pre-commit install
pre-commit run --all-files
```

## Submitting changes

1. Fork the repository and create a feature branch off `main`.
2. Make your changes with clear, focused commits.
3. Add or update tests for any behavior change.
4. Update `CHANGELOG.md` following the
   [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format.
5. Ensure `pytest` and `pre-commit` pass.
6. Open a pull request describing the change and its motivation.

## Code of Conduct

By participating in this project you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).
