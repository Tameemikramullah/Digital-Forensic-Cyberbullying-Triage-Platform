#!/usr/bin/env bash
# Runs the pytest suite from the project root using the root virtualenv.
#
# The root is required: pytest.ini sets `pythonpath = backend`, and running
# from the root also keeps relative paths (.env, sqlite:///./forensic_triage.db,
# UPLOAD_DIR) resolving against the project root instead of backend/.
#
# Extra arguments are forwarded to pytest, e.g.:
#   ./tests/run_tests.sh -k ensemble -x
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  echo "WARNING: no .venv at the project root; falling back to system python3." >&2
  PYTHON="python3"
else
  PYTHON="python"
fi

if ! "$PYTHON" -c "import pytest" >/dev/null 2>&1; then
  echo "ERROR: pytest is not available to '$PYTHON'." >&2
  echo "       Create the virtualenv and install dependencies first:" >&2
  echo "         python3 -m venv .venv && . .venv/bin/activate" >&2
  echo "         python -m pip install -r backend/requirements.txt" >&2
  exit 1
fi

exec "$PYTHON" -m pytest -v "$@"