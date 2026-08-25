#!/usr/bin/env bash
set -e

echo "========================================"
echo " 🔍 Running Local CI Checks"
echo "========================================"

echo ""
echo "1. Checking code style with Ruff..."
pip install ruff > /dev/null 2>&1 || true
ruff check app tests

echo ""
echo "2. Running complete test suite with coverage..."
pytest --cov=app --cov-report=term-missing

echo ""
echo "========================================"
echo " ✅ All CI checks passed successfully!"
echo "========================================"
