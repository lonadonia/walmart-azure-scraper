OFFLINE RESULTS of the Oxylabs Classic probe. No request was sent and no credential was read.
Revision: cbea802891d4e66b74a0abc33e0af0af74c89708. Clean export, installed with uv sync --frozen.
Run (UTC): 2026-11-04T22:43:25+00:00 to 2026-11-04T22:48:29+00:00.
Every command but the two installs (00, 16a) ran with HTTP(S) sent to a closed local port and no OXYLABS variable; commands.csv lists each with its exit code. A command is as_expected only when its exit code is the expected one and, where output_must_say is set, its output says that too (an exit code alone does not show that a test ran).

01_pytest_standalone, junit_standalone.xml  the probe's tests, from the probe alone: SYNTHETIC responses, and real saved Walmart pages inside invented Classic envelopes. Skipped tests say why (-rs): see README_FIRST.md.
07 to 09                                    the plan and validation. The rate card is the shipped placeholder: no rate is known.
10, 11, replay/, synthetic_inputs_of_the_replay/   the Walmart steps replayed against SYNTHETIC responses and an invented rate card (OFFLINE REPLAY). It shows the ledger and the stops work; it shows nothing about Classic.
11b, 11c, replay_marianos/, inputs_of_the_marianos_replay/   the Mariano's steps replayed against real saved Mariano's pages in invented Classic envelopes, with an invented rate card (OFFLINE REPLAY). It shows nothing about Classic.
12 to 14, export/, offline_campaign_manifest.json  an offline ledger: created, read and exported. Marked offline: it cannot back a live campaign.
15_live_is_refused                          live mode refused, exit 3, with what a campaign still lacks.
16a, 16b                                    the reproduction tests of 1.7.1 (tests/test_c2_c4_reproduction.py, with tests/session_drill.py) run against the src/ of probe 1.7.0 (revision 6b9be92): a second clean export of this revision whose src/ was replaced by that of 1.7.0, installed from the same lockfile. 16b must exit 1 and report 7 failed (C2 and C4 as 1.7.0 left them).
17_reproductions_on_1.7.1                   the same 7 tests on this revision: they must report 7 passed.
junit_standalone.xml: its hostname attribute reads (workstation); the workstation's name was replaced before packing, and nothing else in the file was changed.
