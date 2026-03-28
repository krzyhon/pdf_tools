#!/usr/bin/env bash
set -euo pipefail

PASS=0
FAIL=0

run() {
    local name="$1"
    shift
    printf "%-40s" "$name..."
    if "$@" > /dev/null 2>&1; then
        echo "OK"
        ((PASS++))
    else
        echo "FAILED"
        ((FAIL++))
        "$@" 2>&1 | sed 's/^/  /'
    fi
}

echo "=== Local CI ==="
echo

run "ruff lint"          ruff check .
run "ruff format"        ruff format --check .
run "mypy"               mypy pdf_*.py --ignore-missing-imports
run "pip-audit"          pip-audit -r requirements.txt
run "pytest"             pytest tests/ -v

echo
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
