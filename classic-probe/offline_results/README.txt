OFFLINE RESULTS of the Oxylabs Classic probe. No request was sent and no credential was read.
Revision: 627c804d66aa33fc423fd2296c8896c5d5c2c3d4. Clean export, installed with uv sync --frozen.
Run (UTC): 2026-11-01T19:53:47+00:00 to 2026-11-01T19:54:26+00:00.
Every command but the install ran with HTTP(S) sent to a closed local port and no OXYLABS variable; commands.csv lists each with its exit code.

01_pytest_standalone, junit_standalone.xml  the probe's tests, from the probe alone: SYNTHETIC responses, and real saved Walmart pages inside invented Classic envelopes. One test is skipped: it needs the collector beside the probe (README_FIRST.md).
07 to 09                                    the plan and validation. The rate card is the shipped placeholder: no rate is known.
10, 11, replay/, synthetic_inputs_of_the_replay/   the Walmart steps replayed against SYNTHETIC responses and an invented rate card (OFFLINE REPLAY). It shows the ledger and the stops work; it shows nothing about Classic.
12 to 14, export/, offline_campaign_manifest.json  an offline ledger: created, read and exported. Marked offline: it cannot back a live campaign.
15_live_is_refused                          live mode refused, exit 3, with what a campaign still lacks.
