"""Writes scripts/build_walmart_161_delivery.py from build_walmart_152_delivery.py: release 1.6.1, the source
README's live-run table and container line for this delivery, and the probe README for the shared probe 1.7.0 (both
retailers, the C1 to C5 corrections, two vendored-file skips in a probe-only extraction). Run once."""

from pathlib import Path

SRC = Path(r"C:\w9\wt\scripts\build_walmart_152_delivery.py")
DST = Path(r"C:\w9\wt\scripts\build_walmart_161_delivery.py")
if DST.exists():
    raise SystemExit("already written")
s = SRC.read_text(encoding="utf-8")

PROBE_README = '''PROBE_README = """# Oxylabs Classic offline probe {version}: start here

An offline, reviewable probe for the Oxylabs **Classic** Web Scraper API. **It has never sent a request**: its live
mode is disabled in the code, and no credential is in this package.

This is the shared probe (Walmart and Mariano's on one ledger). Version 1.7.0 corrects the five findings of the
client's second review (C1 to C5) in the shared layer; the steps, the response checks, the limits and the Mariano's
adapter are those of 1.6.0. The Walmart probe 1.5.2 that the client reviewed is published unchanged beside it.

| What | Value |
| --- | --- |
| Probe version | {version} |
| Frozen revision | `{commit}` (the revision of Walmart release {release}) |
| The probe's own code last changed in | `{code_changed}` (C1 to C5); `{last_changed}` corrected three of its documents |
| Live mode | disabled: `gates.LIVE_ENABLED = False` in `oxylabs-classic-probe/src/classic_probe/gates.py` |
| Requests sent to Oxylabs or to a retailer | none |

## What is here

| Path | What |
| --- | --- |
| `oxylabs-classic-probe/` | the probe's tree, unchanged from that revision, with its `uv.lock`. Read its `README.md` |
| `oxylabs-classic-probe/CLASSIC_TEST_PLAN.md` | the staged plan for a future approved campaign |
| `oxylabs-classic-probe/docs/PAYLOAD_MATRIX.md` | every request the plan can send, its upper bound and its stops |
| `oxylabs-classic-probe/docs/DOCUMENTED_CONTRACT.md` | what the documentation says, page by page, with each saved page's SHA-256 |
| `offline_results/` | the outputs of the probe's offline run of this tree: tests, lint, types, plan, both replays, the refused live command. `offline_results/README.txt` says what each file is |
| `saved_documentation/` | the public Oxylabs pages the contract names, as published with probe 1.5.2 (the 1.7.0 contract cites the same pages) |
| `FILE_SHA256.txt` | the SHA-256 of every file of the probe's tree at that revision |
| `PACKAGE_MANIFEST.json` | this package's identity |

## Run it (offline)

Python 3.12 and [uv](https://docs.astral.sh/uv/) are the only prerequisites.

```
cd oxylabs-classic-probe
uv sync --frozen
uv run --frozen pytest
uv run --frozen ruff check src tests
uv run --frozen mypy
uv run --frozen classic-probe plan --targets config/targets.json
uv run --frozen classic-probe validate --targets config/targets.json --rates config/rates.example.json
```

The tests close the network: an attempt to open a socket or resolve a name fails the test that made it. Run from
this package alone, two tests are skipped: `test_the_vendored_files_are_still_the_collectors_files`, once for each
collector, compares the vendored page readers with the collector's own files, which are not beside the probe here.
Every vendored copy is still checked against its recorded Git object (`test_each_vendored_file_is_the_recorded_copy`).
The three Walmart readers are the same Git objects in collector 1.5.2, from which they were copied, and in {release}.

## What is not established

The Walmart tests use SYNTHETIC Classic responses; the Mariano's tests use real saved Mariano's pages inside invented
Classic envelopes (OFFLINE REPLAY). **They show nothing about what Classic returns**: no account, target entitlement,
rate, store context, fulfillment or pagination has been confirmed. The limits in the plan (10 requests per retailer,
20 in total, 30 minutes, USD 5 with USD 0.50 of headroom) are a proposal to the client, not an approval. Running a
campaign needs the account owner's Classic credentials, entitlements, confirmed rates and written approval, and a
later version of this probe with live mode enabled. The credential used for this delivery's live stages is an
Oxylabs Web API key, not a Classic username and password.
"""
'''

SOURCE_TABLE_OLD = (
    "| `walmart-oxylabs-{release}/` | Oxylabs Web API (Bearer key; not the Classic product) | none: the last live runs were "
    "on 1.5.1 (2026-10-31), and this release read their stored pages again offline |\n"
    "| `walmart-scrapedo-{release}/` | Scrape.do | none: the account had 10 of 1,000 monthly requests left |\n"
)
SOURCE_TABLE_NEW = (
    "| `walmart-oxylabs-{release}/` | Oxylabs Web API (Bearer key; not the Classic product) | the staged live runs of "
    "2026-11-03 from L3 on (L1 and L2 ran 1.6.0, the release before; see the review documents) |\n"
    "| `walmart-scrapedo-{release}/` | Scrape.do | none: built and tested offline; a live Scrape.do run needs access "
    "supplied separately |\n"
)
reps = [
    ('"""Build the Walmart release 1.5.2 delivery', '"""Build the Walmart release 1.6.1 delivery'),
    ('RELEASE = "1.5.2"\nFIXED_TIME = (2026, 11, 2, 0, 0, 0)\n', 'RELEASE = "1.6.1"\nFIXED_TIME = (2026, 11, 3, 0, 0, 0)\n'),
    (SOURCE_TABLE_OLD, SOURCE_TABLE_NEW),
    (
        "| `Dockerfile` | the container image, built and run on the owner's Azure test VM for this delivery |\n",
        "| `Dockerfile` | the container image. Not built for {release}: the workstation has no container runtime. Its "
        "recipe is 1.5.2's, which was built and run on the owner's Azure test VM, with two comment lines changed |\n",
    ),
    (
        '    last = git("log", "-1", "--format=%H", commit, "--", PROBE).decode().strip()\n',
        '    last = git("log", "-1", "--format=%H", commit, "--", PROBE).decode().strip()\n'
        '    code_changed = git("log", "-1", "--format=%H", commit, "--", PROBE + "/src").decode().strip()\n',
    ),
    (
        '            "tests": "SYNTHETIC TEST (invented Classic responses) and OFFLINE REPLAY (real saved Walmart pages '
        'inside invented Classic envelopes)",\n',
        '            "tests": "SYNTHETIC TEST (invented Classic responses) and OFFLINE REPLAY (real saved Walmart and '
        'Mariano\'s pages inside invented Classic envelopes)",\n',
    ),
    (
        '        "files_of_the_probe_tree": len(tree),\n',
        '        "probe_code_last_changed_in_src": code_changed,\n        "files_of_the_probe_tree": len(tree),\n',
    ),
    (
        "    readme = PROBE_README.format(version=version, commit=commit, release=RELEASE, last_changed=last)\n",
        "    readme = PROBE_README.format(version=version, commit=commit, release=RELEASE, last_changed=last,\n"
        "                                 code_changed=code_changed)\n",
    ),
]
for a, b in reps:
    assert s.count(a) == 1, a[:90]
    s = s.replace(a, b)
start = s.index('PROBE_README = """')
end = s.index('"""\n', start + len('PROBE_README = """')) + 4
s = s[:start] + PROBE_README + s[end:]
for old in ("1.5.2", "1_5_2", "152"):
    left = [ln for ln in s.splitlines() if old in ln]
    print(old, len(left), left[:6])
DST.write_bytes(s.encode("utf-8"))
print("written", DST)
