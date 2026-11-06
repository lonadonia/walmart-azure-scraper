#!/usr/bin/env bash
# Owner VM: the collector suite of commit 85c29e7 (release 1.6.8, fourth candidate; a clean extraction of its tree)
# on Linux, then two fail-befores: the 1.6.8 tests (as committed in 85c29e7) on the frozen 1.6.7 collector tree
# (commit 7ee2fa1), and the fourth candidate's tests on the third candidate's tree (commit 9c14425). The first
# candidate 745607e failed one test of this suite; the second, 7a96218, renamed carried records after a filtered
# view's link (found by its replay of L12 on the workstation); the third, 9c14425, took only a link's listing ID for
# what the link shows (found on the workstation against the stored links' full URLs; never run on this VM).
# Isolated: ~/q168d, own uv environments, throwaway PostgreSQL servers in temp dirs (pgserver). No provider request.
# Absolute paths only.
set -u
BASE="$HOME/q168d"
NEW="$BASE/c168d"
OLD_TAR="$HOME/q167/c167.tar"
TREE="$BASE/fb167d"
FULL="$BASE/FULL_1.6.8d_LINUX.log"
FB="$BASE/FAILBEFORE_1.6.8d_ON_1.6.7_LINUX.log"
B_TAR="$BASE/c168c.tar"  # git archive of the third candidate 9c14425
TREE2="$BASE/fb168c"
FB2="$BASE/FAILBEFORE_1.6.8d_ON_9c14425_LINUX.log"
# git archive of a tree sets every file's time to the archive time, so a tar's own hash is not reproducible; the
# digest of its files' contents is (sha256 of the sorted "sha256  ./path" lines), checked against the commit's.
NEW_CONTENT=e7d515a098827493e4de670988da129b3bb764129c1245447dc05ece7717bc81
B_CONTENT=c6d72db2a5a86deaa451e9addb1df21d9210ad972a6c0c2c78707bd10506710b
OLD_CONTENT=5ca22e6440f3f97883a7dedca857b981f925f000e295a853150d8097801152d6
unset WALMART_COLLECTOR_TEST_DATABASE_URL
OS="$(. /etc/os-release; echo "$PRETTY_NAME"), kernel $(uname -r), $(uname -m)"
content() { ( cd "$1" && find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum | sha256sum | cut -d' ' -f1 ); }
FB_FILES="tests/mock_scrapedo.py tests/integration/test_scrapedo_walmart.py tests/integration/test_operations.py tests/integration/test_publication_safety.py tests/integration/test_coverage_and_assortment.py tests/integration/test_category_mapping.py tests/unit/test_subcategory_pages_168.py tests/unit/test_filtered_views_168.py"
T=tests/integration/test_scrapedo_walmart.py

rm -rf "$NEW" && mkdir -p "$NEW" && tar -xf "$BASE/c168d.tar" -C "$NEW" || exit 2
[ "$(content "$NEW")" = "$NEW_CONTENT" ] || { echo "c168d content digest differs"; exit 2; }
{
  echo "tree: commit 85c29e7b2404500299056973f50c84b84e187a5a collector tree (git archive 85c29e7:headless/walmart-azure-headless, core.autocrlf=false),"
  echo "  $(tar -tf "$BASE/c168d.tar" | grep -vc '/$') files, content digest $NEW_CONTENT (equal to the commit's)"
  echo "host: $OS; started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd "$NEW" || exit 2
  grep -n '^version' pyproject.toml
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
} > "$FULL" 2>&1

# Fail-before: the 1.6.8 tests as committed, copied into the frozen 1.6.7 tree.
rm -rf "$TREE" && mkdir -p "$TREE" && tar -xf "$OLD_TAR" -C "$TREE" || exit 2
[ "$(content "$TREE")" = "$OLD_CONTENT" ] || { echo "c167 content digest differs"; exit 2; }
for f in $FB_FILES; do cp "$NEW/$f" "$TREE/$f" || exit 2; done
{
  echo "tree: frozen collector 1.6.7 (commit 7ee2fa1, git archive, content digest $OLD_CONTENT, equal to the commit's)"
  echo "  with the tests of commit 85c29e7 copied in (from its clean extraction above)"
  echo "label: FAILBEFORE_1.6.8d_ON_1.6.7_LINUX; host: $OS"
  for f in $FB_FILES; do
    echo "copied $f sha256 $(sha256sum "$TREE/$f" | cut -d' ' -f1) (same as commit 85c29e7: $(cmp -s "$TREE/$f" "$NEW/$f" && echo yes || echo NO))"
  done
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd "$TREE" || exit 2
  grep -n '^version' pyproject.toml
  uv sync --frozen 2>&1 | tail -1; echo "sync exit ${PIPESTATUS[0]}"
  uv run --frozen python -c "import walmart_headless as w; print('import check:', w.__file__, w.__version__)"
  echo "== integration: the five 1.6.8 tests (expected to FAIL by their own assertions) and three controls whose"
  echo "   credit budget 1.6.8 raised by one (expected to pass on 1.6.7 as on 1.6.8)"
  uv run --frozen python -m pytest -p no:cacheprovider -q -rfEP \
    "$T::test_a_subcategory_with_a_category_page_of_its_own_is_read_through_the_listings_it_names" \
    "$T::test_a_subcategory_page_the_site_does_not_serve_keeps_its_row_incomplete" \
    "$T::test_a_subcategory_page_an_earlier_release_skipped_keeps_its_row_open_in_the_coverage_report" \
    "$T::test_a_run_checks_every_page_against_the_store_and_charges_the_ledger" \
    "tests/integration/test_coverage_and_assortment.py::test_the_category_page_is_read_through_the_general_api_never_the_store_plugin" \
    "$T::test_an_exhausted_key_stops_the_run_resumably_and_nothing_else_is_tried" \
    "tests/integration/test_operations.py::test_a_complete_run_is_published_and_a_partial_run_never_replaces_it" \
    "tests/integration/test_publication_safety.py::test_a_published_dataset_is_never_replaced_by_a_run_that_fails_its_checks" \
    2>&1
  echo "pytest exit code ${PIPESTATUS[0]}"
  echo "== unit: tests/unit/test_subcategory_pages_168.py (the functions 1.6.8 adds: expected to fail on import)"
  uv run --frozen python -m pytest -p no:cacheprovider -q -rfE tests/unit/test_subcategory_pages_168.py 2>&1 | tail -12
  echo "pytest exit code ${PIPESTATUS[0]}"
  echo "== unit: tests/unit/test_filtered_views_168.py (the functions the fourth candidate adds: expected to fail)"
  uv run --frozen python -m pytest -p no:cacheprovider -q -rfE tests/unit/test_filtered_views_168.py 2>&1 | tail -14
  echo "pytest exit code ${PIPESTATUS[0]}"
  echo "== integration: tests/integration/test_category_mapping.py of 85c29e7 on 1.6.7 (the 1.6.8 tests in it expected to fail)"
  uv run --frozen python -m pytest -p no:cacheprovider -q -rfE tests/integration/test_category_mapping.py 2>&1 | grep -v '^{"ts"' | tail -24
  echo "pytest exit code ${PIPESTATUS[0]}"
  echo "ended $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$FB" 2>&1

# Fail-before of the fourth candidate: its test files as committed in 85c29e7, copied into the third candidate's tree
# (commit 9c14425): test_category_mapping.py (seven new tests expected to fail by their own assertions, seven earlier
# ones to pass), test_filtered_views_168.py (the functions the fourth candidate adds) and test_subcategory_pages_168.py
# (the pin of the coverage report's last columns).
rm -rf "$TREE2" && mkdir -p "$TREE2" && tar -xf "$B_TAR" -C "$TREE2" || exit 2
[ "$(content "$TREE2")" = "$B_CONTENT" ] || { echo "c168c content digest differs"; exit 2; }
FB2_FILES="tests/integration/test_category_mapping.py tests/unit/test_filtered_views_168.py tests/unit/test_subcategory_pages_168.py"
for f in $FB2_FILES; do cp "$NEW/$f" "$TREE2/$f" || exit 2; done
{
  echo "tree: the third 1.6.8 candidate (commit 9c14425, git archive, content digest $B_CONTENT, equal to the commit's)"
  echo "  with these files of commit 85c29e7 copied in (from its clean extraction above)"
  echo "label: FAILBEFORE_1.6.8d_ON_9c14425_LINUX; host: $OS"
  for f in $FB2_FILES; do
    echo "copied $f sha256 $(sha256sum "$TREE2/$f" | cut -d' ' -f1) (same as commit 85c29e7: $(cmp -s "$TREE2/$f" "$NEW/$f" && echo yes || echo NO))"
  done
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  cd "$TREE2" || exit 2
  grep -n '^version' pyproject.toml
  uv sync --frozen 2>&1 | tail -1; echo "sync exit ${PIPESTATUS[0]}"
  uv run --frozen python -c "import walmart_headless as w; print('import check:', w.__file__, w.__version__)"
  for f in $FB2_FILES; do
    echo "== $f"
    uv run --frozen python -m pytest -p no:cacheprovider -q -rfEP "$f" 2>&1 | grep -v '^{"ts"'
    echo "pytest exit code ${PIPESTATUS[0]}"
  done
  echo "ended $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$FB2" 2>&1
grep -E "^==|passed|failed|skipped|^exit|ALL DONE" "$FULL" | tail -70
echo "---- fail-before on 1.6.7"
grep -E "^FAILED|^PASSED|^ERROR|^E  |passed|failed|pytest exit|same as commit" "$FB" | cut -c1-260 | tail -40
echo "---- fail-before on 9c14425"
grep -E "^FAILED|^PASSED|^ERROR|^E  |passed|failed|pytest exit|same as commit|import check" "$FB2" | cut -c1-260 | tail -40
