#!/usr/bin/env bash
# Owner VM: the collector suite of commit 7ee2fa1 (clean extraction) on Linux, then the fail-before of the 1.6.7
# tests (as committed) on the frozen 1.6.6 tree. Isolated: ~/q167, own uv environments, throwaway PostgreSQL
# servers in temp dirs (pgserver). No provider request.
set -u
BASE="$HOME/q167"
cd "$BASE" || exit 2
unset WALMART_COLLECTOR_TEST_DATABASE_URL
OS="$(. /etc/os-release; echo "$PRETTY_NAME"), kernel $(uname -r), $(uname -m)"

rm -rf c167 && mkdir c167 && tar -xf c167.tar -C c167
{
  echo "tree: commit 7ee2fa1 collector tree (git archive, core.autocrlf=false), tar sha256 $(sha256sum c167.tar | cut -d' ' -f1)"
  echo "host: $OS; started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd c167
  uv --version
  uv sync --frozen 2>&1 | tail -2; echo "sync exit ${PIPESTATUS[0]}"
  uv run --frozen python --version
  echo "== ruff check"; uv run --frozen ruff check src tests; echo "exit $?"
  echo "== ruff format --check"; uv run --frozen ruff format --check src tests; echo "exit $?"
  echo "== mypy"; uv run --frozen mypy; echo "exit $?"
  echo "== uv lock --check"; uv lock --check --offline; echo "exit $?"
  echo "== unit $(date -u +%H:%M:%SZ)"
  uv run --frozen python -m pytest -p no:cacheprovider -q -rfEs tests/unit 2>&1 | tail -6; echo "exit ${PIPESTATUS[0]}"
  for f in tests/integration/test_*.py; do
    echo "== $f $(date -u +%H:%M:%SZ)"
    timeout 1800 uv run --frozen python -m pytest -p no:cacheprovider -q -rfEs "$f" 2>&1 | tail -8
    echo "exit ${PIPESTATUS[0]}"
  done
  echo "ALL DONE $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$BASE/FULL_1.6.7_LINUX.log" 2>&1

# Fail-before: the 1.6.7 tests as committed, copied into the frozen 1.6.6 tree.
TREE="$BASE/fb166final"
rm -rf "$TREE" && mkdir -p "$TREE" && tar -xf r166.tar -C "$TREE"
for f in tests/unit/test_completeness_167.py tests/integration/test_category_mapping.py \
         tests/integration/test_detail_path.py tests/integration/test_coverage_and_assortment.py; do
  cp "c167/$f" "$TREE/$f"
done
{
  echo "tree: frozen collector 1.6.6 (commit 39cc61f, tar sha256 $(sha256sum r166.tar | cut -d' ' -f1)) with the tests of commit 7ee2fa1 copied in"
  echo "label: FAILBEFORE_1.6.7_ON_1.6.6_LINUX; host: $OS"
  for f in tests/unit/test_completeness_167.py tests/integration/test_category_mapping.py \
           tests/integration/test_detail_path.py tests/integration/test_coverage_and_assortment.py; do
    echo "copied $f sha256 $(sha256sum "$TREE/$f" | cut -d' ' -f1) (same as commit 7ee2fa1: $(cmp -s "$TREE/$f" "c167/$f" && echo yes || echo NO))"
  done
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd "$TREE"
  grep -n '^version' pyproject.toml
  uv sync --frozen 2>&1 | tail -1; echo "sync exit ${PIPESTATUS[0]}"
  uv run --frozen python -m pytest -p no:cacheprovider -q -rfE \
    tests/unit/test_completeness_167.py \
    tests/integration/test_category_mapping.py \
    "tests/integration/test_detail_path.py::test_a_size_conflict_never_withholds_the_upc_the_same_read_verifies_for_a_carried_row" \
    "tests/integration/test_coverage_and_assortment.py::test_the_coverage_report_judges_a_partition_through_its_children_and_gives_each_csv_row_its_verdict" \
    "tests/integration/test_coverage_and_assortment.py::test_a_partition_whose_total_moved_leaves_its_csv_row_incomplete_in_the_report" \
    2>&1
  echo "pytest exit code ${PIPESTATUS[0]}"
  echo "ended $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$BASE/FAILBEFORE_1.6.7_ON_1.6.6_LINUX.log" 2>&1
grep -E "^==|passed|failed|skipped|^exit|ALL DONE" "$BASE/FULL_1.6.7_LINUX.log" | tail -70
echo "---- fail-before"
grep -E "^FAILED|passed|failed|pytest exit|same as commit" "$BASE/FAILBEFORE_1.6.7_ON_1.6.6_LINUX.log" | tail -30
