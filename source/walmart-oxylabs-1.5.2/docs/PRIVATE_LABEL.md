# Private-label brands: how `store_brand` is decided

`store_brand` is `yes` when a product's brand, or the brand its title opens with, is in
`config/walmart_private_label_brands.yaml`, and `no` otherwise. Where ownership or the client's policy is
uncertain, the value stays `no` and the uncertainty is written here.

## What counts as evidence

The record of the mark at the United States Patent and Trademark Office (USPTO): its current owner, status and goods.
Walmart holds its marks through Walmart Apollo, LLC. A trademark record shows who owns a name, so it is read together
with what the name is sold as on Walmart's own pages. Third-party lists and search summaries are not evidence: one
search summary gave a serial number for PURE BALANCE that the USPTO's record shows is another mark (MAS CLUB).

## Brands added in release 1.5.2

Read on 2026-11-01 from `https://tsdr.uspto.gov/statusview/sn<serial>`.

| Brand | Mark | Serial | Registration | Current owner | Status at the USPTO | Goods on the record |
|---|---|---|---|---|---|---|
| Prima Della | PRIMA DELLA | 76458530 | 2862043 | Walmart Apollo, LLC | Live, renewed (2024-07-02) | Beef; cheese; chicken; ham; luncheon meats; salami; turkey |
| Clear American | CLEAR AMERICAN ESSENTIALS | 87727865 | 5801294 | Walmart Apollo, LLC | Live (2024-12-19) | Soft drinks, fruit flavored drinks, sparkling waters |
| ReliOn | RELION | 75980144 | 2454191 | Walmart Apollo, LLC | Renewed (2021-06-22) | Blood pressure measuring apparatus and medical thermometers |
| Special Kitty | SPECIAL KITTY | 74539951 | 1910334 | Walmart Apollo, LLC | Live, renewed (2024-11-28) | Cat food |
| Vibrant Life | VIBRANT LIFE | 87892205 | 5617359 | Walmart Apollo, LLC | Live (2024-06-11) | Dog food, cat food, pet treats and other pet foods |
| Pure Balance | PURE BALANCE | 97302333 | 7109375 | Walmart Apollo, LLC | Live (2023-07-11) | Dietary supplements for pets; protein supplements for animals; animal feed supplements |

Limits of this evidence:

- **Pure Balance.** The live mark read covers pet supplements. The record for pet food that was read, PB PURE BALANCE
  (serial 85055908, registration 4448075), has the same owner but was cancelled on 2024-06-21 because no Section 8
  declaration was filed. Trade press calls Pure Balance Walmart's private-label pet food; no live pet-food registration
  was read.
- **Clear American.** The record read is CLEAR AMERICAN ESSENTIALS. It claims acquired distinctiveness in part, "as to
  'CLEAR AMERICAN'". No live record for CLEAR AMERICAN alone was read. The USPTO record of serial 75251533 could not be
  read in this check.
- **ReliOn.** The record read does not name diabetes supplies. Trade press reports Walmart's ReliOn line as private label,
  including the insulin of 2021.
- Walmart's own category page for Prima Della could not be read: it answered with a challenge page, and no attempt was
  made to pass it. A search listing titles that page "Prima Della in Deli Private Brands".

## Walmart's own product pages

A check of the 1,080 saved product pages (`private_label/brands_on_saved_pages.json` in the evidence) found no field that
marks a private brand: the only matching text is `privateLabel`, a payment-card type. A "Manufacturer" specification
naming Walmart appears only for Equate, Parent's Choice, Marketside and Freshness Guaranteed, all listed, and for the
non-brands below. None of the six added brands had a saved page naming Walmart as the manufacturer; Pure Balance has one
page naming Diamond Pet, its maker, which does not change who owns the brand.

## Left at `no`

| Name | Why |
|---|---|
| Scent Theory | Trademark listings name Scent Theory Products, LLC as owner. Sold at Walmart, not owned by it on that evidence. |
| Millie Moon | Walmart's page names ZURU as manufacturer. |
| Fresh Produce, Unbranded, Generic | Walmart's labels for unbranded goods, not brands. A few pages name Walmart as manufacturer. No brand name to classify. |
| Better Homes & Gardens and other licensed names | Not in the configured categories' evidence, and a licence is not ownership. |
| Member's Mark | Sam's Club's label. Not seen on a Walmart Pickup page in the evidence. |

"Walmart Exclusive" on a page means sold only at Walmart. It does not mean private label, and it sets no value.

## What the client decides

The list follows ownership. If the client's own definition of private label differs (for example, counting exclusive or
licensed brands), the list is one configuration file. No code changes.
