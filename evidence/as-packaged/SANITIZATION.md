# What was changed when this evidence was packaged

The files of folders 1 to 6, `accounts/` and `tools/` were packaged for release 1.5.1 and are carried byte for byte: their rows in `EVIDENCE_MANIFEST.csv` and `SANITIZATION_LOG.csv` are those of 1.5.1. Files of `7_release_1_5_2/` went through the same rules, using the sanitizer of release 1.5.1 again, which release 1.5.2 did not change.

Every file is listed in `EVIDENCE_MANIFEST.csv` with the SHA-256 of its source and of the packaged copy. Every file that differs from its source is also in `SANITIZATION_LOG.csv`, with the reason. There are two kinds of change, and nothing else is changed.

## Stored Walmart pages (`*.html.gz`)

The collector sanitizes a page before storing it: script bodies other than the page data and JSON-LD are removed, and values that could identify a browsing session or a person are replaced with `[REDACTED]` (`src/walmart_headless/sites/walmart/sanitize.py` in the source ZIP). So a stored page is not a byte-for-byte copy of what the provider answered.

The assembler passed each stored page through the same sanitizer of release 1.5.1 again. When that changed a page, it checked that the page data differs only in values now `[REDACTED]`, and that the HTML outside the page data is unchanged. Product, price, store and fulfillment data are not touched. A changed page is listed in `SANITIZATION_LOG.csv` with the SHA-256 of the source file and of the packaged file.

The hash a run's `record_map.json` gives for a page (`stored_page_sha256`) is the hash of the stored file: the source column of the log.

## Text files (logs, CSV, JSON, tools)

Three kinds of value are abbreviated wherever they appear, by the local rules:

- the test VM's public IP address;
- the operator's IP address;
- the Azure subscription ID.

The test VM's host name (scraper-test-vm) and its user (azureuser, Azure's default) are left as they ran in `7_release_1_5_2/owner_vm/`, as they were in 1.5.1's evidence: they name a test machine, not a person. Its public IP address is abbreviated by the rule above.

The operator's home and repository folders are shortened to `<home>` and `<repository>`. The workstation's host name is shortened to `<workstation>`: the collector names a worker `<host>:<process id>:w<n>`, so the parallel runs' worker names read `<workstation>:7524:w0`, for example. The other workstation folders, such as `C:\w7\...`, are left as they ran: they are working folders that say nothing about a person, and a path that matters is explained where it is used.

The two files in `4_historical_references/1_4_1/` are exempt: they are byte-identical copies of release 1.4.1's own `SHA256SUMS.txt` and `SOURCE_AND_RUN_MANIFEST.json`, so that their hashes can still be checked against that delivery. The manifest names the repository folder once, as it did in 1.4.1.

## Not packaged

- **The providers' raw answers** (`live/raw/*.body.gz`). They may hold session values the sanitizer removes, so they stay on the workstation. `RAW_ORIGINALS_MANIFEST.csv` in each run's folder gives each one's SHA-256 and size.
- **Keys and credentials.** The collector's database stores only a key's fingerprint. The delivery's secret scan opened every archive member and compressed page, and `PACKAGE_VERIFICATION.txt` gives its result.
- **The database itself.** Its tables are exported as CSV. The exports leave out no column that could hold a credential: none exists in those tables.
