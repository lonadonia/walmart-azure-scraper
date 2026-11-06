"""An in-memory mock of Scrape.do's API (``httpx.MockTransport``) as its documentation describes it, serving
SYNTHETIC Walmart pages: the Walmart store endpoint (10 credits), the general API (1 credit), the free
``/info`` account endpoint, the cost and remaining-credit headers, and the failures the collector must tell
apart. Nothing here reaches Scrape.do or Walmart; the tokens are invented."""

from __future__ import annotations

import json
from collections.abc import Callable
from urllib.parse import parse_qs, urlsplit

import httpx

from tests import synthetic_walmart as syn

PRIMARY = "0" * 40 + "aaa"  # SYNTHETIC tokens
SECONDARY = "1" * 40 + "bbb"
MILK = "https://www.walmart.com/browse/food/milk/976759_9176907"
SNACKS = "https://www.walmart.com/browse/food/snacks/976759_976787"
DIAPERING = "https://www.walmart.com/browse/diapering/5427_486190"


def listing(
    items: list[syn.Item],
    *,
    page: int,
    max_page: int,
    total: int,
    store: str = "3891",
    intent: str = "PICKUP",
    cat: tuple[str, list[str]] | None = None,
    departments: list[tuple[str, str, str]] | None = None,
    grid_filter: str | None = None,
) -> str:
    html = syn.listing_page(
        items,
        store=store,
        page=page,
        max_page=max_page,
        total=total,
        cat=cat,
        departments=departments,
        grid_filter=grid_filter,
    )
    loc = json.dumps({"location": {"storeId": store, "postalCode": "60085", "intent": intent}})
    return html.replace('"searchResult":', f'"pageMetadata": {loc}, "searchResult":', 1)


def category_page() -> str:
    data = {
        "props": {
            "pageProps": {
                "initialData": {},
                "initialTempoData": {
                    "contentLayout": {
                        "modules": [
                            {
                                "configs": {
                                    "categoriesData": [
                                        {
                                            "name": "Recipes",
                                            "subcategories": [
                                                {
                                                    "subCategoryLink": {
                                                        "title": "Shop All",
                                                        "clickThrough": {"value": "/i/recipes"},
                                                    }
                                                }
                                            ],
                                        },
                                        {
                                            "name": "Dairy & Eggs",
                                            "subcategories": [
                                                {
                                                    "subCategoryLink": {
                                                        "title": "Shop All",
                                                        "clickThrough": {"value": "/cp/dairy-eggs/9176907"},
                                                    }
                                                },
                                                {
                                                    "subCategoryLink": {
                                                        "title": "Milk",
                                                        "clickThrough": {"value": MILK},
                                                    }
                                                },
                                            ],
                                        },
                                        {
                                            "name": "Snacks",
                                            "subcategories": [
                                                {
                                                    "subCategoryLink": {
                                                        "title": "Shop all",
                                                        "clickThrough": {"value": SNACKS},
                                                    }
                                                }
                                            ],
                                        },
                                    ]
                                }
                            }
                        ]
                    }
                },
            }
        }
    }
    return f"<!doctype html><html><body>{syn.next_data_script(data)}</body></html>"


STORE_PAGE = syn.store_page(
    "3891",
    name="Waukegan Supercenter",
    address="3900 Fountain Square Pl",
    city="Waukegan",
    state="IL",
    postal="60085",
)
PAGES: dict[str, list[list[syn.Item]]] = {
    MILK: [[syn.Item("7101", "Milk, Gallon, 128 fl oz", "$3.12", unit="2.4 ¢/fl oz")]],
    SNACKS: [
        [
            syn.Item("7201", "Chips, 8 oz", "$2.12", unit="26.5 ¢/oz"),
            syn.Item(
                "7202", "Market Snack, 1 ct", "$9.99", seller="Other Seller LLC", lines=(("SHIPPING", "0"),)
            ),
        ],
        # Out of stock with the store's Pickup line: the store's product and price (unavailable now).
        [syn.Item("7203", "Pretzels, 16 oz", "$2.50", availability="OUT_OF_STOCK")],
    ],
    DIAPERING: [[syn.Item("7301", "Diapers, Size 1, 84 Count", "$9.97", unit="11.9 ¢/ea")]],
}
# Each listing page's own name and breadcrumb category ids, as Walmart states them (catInfo, breadCrumb).
LISTING_CATS: dict[str, tuple[str, list[str]]] = {
    MILK: ("Milk", ["976759", "976759_9176907"]),
    SNACKS: ("Snacks", ["976759", "976759_976787"]),
    DIAPERING: ("Diapering", ["5427", "5427_486190"]),
}
# The UPC each SYNTHETIC product page states (leading zeros kept as written); an item missing here has a
# product page that states no UPC.
PRODUCT_UPCS = {"7101": "078742371245", "7201": "028400090896", "7203": "001234567890"}


def nav_page(groups: list[tuple[str, list[tuple[str, str]]]]) -> str:
    """A SYNTHETIC category page whose own navigation (``configs.categoriesData``, where live category pages
    keep it) has these groups of (link title, link), in order."""
    data = {
        "props": {
            "pageProps": {
                "initialData": {},
                "initialTempoData": {
                    "contentLayout": {
                        "modules": [
                            {
                                "configs": {
                                    "categoriesData": [
                                        {
                                            "name": name,
                                            "subcategories": [
                                                {
                                                    "subCategoryLink": {
                                                        "title": t,
                                                        "clickThrough": {"value": v},
                                                    }
                                                }
                                                for t, v in links
                                            ],
                                        }
                                        for name, links in groups
                                    ]
                                }
                            }
                        ]
                    }
                },
            }
        }
    }
    return f"<!doctype html><html><body>{syn.next_data_script(data)}</body></html>"


# Release 1.6.8: the category pages of their own the Food page's navigation links, by path, served through
# the general API like every category page and read for the listings they name. The "Shop All" page of
# Dairy & Eggs names Milk, which the Food page names too (read once). A test adds its own pages here.
CATEGORY_PAGES: dict[str, str] = {
    "/cp/dairy-eggs/9176907": nav_page([("Milk", [("Milk", MILK)])]),
}


def product_page(item_id: str, upc: str | None = None) -> str:
    """A SYNTHETIC Walmart product page: its page data names the item, with its UPC when it has one."""
    product: dict[str, str] = {"usItemId": item_id, "name": f"Synthetic item {item_id}"}
    value = PRODUCT_UPCS.get(item_id) if upc is None else upc
    if value:
        product["upc"] = value
    data = {"props": {"pageProps": {"initialData": {"data": {"product": product}}}}}
    return f"<!doctype html><html><body>{syn.next_data_script(data)}</body></html>"


CP_PLUGIN_FAILURE = (
    '{"error":"Walmart-store plugin failure.","message":"Please ensure all provided parameters are correct '
    'and try again. If the problem persists, please contact support."}'
)


class MockScrapeDo:
    """Scrape.do's API as the documentation describes it (SYNTHETIC answers)."""

    def __init__(self, *, primary_credits: int = 1000, secondary_credits: int = 1000):
        self.remaining = {PRIMARY: primary_credits, SECONDARY: secondary_credits}
        self.calls: list[tuple[str, str, str]] = []  # (token role, endpoint, target url)
        self.page_override: Callable[[str], httpx.Response | None] | None = None
        self.intent = "PICKUP"
        # The store the provider says a store-endpoint answer reflects (Scrape.do-Walmart-Store-Id).
        self.store_header: str | None = "3891"

    def role(self, token: str) -> str:
        return "primary" if token == PRIMARY else "secondary" if token == SECONDARY else "?"

    def handler(self, request: httpx.Request) -> httpx.Response:
        token = request.url.params.get("token", "")
        path = request.url.path
        url = request.url.params.get("url", "")
        if path == "/info":
            return httpx.Response(
                200,
                json={
                    "IsActive": True,
                    "ConcurrentRequest": 5,
                    "MaxMonthlyRequest": 1000,
                    "RemainingConcurrentRequest": 5,
                    "RemainingMonthlyRequest": self.remaining.get(token, 0),
                },
            )
        self.calls.append((self.role(token), path, url))
        if token not in self.remaining:
            return httpx.Response(401, json={"Message": "invalid token"})
        cost = 10 if path == "/plugin/walmart/store" else 1
        if self.remaining[token] < cost:
            return httpx.Response(
                401, json={"Message": "You have no credits or your subscription has been suspended"}
            )
        if self.page_override is not None:
            r = self.page_override(url)
            if r is not None:
                return r
        body, status = self.page(path, request)
        if status < 300 or status in (400, 404):
            self.remaining[token] -= cost
            headers = {
                "Scrape.do-Request-Cost": str(cost),
                "Scrape.do-Remaining-Credits": str(self.remaining[token]),
            }
        else:
            headers = {"Scrape.do-Request-Cost": "0"}
        headers["Scrape.do-Request-Id"] = f"req-{len(self.calls)}"
        if path == "/plugin/walmart/store" and status < 300 and self.store_header:
            headers["Scrape.do-Walmart-Store-Id"] = self.store_header
        return httpx.Response(status, text=body, headers={**headers, "Content-Type": "text/html"})

    def page(self, path: str, request: httpx.Request) -> tuple[str, int]:
        url = request.url.params.get("url", "")
        u = urlsplit(url)
        if path == "/":
            if u.path == "/robots.txt":
                return "User-agent: *\nDisallow: /search\n", 200
            if u.path.startswith("/store/"):
                return STORE_PAGE, 200
            if u.path.startswith("/ip/"):
                return product_page(u.path.rstrip("/").rsplit("/", 1)[-1]), 200
            if u.path == "/cp/food/976759":
                return category_page(), 200
            if u.path in CATEGORY_PAGES:
                return CATEGORY_PAGES[u.path], 200
            return "not found", 404
        if path != "/plugin/walmart/store":
            return "", 404
        params = request.url.params
        if (params.get("storeid"), params.get("zipcode")) != ("3891", "60085"):
            return json.dumps({"error": "invalid combination of zipcode and storeid"}), 502
        base = f"{u.scheme}://{u.netloc}{u.path}"
        if u.path.startswith("/cp/"):
            # What the store plugin answered for every category page on 2026-10-23 (a provider error).
            return CP_PLUGIN_FAILURE, 502
        if base in PAGES:
            pages = PAGES[base]
            query = parse_qs(u.query)
            n = int(query.get("page", ["1"])[0])
            items = pages[n - 1] if n <= len(pages) else []
            total = sum(len(p) for p in pages)
            cat = LISTING_CATS.get(base)
            # Walmart filters the grid for Pickup when the URL carries its facet (values joined by "||");
            # without it the store endpoint's answer is the store's unfiltered grid (live 2026-10-28).
            facets = {f for v in query.get("facet", []) for f in v.split("||")}
            grid = "Pickup" if "fulfillment_method:Pickup" in facets else None
            html = listing(
                items, page=n, max_page=len(pages), total=total, intent=self.intent, cat=cat, grid_filter=grid
            )
            return html, 200
        return "not found", 404
