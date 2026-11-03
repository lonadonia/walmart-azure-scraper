# Changelog

There is one entry for each delivery to the client's review, newest first. Each delivery keeps its own review tag,
and a tag is never moved. The collector's change history by release is in
[`docs/VERIFICATION.md`](source/walmart-oxylabs-1.5.2/docs/VERIFICATION.md).

## How this repository is updated

- **One source tree.** For each release, `source/` is replaced by the next frozen tree. An earlier tree stays
  available through its tag.
- **Live runs.** Each new live run gets its own folder, `data/<run>-<release that collected it>/`, for example
  `data/S6-1.5.1/`. An existing folder is never rewritten.
- **Evidence.** It goes under `evidence/<class>/`, with the release in the path where the class has one.
- **Each delivery** adds:
  - an entry here;
  - its own tag, `review-<release>-<YYYYMMDD>`, with the UTC date the tag was made;
  - freshly written manifests, with `SHA256SUMS.txt` written last.

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
