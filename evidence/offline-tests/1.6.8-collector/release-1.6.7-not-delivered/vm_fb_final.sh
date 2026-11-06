#!/usr/bin/env bash
# Owner VM: the fail-before of the 1.6.7 tests (as committed in 7ee2fa1) on the frozen 1.6.6 collector tree.
# (vm_full.sh's own fail-before part did not run: its first block left the shell in c167, so its relative paths
# named files that do not exist; this script uses absolute paths only.) Isolated: ~/q167, own uv environment,
# throwaway PostgreSQL servers in temp dirs (pgserver). No provider request.
set -u
BASE="$HOME/q167"
NEW="$BASE/c167"
TREE="$BASE/fb166final"
LOG="$BASE/FAILBEFORE_1.6.7_ON_1.6.6_LINUX.log"
unset WALMART_COLLECTOR_TEST_DATABASE_URL
OS="$(. /etc/os-release; echo "$PRETTY_NAME"), kernel $(uname -r), $(uname -m)"
FILES="tests/unit/test_completeness_167.py tests/integration/test_category_mapping.py tests/integration/test_detail_path.py tests/integration/test_coverage_and_assortment.py"
[ -f "$BASE/r166.tar" ] && [ -d "$NEW/tests" ] || { echo "missing r166.tar or c167"; exit 2; }
rm -rf "$TREE" && mkdir -p "$TREE" && tar -xf "$BASE/r166.tar" -C "$TREE" || exit 2
for f in $FILES; do cp "$NEW/$f" "$TREE/$f" || exit 2; done
{
  echo "tree: frozen collector 1.6.6 (commit 39cc61f, tar sha256 $(sha256sum "$BASE/r166.tar" | cut -d' ' -f1)) with the tests of commit 7ee2fa1 copied in (from its clean extraction, tar sha256 $(sha256sum "$BASE/c167.tar" | cut -d' ' -f1))"
  echo "label: FAILBEFORE_1.6.7_ON_1.6.6_LINUX; host: $OS"
  for f in $FILES; do
    echo "copied $f sha256 $(sha256sum "$TREE/$f" | cut -d' ' -f1) (same as commit 7ee2fa1: $(cmp -s "$TREE/$f" "$NEW/$f" && echo yes || echo NO))"
  done
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd "$TREE" || exit 2
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
} > "$LOG" 2>&1
grep -E "^FAILED|passed|failed|pytest exit|same as commit|^tree|^label" "$LOG" | cut -c1-260 | tail -40
