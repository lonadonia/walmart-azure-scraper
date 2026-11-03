SYNTHETIC TEST: publication faults, release 1.5.2 (627c804), on Hamza's Azure test VM, 2026-11-01T20:14Z to 20:16Z.

Not a retailer run. tests/integration/test_publication_safety.py ran from the delivered source (WALMART_SOURCE_1.5.2.zip,
the Oxylabs edition) against a fixture standing in for Walmart, on an isolated database and destination. No request left
the VM. The suite's result: 10 passed in 105.27 s (../logs/publication_faults.log; ../junit/test_publication_safety.xml).

Each file records one fault. A first run publishes; a second run meets the fault. "before" and "after" are the last-good
pointer, the published files' SHA-256 and the published products, read before and after the second run.

  Fault                                 Second run                                    Last-good publication
  publication_refused_incomplete        rejected, CREDITS_EXHAUSTED, exit 4           unchanged
  publication_refused_site_refusal      rejected, SITE_REFUSAL, exit 5                unchanged
  publication_refused_wrong_store       rejected, STORE_NOT_VERIFIED, exit 7          unchanged
  publication_refused_empty             rejected, exit 6                              unchanged
  publication_refused_thin              rejected, exit 6                              unchanged
  publication_refused_failed_detail     rejected, exit 6: the product-page path       unchanged
                                        paused after 3 refused or failed requests
  publication_refused_mixed_lineage     publishing refused, exit 6: a segment ran     unchanged
                                        with another lineage
  publication_interrupted_then_retried  interrupted, then retried (exit 0)            kept until the retry published
  publication_interrupted_run_then_resumed  stopped (exit 75); a manual publish       kept until the resumed run
                                        refused (exit 6); resumed (exit 0)            published
  publication_allowed_one_failed_detail published with one failed product page        replaced by version 2

In the refused cases the pointer, its version and the published files' SHA-256 are the same after the fault as before it.
The challenge names in the failed-detail case are the fixture's own: no challenge was met or answered.
