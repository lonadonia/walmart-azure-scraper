# The source check defect of release 1.6.4, and its correction in 1.6.5

Offline: no request was made for any file here. Everything is read from what the live runs stored.

## What happened

Live census L10 (run `01M6KA3CKYJSD6WDY4TDAAV73Y`, release 1.6.4) read 10,301 records. The collector's own
`validate-export --run` then exited 6 (step 162, `../../../live/1.6.x/campaign/logs/162_l10_validate_export.jsonl`).
Its independent source check reported 21 records as mismatches against the stored pages. The run's own end-of-run
checks had passed.

All 21 records were read from one listing page: Beauty's "New Arrivals", fetch `01M6KB69AJA2N65MDQP4V1QWTE`,
received at 13:15:20Z. That page gave the prices of all 50 of its product placements as flat display strings
(`priceInfo.linePriceDisplay`, `linePrice` and `unitPrice` as strings), with no price line. The collector's page
reader reads that layout. The 1.6.4 source check did not: it read only price lines and nested price objects. It
expected no price on that page, so the records' correct prices looked wrong:

- regular price ×19;
- unit price ×12;
- 1 URL and 1 image, for records it then judged on another page.

The defect was in the checker, not in the data. Release 1.6.5 corrects it (`../../../offline-tests/1.6.5-collector/`).

## The files

| File | What it holds |
|---|---|
| `L10_SOURCE_MISMATCHES_ON_1.6.4.json`, `source_mismatch_164.py` | the 21 records, with the 1.6.4 check's full per-record result. The script uses the inputs `validate-export --run` reads and the collector's own `checks/source_check.check`, run with the 1.6.4 edition |
| `L10_SOURCE_CHECK_RECHECK.csv`, `L10_SOURCE_CHECK_RECHECK.json`, `flat_layout_recheck_164.py` | an independent recheck of the 21. It reads each record's item on every stored L10 page that holds it, with a few lines of its own rather than the collector's reader, in all three layouts. For each of the 21 records, one page shows exactly the record's prices, unit price, URL, image and title, with a Pickup line for store 3891. That page is the flat-layout page each time |
| `UNREPORTED_FIVE_ON_1.6.4.json`, `UNREPORTED_FIVE_ON_1.6.5.json`, `unreported_five_165.py` | why 21, not 26. L10 read 26 records from the flat page (they are the 1.6.5 test capture's `l10_records.json`). The other 5 also appear on other stored pages that give their prices in price lines: four L6 pages (`01M6K2A1Q58NG4DHFP75FFT89E`, `01M6K2BK1JSQJRX5N1361JHYY0`, `01M6K2DH9FZ30V1ZVSNDGRTGV2`, `01M6K2EGNY0FHXP2TX5GC7WAV3`) and one L10 page (`01M6KB90WYBWM9DGXHAA561MTQ`). On those pages 1.6.4 found every field equal, so it did not report them. With 1.6.5, each of the 5 also equals its placement on the flat page |

## The re-validation with release 1.6.5

The 1.6.5 checks were rerun offline on the exports already written (step logs in `../../../live/1.6.x/campaign/logs/`):

| Step | Export | Release that collected it | 1.6.5 `validate-export --run` |
|---|---|---|---|
| 169 (14:21:18Z) | L10, 10,301 records | 1.6.4 | exit 0: contract passed, 10,301 of 10,301 verified against 1,478 stored pages of 13 runs, 0 mismatches, 0 unverified |
| 170 (14:22:47Z) | L8, 2,515 records | 1.6.3 | exit 0: contract passed, 2,515 of 2,515 verified against 951 stored pages of 10 runs, 0 mismatches, 0 unverified |

L10 and L8 stay attributed to the releases that collected them. Only the check is 1.6.5's. Release 1.6.5's live
canary is L11b (`../../../live/1.6.x/runs/L11b_01M6KFRFEX31W014SW9ZTT4Y54/`): it passed on its first recorded page,
35 of 35 records verified.

## What else 1.6.4's check would have done

The regression tests in `../../../offline-tests/1.6.5-collector/` show two more effects on a page in this layout:

- **A correct run stopped.** The automated canary compares a run's first recorded page in the same way. A run whose
  first page came in this layout would have been stopped, although its records were correct.
- **A missing price accepted.** A record whose price and unit price were both empty would have been "verified",
  because the check expected no price there. In SYNTHETIC test copies of an authentic record, 1.6.4 verified that
  copy; 1.6.5 reports it as a mismatch.

No delivered record was affected by the second effect. The only stored pages in this layout are L10's (13:15Z) and
L11's (14:24Z). All 26 records L10 read from its page carry the prices the page displays, and 1.6.5 verifies them.
L11 recorded no product.
