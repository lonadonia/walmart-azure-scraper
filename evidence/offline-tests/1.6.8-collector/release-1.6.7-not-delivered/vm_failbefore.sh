#!/usr/bin/env bash
# Fail-before of the release 1.6.7 tests on the frozen 1.6.6 collector (commit 39cc61f), owner VM.
# Isolated: its own folder (~/q167), its own uv environment, a throwaway PostgreSQL (pgserver, temp dir).
set -u
BASE="$HOME/q167"
TREE="$BASE/fb166"
LOG="$BASE/FAILBEFORE_1.6.7_TESTS_ON_1.6.6_LINUX.log"
cd "$BASE" || exit 2
rm -rf "$TREE" && mkdir -p "$TREE" && tar -xf r166.tar -C "$TREE"
cp new_tests/test_completeness_167.py "$TREE/tests/unit/"
cp new_tests/test_category_mapping.py "$TREE/tests/integration/"
cp new_tests/test_detail_path.py "$TREE/tests/integration/"
{
  echo "tree: frozen collector 1.6.6 (commit 39cc61f, tar sha256 $(sha256sum r166.tar | cut -d' ' -f1)) with the 1.6.7 tests copied in"
  echo "label: FAILBEFORE_1.6.7_TESTS_ON_1.6.6_LINUX; host OS: $(. /etc/os-release; echo "$PRETTY_NAME"), kernel $(uname -r), $(uname -m)"
  for f in tests/unit/test_completeness_167.py tests/integration/test_category_mapping.py tests/integration/test_detail_path.py; do
    echo "copied test $f sha256 $(sha256sum "$TREE/$f" | cut -d' ' -f1)"
  done
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd "$TREE"
  grep -n '^version' pyproject.toml
  uv --version
  unset WALMART_COLLECTOR_TEST_DATABASE_URL
  uv sync --frozen 2>&1 | tail -3; echo "sync exit ${PIPESTATUS[0]}"
  uv run --frozen python --version
  uv run --frozen python -m pytest -p no:cacheprovider -q -rfE \
    tests/unit/test_completeness_167.py \
    tests/integration/test_category_mapping.py \
    tests/integration/test_detail_path.py 2>&1
  echo "pytest exit code ${PIPESTATUS[0]}"
  echo "ended $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$LOG" 2>&1
tail -25 "$LOG"
