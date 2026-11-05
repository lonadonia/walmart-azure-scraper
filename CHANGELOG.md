# Changelog

There is one entry for each delivery to the client's review, newest first. Each delivery keeps its own review tag,
and a tag is never moved. The collector's change history by release is in
[`docs/VERIFICATION.md`](source/walmart-oxylabs-1.6.6/docs/VERIFICATION.md).

## How this repository is updated

- **One source tree.** For each release, `source/` is replaced by the next frozen tree. An earlier tree stays
  available through its tag.
- **Live runs.** The product files of a delivered live run get their own folder, `data/<run>-<release that
  collected it>/`, for example `data/S6-1.5.1/`. Every run's exports are in its evidence folder. An existing folder
  is never rewritten.
- **Evidence.** It goes under `evidence/<class>/`, with the release in the path where the class has one.
- **Each delivery** adds:
  - an entry here;
  - its own tag, `review-<release>-<YYYYMMDD>`, with the UTC date the tag was made;
  - freshly written manifests, with `SHA256SUMS.txt` written last.

## 1.6.6: correction delivery, published 2026-11-05 (tag `review-1.6.6-20261105`)

- **Collector:** release 1.6.6, commit `39cc61f61ee694c0659a611310605bee6ed42d6b`, 2026-11-04T22:34:53Z. The
  archives were built at `cbea802`, which adds only their builder. The shared Classic probe is 1.7.1
  ([`classic-probe-1.7.1/`](classic-probe-1.7.1/)). The probe 1.7.0 stays in
  [`classic-probe-1.7.0/`](classic-probe-1.7.0/), unchanged, and the Walmart probe 1.5.2 in
  [`classic-probe/`](classic-probe/).
- **Corrections** (the client's review of 1.6.5; see [`review/CORRECTION_MAP.md`](review/CORRECTION_MAP.md)):
  - Classic C2 and C4 are completed in probe 1.7.1. The deadline holds through recovery, export and cleanup. Each
    answer is kept durably, across a crash, before the next paid step, and a body cut at its deadline is recorded.
    Seven reproduction tests fail on 1.7.0 and pass on 1.7.1.
  - A refused automatic publication is an `ERROR` and exits 6, also on Azure's retry (collector 1.6.6). The
    operations guide's alert advice names it.
  - The 1.6.5 statements that were not accurate are corrected, among them "C1 to C5 corrected (probe 1.7.0)" and the
    pass given to the operating documentation's monitoring. See
    [`manifests/DOC_CORRECTIONS.md`](manifests/DOC_CORRECTIONS.md).
- **Live data:** one new run, L12 on 1.6.6 (2026-11-04T22:52Z to 22:59Z). It is a canary with product-page
  collection on: 40 fresh valid products, 10 product pages read, UPC 27 of 40, three UPCs read that had never been
  read. It is a rejected pilot. Its evidence is in `evidence/live/1.6.x/runs/`, and it adds no `data/` folder.
  `data/RUN_SUMMARY.json` gains its entry; every other file of `data/` is unchanged. The demonstration of 500 or more
  with detail on, on 1.6.6, was not funded: USD 0.003 of Walmart's share is left.
- **Verification:** both 1.6.6 edition ZIPs from clean extractions
  ([`evidence/verification/1.6.6/`](evidence/verification/1.6.6/)); the probe 1.7.1 from its own export
  ([`classic-probe-1.7.1/offline_results/`](classic-probe-1.7.1/offline_results/)). Nothing ran in the client's
  environment.
- **States:** [`review/REQUIREMENT_MATRIX.md`](review/REQUIREMENT_MATRIX.md) and the four 1.6.6 columns of
  [`review/ACCEPTANCE_MATRIX.csv`](review/ACCEPTANCE_MATRIX.csv).

## 1.6.5: correction delivery, published 2026-11-04 (tag `review-1.6.5-20261104`)

- **Collector:** release 1.6.5, commit `67d216eb8ee2ec839a437b0b5bf2d594324b6982`, 2026-11-04. It follows 1.6.0 to
  1.6.4, which were not published separately; their changes are in this delivery. The shared Classic probe is
  1.7.0 ([`classic-probe-1.7.0/`](classic-probe-1.7.0/)). The Walmart probe 1.5.2 stays in
  [`classic-probe/`](classic-probe/), unchanged.
- **Corrections** (see [`review/CORRECTION_MAP.md`](review/CORRECTION_MAP.md)):
  - the four deal fields are always `""`, the client's clarification (1.6.0);
  - saved product-page reads are used when a run ends early, when detail reading is off, and for carried rows
    (1.6.1, 1.6.3);
  - a listing whose total moves while it is read is never `DONE`; a link that serves a category page is recorded
    (1.6.2);
  - Walmart's not-found page is recognized (1.6.3);
  - a listing total of 0 is a total (1.6.4);
  - the independent source check reads the flat price strings some pages use (1.6.5);
  - the Classic findings C1 to C5 are corrected offline (probe 1.7.0). (Corrected in 1.6.6: C1, C3 and C5 were;
    C2 and C4 were corrected only in part, and are completed in probe 1.7.1.)
- **Live data:** fourteen runs of the user's Oxylabs Web API trial, 2026-11-03 and 2026-11-04, each on the release
  that ran it. [`data/L10-1.6.4/`](data/L10-1.6.4/) is the census of release 1.6.4 (7,055 fresh valid, detail
  reading off); its export passes the final release's check. [`data/L8-1.6.3/`](data/L8-1.6.3/) is the last
  demonstration with detail reading on (675 fresh valid). 1.6.5's own live runs are two canaries. The 1.5.x folders
  of `data/` are unchanged. The full catalogue was not read.
- **Verification:** the suites of every release on its commit, and both 1.6.5 edition ZIPs from clean extractions
  ([`evidence/verification/1.6.5/`](evidence/verification/1.6.5/)). Nothing ran in the client's environment.
- **States:** `review/REQUIREMENT_MATRIX.md` and the four 1.6.5 columns of `review/ACCEPTANCE_MATRIX.csv`, as
  published at the tag `review-1.6.5-20261104`.

## 1.5.2: correction delivery, published 2026-11-03 (tag `review-1.5.2-20261103`)

- **Collector:** release 1.5.2, commit `627c804d66aa33fc423fd2296c8896c5d5c2c3d4`, 2026-11-01. The Classic probe is
  1.5.2, frozen at the same revision. This is the first publication in this repository.
- **Corrections:** see [`review/CORRECTION_MAP.md`](review/CORRECTION_MAP.md).
  - Each provenance file now names the real capture of a recovered value.
  - Sizes and packs: "30 lb" became "2 pack, 30 lb" on five carried rows, and "2 pack, 1 Pack" became "2 pack". Both
    sizes of a set of two are kept.
  - `blocked` and `request_failed` replace one failure class.
  - An interrupted replay resumes as a replay.
  - A row carried from a replay names the live run that read it.
  - Six private-label brands are confirmed from USPTO records.
- **Live data:** there is no new live run. [`data/`](data/) carries these runs of 2026-10-31:
  - S6, on 1.5.1: 580 valid, distinct fresh products;
  - S7, on 1.5.1;
  - S4, on 1.5.0.
- **Verification of 1.5.2:** offline only. It consists of tests, replays of the stored pages, and the owner's Azure
  test VM with no provider request.
- **Publication changes:** paths were rewritten to this layout. Notes in the review documents were corrected, among
  them an erratum on the set of two sizes. Some files were redacted and others left out. Everything is listed in
  [`manifests/`](manifests/).

## 1.5.1: collector `488a033`, 2026-10-31

This release corrected what the bounded live campaign showed in 1.5.0:
- a multipack is kept beside the size;
- inches, load ratings and strengths are not taken as sizes;
- a Walmart brand after a bracketed multipack is recognised, and two more brand wordings are listed;
- a page budget no longer blanks what earlier reads established.

It ran S6 and S7 live. It is not published here as a release of its own; its live files are in [`data/`](data/).

## 1.5.0: collector `7b6f325`, 2026-10-31

This release answered the client's review of 1.4.1:
- the product detail path;
- pack size told apart from serving size;
- the volume-offer rule;
- the Walmart-seller rule;
- schedule occurrences;
- publication faults.

It ran S1 to S5 live. Its S4 files are in [`data/S4-1.5.0/`](data/S4-1.5.0/).

## 1.4.1: collector `37ffca8`, 2026-10-28

The release the client reviewed. It is not republished here: references to
`shared/WALMART_SHARED_EVIDENCE_1.4.1.zip` point into that delivery.
