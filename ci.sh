#!/usr/bin/env bash
set -euo pipefail

VENV_BIN="$(dirname "$0")/.venv/bin"
export PATH="$VENV_BIN:$PATH"

PASS=0
FAIL=0

run() {
    local name="$1"
    shift
    printf "%-40s" "$name..."
    if "$@" > /dev/null 2>&1; then
        echo "OK"
        PASS=$((PASS + 1))
    else
        echo "FAILED"
        FAIL=$((FAIL + 1))
        "$@" 2>&1 | sed 's/^/  /' || true
    fi
}

echo "=== Local CI ==="
echo

run "ruff lint"          ruff check .
echo "=================================================="
run "ruff format"        ruff format --check .
echo "=================================================="
run "mypy"               mypy pdf_*.py --ignore-missing-imports
echo "=================================================="
run "pip-audit"          pip-audit -r requirements.txt
echo "=================================================="
run "pytest"             pytest tests/ -v --cov=. --cov-fail-under=80 --cov-report=term-missing
echo "=================================================="

echo
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
