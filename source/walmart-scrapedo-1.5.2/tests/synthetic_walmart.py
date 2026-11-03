"""SYNTHETIC Walmart pages for offline tests: documents shaped like walmart.com's server-rendered pages
(``<script id="__NEXT_DATA__">``: ``searchResult.itemStacks[].items[]`` with ``priceInfo``,
``fulfillmentSummary``, ``sellerName``, ``availabilityStatusV2``; category pages with ``contentLayout``
links; store pages with the store's address). Every value here is invented for the tests; none of it is
live data and none of it may be reported as such."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Item:
    item_id: str
    name: str
    price: str  # displayed current price, e.g. "$3.12"
    was: str = ""  # struck-through price
    unit: str = ""  # displayed price per measure, e.g. "16.0 ¢/oz"
    brand: str = ""
    seller: str = "Walmart.com"
    lines: tuple[tuple[str, str], ...] = (("PICKUP", "{store}"), ("DELIVERY", "{store}"), ("SHIPPING", "0"))
    availability: str = "IN_STOCK"
    sponsored: bool = False
    upc: str = ""
    badges: tuple[tuple[str, str], ...] = ()
    flat_price: bool = False  # the flat display-string layout of priceInfo
    price_range: str = ""
    weight_priced: bool = False
    condition: str = ""  # Walmart's wording next to the price ("each (est.)", "/ 0.14lb")
    extra: dict[str, Any] = field(default_factory=dict)


def item_json(it: Item, store: str) -> dict[str, Any]:
    if it.flat_price:
        price_info: dict[str, Any] = {
            "linePrice": it.price,
            "linePriceDisplay": it.price,
            "wasPrice": it.was,
            "unitPrice": it.unit,
            "priceRangeString": it.price_range,
            "priceDisplayCodes": {
                "finalCostByWeight": it.weight_priced or None,
                "rollback": bool(it.was),
                "priceDisplayCondition": it.condition or None,
            },
        }
    else:
        price_info = {
            "currentPrice": {
                "price": float(it.price.strip("$")) if it.price else None,
                "priceString": it.price,
            },
            "wasPrice": {"priceString": it.was} if it.was else None,
            "unitPrice": {"priceString": it.unit} if it.unit else None,
            "priceDisplayCodes": {
                "finalCostByWeight": it.weight_priced or None,
                "strikethrough": bool(it.was),
                "priceDisplayCondition": it.condition or None,
            },
        }
        if it.price_range:
            price_info["priceRange"] = {"priceString": it.price_range}
    d: dict[str, Any] = {
        "__typename": "Product",
        "id": f"PID{it.item_id}",
        "usItemId": it.item_id,
        "name": it.name,
        "brand": it.brand,
        "canonicalUrl": f"/ip/{it.name.split(',')[0].replace(' ', '-')}/{it.item_id}",
        "imageInfo": {
            "thumbnailUrl": f"https://i5.walmartimages.com/seo/synthetic_{it.item_id}.jpeg?odnHeight=180"
        },
        "priceInfo": price_info,
        "sellerName": it.seller,
        "sellerId": "F55CDC31AB754BB68FE0B39041159D63" if it.seller == "Walmart.com" else "SELLER2",
        "fulfillmentSummary": [
            {"fulfillment": k, "storeId": s.format(store=store), "deliveryDate": None} for k, s in it.lines
        ],
        "availabilityStatusV2": {
            "value": it.availability,
            "display": it.availability.replace("_", " ").title(),
        },
        "isSponsoredFlag": it.sponsored,
        "badges": {"flags": [{"key": k, "text": t} for k, t in it.badges], "tags": [], "groups": []},
        "salesUnitType": "WEIGHT" if it.weight_priced else "EACH",
        **({"upc": it.upc} if it.upc else {}),
        **it.extra,
    }
    return d


def next_data_script(data: dict[str, Any]) -> str:
    text = json.dumps(data).replace("<", "\\u003c")
    return f'<script id="__NEXT_DATA__" type="application/json">{text}</script>'


def listing_page(
    items: list[Item],
    *,
    store: str,
    page: int = 1,
    max_page: int = 1,
    total: int | None = None,
    title: str = "Synthetic listing",
    extra_props: dict[str, Any] | None = None,
    cat: tuple[str, list[str]] | None = None,
    departments: list[tuple[str, str, str]] | None = None,
    grid_filter: str | None = None,
) -> str:
    """``cat``: the listing's own name and its breadcrumb's category ids (``catInfo``, ``breadCrumb``).
    ``departments``: (id, name, /browse/ path) values of the listing's own "Departments" facet.
    ``grid_filter``: the fulfillment the result grid is filtered for (its ``meta.fulfillmentIntent``:
    "Pickup" in Walmart's Pickup grid, null in the store's unfiltered grid)."""
    crumbs: list[dict[str, Any]] = [{"name": "Synthetic"}, {"name": title}]
    if cat is not None:
        crumbs = [{"id": c, "name": f"Synthetic {c}"} for c in cat[1]]
    data = {
        "props": {
            "pageProps": {
                "initialData": {
                    "searchResult": {
                        "title": title,
                        "aggregatedCount": total if total is not None else len(items),
                        "itemStacks": [
                            {
                                "count": total,
                                "items": [item_json(i, store) for i in items],
                                "meta": {"fulfillmentIntent": grid_filter},
                            }
                        ],
                        "paginationV2": {"maxPage": max_page, "pageProperties": {"page": page}},
                        "breadCrumb": crumbs,
                        **({"catInfo": {"catId": cat[1][-1], "name": cat[0]}} if cat else {}),
                    },
                    **(
                        {
                            "contentLayout": {
                                "modules": [
                                    {
                                        "configs": {
                                            "allSortAndFilterFacets": [
                                                {
                                                    "name": "Departments",
                                                    "type": "cat_id",
                                                    "values": [
                                                        {
                                                            "id": i,
                                                            "name": n,
                                                            "baseSeoURL": path,
                                                            "url": f"cat_id={i}&stores={store}",
                                                            "itemCount": None,
                                                        }
                                                        for i, n, path in departments
                                                    ],
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                        if departments
                        else {}
                    ),
                },
                **(extra_props or {}),
            }
        },
        "page": "/browse/[...slug]",
        "query": {"page": str(page)},
    }
    return (
        "<!doctype html><html><head><title>SYNTHETIC listing</title>"
        '<script src="/static/app.js"></script><link rel="stylesheet" href="/static/app.css"></head>'
        f'<body><div id="__next"><h1>{title}</h1></div>{next_data_script(data)}'
        '<script>window.__SYNTHETIC_INLINE_TOKEN__ = "inline-token-123";</script></body></html>'
    )


def category_page(links: list[tuple[str, str]], *, title: str = "Synthetic category") -> str:
    data = {
        "props": {
            "pageProps": {
                "initialData": {
                    "contentLayout": {
                        "modules": [
                            {
                                "type": "PillsModule",
                                "configs": {
                                    "pillsV2": [
                                        {"title": name, "url": url, "image": {"alt": name}}
                                        for name, url in links
                                    ]
                                },
                            }
                        ]
                    }
                }
            }
        }
    }
    return (
        f"<!doctype html><html><head><title>SYNTHETIC {title}</title></head><body>"
        f"<h1>{title}</h1>{next_data_script(data)}</body></html>"
    )


def store_page(
    store_id: str,
    *,
    name: str,
    address: str,
    city: str,
    state: str,
    postal: str,
    button: bool = True,
    confirm_dialog: bool = False,
    session_token: str = "sess-secret-abc",
    sensor_cookie: bool = False,
) -> str:
    data = {
        "props": {
            "pageProps": {
                "initialData": {
                    "initialDataStoreDetails": {
                        "id": store_id,
                        "displayName": name,
                        "address": {
                            "addressLineOne": address,
                            "city": city,
                            "state": state,
                            "postalCode": postal,
                        },
                    }
                },
                "bootstrapData": {
                    "sessionId": session_token,
                    "clientIp": "203.0.113.7",
                    "csrfToken": "csrf-xyz",
                },
            }
        }
    }
    click = "openDialog()" if confirm_dialog else "makeMyStore()"
    control = (
        f'<button id="mms" type="button" onclick="{click}">Make this my store</button>' if button else ""
    )
    dialog = (
        '<div id="dlg" role="dialog" aria-label="Change store" hidden>'
        "<p>Make Chicago Supercenter your store?</p>"
        '<button type="button" onclick="closeDialog()">Cancel</button>'
        '<button type="button" onclick="makeMyStore()">Confirm</button></div>'
        if confirm_dialog
        else ""
    )
    # Stands in for the bot manager's sensor setting its token cookie a moment after the page loaded.
    sensor = (
        "setTimeout(function(){document.cookie='_px3=synthetic-token; path=/';},400);"
        if sensor_cookie
        else ""
    )
    script = (
        f"<script>{sensor}function openDialog(){{document.getElementById('dlg').hidden=false;}}"
        "function closeDialog(){document.getElementById('dlg').hidden=true;}"
        "async function makeMyStore(){"
        f"await fetch('/orchestra/home/graphql/setPickupStore?storeId={store_id}',{{method:'POST'}});"
        "const b=document.getElementById('mms'); b.remove();"
        "const d=document.getElementById('dlg'); if(d){d.remove();}"
        "document.getElementById('status').innerText='This is your store';}</script>"
    )
    return (
        f"<!doctype html><html><head><title>SYNTHETIC store {store_id}</title></head><body>"
        f'<h1>{name}</h1><p>{address}, {city}, {state} {postal}</p><p id="status"></p>{control}{dialog}'
        f"{next_data_script(data)}{script}</body></html>"
    )


# The shape of PerimeterX's answer to a blocked data request and of its dialog (SYNTHETIC values; the
# live answer of 2026-10-20 had these keys).
PX_BLOCK_RESPONSE = (
    '{"redirectUrl":"/blocked?url=L3N0b3Jl&uuid=00000000-0000-0000-0000-000000000000&vid=synthetic&g=b",'
    '"appId":"PXsynthetic","jsClientSrc":"/px/PXsynthetic/init.js","firstPartyEnabled":true,'
    '"blockScript":"/px/PXsynthetic/captcha/captcha.js?a=c&m=0"}'
)
CHALLENGE_DIALOG = (
    '<div role="dialog"><h2>Robot or human?</h2>'
    "<p>Activate and hold the button to confirm that you are human.</p>"
    '<div id="px-captcha"></div></div>'
)

CHALLENGE_PAGE = (
    "<!doctype html><html><head><title>Robot or human?</title></head><body>"
    "<h1>Robot or human?</h1><p>Activate and hold the button to confirm that you're human.</p>"
    '<div id="px-captcha"></div></body></html>'
)
