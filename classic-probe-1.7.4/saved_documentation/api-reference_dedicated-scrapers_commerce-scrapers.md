> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/api-reference/dedicated-scrapers/commerce-scrapers.md).

# Commerce Scrapers

Reference for Web API commerce scraper endpoints: Amazon, Walmart, Target, the Kroger banners, and more. Parameters and delivery modes for every endpoint.

Use the table search bar to fin a dedicated commerce scraper and click a target to jump to its endpoints.

<table><thead><tr><th width="170.5">Scraper</th><th>Endpoints</th></tr></thead><tbody><tr><td><a href="#alibaba">Alibaba</a></td><td><code>/alibaba</code>, <code>/alibaba/product</code>, <code>/alibaba/search</code></td></tr><tr><td><a href="#aliexpress">AliExpress</a></td><td><code>/aliexpress</code>, <code>/aliexpress/product</code>, <code>/aliexpress/search</code></td></tr><tr><td><a href="#allegro">Allegro</a></td><td><code>/allegro/product</code>, <code>/allegro/search</code></td></tr><tr><td><a href="#amazon">Amazon</a></td><td><code>/amazon</code>, <code>/amazon/bestsellers</code>, <code>/amazon/pricing</code>, <code>/amazon/product</code>, <code>/amazon/search</code>, <code>/amazon/sellers</code></td></tr><tr><td><a href="#bakers-plus">Baker's Plus</a></td><td><code>/bakersplus</code>, <code>/bakersplus/product</code>, <code>/bakersplus/search</code></td></tr><tr><td><a href="#bed-bath-and-beyond">Bed Bath &#x26; Beyond</a></td><td><code>/bedbathandbeyond</code>, <code>/bedbathandbeyond/product</code>, <code>/bedbathandbeyond/search</code></td></tr><tr><td><a href="#best-buy">Best Buy</a></td><td><code>/bestbuy</code>, <code>/bestbuy/product</code>, <code>/bestbuy/search</code></td></tr><tr><td><a href="#bodega-aurrera">Bodega Aurrera</a></td><td><code>/bodegaaurrera</code>, <code>/bodegaaurrera/product</code>, <code>/bodegaaurrera/search</code></td></tr><tr><td><a href="#cdiscount">Cdiscount</a></td><td><code>/cdiscount</code>, <code>/cdiscount/product</code>, <code>/cdiscount/search</code></td></tr><tr><td><a href="#city-market">City Market</a></td><td><code>/citymarket</code>, <code>/citymarket/product</code>, <code>/citymarket/search</code></td></tr><tr><td><a href="#costco">Costco</a></td><td><code>/costco</code>, <code>/costco/product</code>, <code>/costco/search</code></td></tr><tr><td><a href="#dcard">Dcard</a></td><td><code>/dcard/search</code></td></tr><tr><td><a href="#dillons">Dillons</a></td><td><code>/dillons</code>, <code>/dillons/product</code>, <code>/dillons/search</code></td></tr><tr><td><a href="#ebay">eBay</a></td><td><code>/ebay</code>, <code>/ebay/product</code>, <code>/ebay/search</code></td></tr><tr><td><a href="#etsy">Etsy</a></td><td><code>/etsy</code>, <code>/etsy/product</code>, <code>/etsy/search</code></td></tr><tr><td><a href="#falabella">Falabella</a></td><td><code>/falabella</code>, <code>/falabella/product</code>, <code>/falabella/search</code></td></tr><tr><td><a href="#flipkart">Flipkart</a></td><td><code>/flipkart</code>, <code>/flipkart/product</code>, <code>/flipkart/search</code></td></tr><tr><td><a href="#food-4-less">Food 4 Less</a></td><td><code>/foodfourless</code>, <code>/foodfourless/product</code>, <code>/foodfourless/search</code></td></tr><tr><td><a href="#fred-meyer">Fred Meyer</a></td><td><code>/fredmeyer</code>, <code>/fredmeyer/product</code>, <code>/fredmeyer/search</code></td></tr><tr><td><a href="#frys-food">Fry's Food</a></td><td><code>/frysfood</code>, <code>/frysfood/product</code>, <code>/frysfood/search</code></td></tr><tr><td><a href="#gerbes">Gerbes</a></td><td><code>/gerbes</code>, <code>/gerbes/product</code>, <code>/gerbes/search</code></td></tr><tr><td><a href="#grainger">Grainger</a></td><td><code>/grainger</code>, <code>/grainger/product</code>, <code>/grainger/search</code></td></tr><tr><td><a href="#harris-teeter">Harris Teeter</a></td><td><code>/harristeeter</code>, <code>/harristeeter/product</code>, <code>/harristeeter/search</code></td></tr><tr><td><a href="#idealo">Idealo</a></td><td><code>/idealo/search</code></td></tr><tr><td><a href="#indiamart">Indiamart</a></td><td><code>/indiamart</code>, <code>/indiamart/product</code>, <code>/indiamart/search</code></td></tr><tr><td><a href="#instacart">Instacart</a></td><td><code>/instacart</code>, <code>/instacart/product</code>, <code>/instacart/search</code></td></tr><tr><td><a href="#king-soopers">King Soopers</a></td><td><code>/kingsoopers</code>, <code>/kingsoopers/product</code>, <code>/kingsoopers/search</code></td></tr><tr><td><a href="#kroger">Kroger</a></td><td><code>/kroger</code>, <code>/kroger/product</code>, <code>/kroger/search</code></td></tr><tr><td><a href="#lazada">Lazada</a></td><td><code>/lazada</code>, <code>/lazada/product</code>, <code>/lazada/search</code></td></tr><tr><td><a href="#lowes">Lowe's</a></td><td><code>/lowes</code>, <code>/lowes/product</code>, <code>/lowes/search</code></td></tr><tr><td><a href="#magazine-luiza">Magazine Luiza</a></td><td><code>/magazineluiza</code>, <code>/magazineluiza/product</code>, <code>/magazineluiza/search</code></td></tr><tr><td><a href="#marianos">Mariano's</a></td><td><code>/marianos</code>, <code>/marianos/product</code>, <code>/marianos/search</code></td></tr><tr><td><a href="#mediamarkt">MediaMarkt</a></td><td><code>/mediamarkt</code>, <code>/mediamarkt/product</code>, <code>/mediamarkt/search</code></td></tr><tr><td><a href="#menards">Menards</a></td><td><code>/menards</code>, <code>/menards/product</code>, <code>/menards/search</code></td></tr><tr><td><a href="#mercado-libre">Mercado Libre</a></td><td><code>/mercadolibre</code>, <code>/mercadolibre/product</code>, <code>/mercadolibre/search</code></td></tr><tr><td><a href="#mercado-livre">Mercado Livre</a></td><td><code>/mercadolivre/product</code>, <code>/mercadolivre/search</code></td></tr><tr><td><a href="#metro-market">Metro Market</a></td><td><code>/metromarket</code>, <code>/metromarket/product</code>, <code>/metromarket/search</code></td></tr><tr><td><a href="#neobits">Neobits</a></td><td><code>/neobits/search</code></td></tr><tr><td><a href="#petco">Petco</a></td><td><code>/petco</code>, <code>/petco/search</code></td></tr><tr><td><a href="#pick-n-save">Pick 'n Save</a></td><td><code>/picknsave</code>, <code>/picknsave/product</code>, <code>/picknsave/search</code></td></tr><tr><td><a href="#publix">Publix</a></td><td><code>/publix</code>, <code>/publix/product</code>, <code>/publix/search</code></td></tr><tr><td><a href="#qfc">QFC</a></td><td><code>/qfc</code>, <code>/qfc/product</code>, <code>/qfc/search</code></td></tr><tr><td><a href="#rakuten">Rakuten</a></td><td><code>/rakuten</code>, <code>/rakuten/search</code></td></tr><tr><td><a href="#ralphs">Ralphs</a></td><td><code>/ralphs</code>, <code>/ralphs/product</code>, <code>/ralphs/search</code></td></tr><tr><td><a href="#safeway">Safeway</a></td><td><code>/safeway/product</code>, <code>/safeway/search</code>, <code>/safeway/category</code></td></tr><tr><td><a href="#shein">Shein</a></td><td><code>/shein/search</code></td></tr><tr><td><a href="#smiths">Smith's</a></td><td><code>/smithsfoodanddrug</code>, <code>/smithsfoodanddrug/product</code>, <code>/smithsfoodanddrug/search</code></td></tr><tr><td><a href="#target">Target</a></td><td><code>/target</code>, <code>/target/category</code>, <code>/target/product</code>, <code>/target/search</code></td></tr><tr><td><a href="#tiktok-shop">TikTok Shop</a></td><td><code>/tiktok</code>, <code>/tiktok/shop/product</code>, <code>/tiktok/shop/search</code></td></tr><tr><td><a href="#walmart">Walmart</a></td><td><code>/walmart</code>, <code>/walmart/product</code>, <code>/walmart/search</code></td></tr></tbody></table>

### Alibaba

#### `POST /v1/scrape/alibaba`

Returns parsed fields for a Alibaba page from a URL you provide.

**Modes:** `sync`, `async`

<table><thead><tr><th width="144.5">Name</th><th width="92.5">Type</th><th width="88">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>url</code></td><td>string</td><td>yes</td><td>A Alibaba product or search URL</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower. Use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/alibaba/product`

Returns one Alibaba product's price, stock, and details.

**Modes:** `sync`, `async`

<table><thead><tr><th width="143">Name</th><th width="89">Type</th><th width="84">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Product ID</td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Storefront TLD</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/alibaba/search`

Returns Alibaba search results for a keyword.

**Modes:** `sync`, `async`

<table><thead><tr><th width="132">Name</th><th width="95">Type</th><th width="93">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Search keyword</td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Storefront TLD</td></tr><tr><td><code>start_page</code></td><td>integer</td><td>no</td><td>First results page</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

### AliExpress

#### `POST /v1/scrape/aliexpress`

Returns parsed fields for a AliExpress page from a URL you provide.

**Modes:** sync · async

<table><thead><tr><th width="138">Name</th><th width="95">Type</th><th width="89">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>url</code></td><td>string</td><td>yes</td><td>A AliExpress product or search URL</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/aliexpress/product`

Returns one AliExpress product's price, stock, and details.

**Modes:** sync · async

<table><thead><tr><th width="134">Name</th><th width="90">Type</th><th width="85">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Product ID</td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Storefront TLD</td></tr><tr><td><code>subdomain</code></td><td>string</td><td>no</td><td>Regional storefront subdomain</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/aliexpress/search`

Returns AliExpress search results for a keyword.

**Modes:** sync · async

<table><thead><tr><th width="136">Name</th><th width="95">Type</th><th width="86">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Search keyword</td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Storefront TLD</td></tr><tr><td><code>start_page</code></td><td>integer</td><td>no</td><td>First results page</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

### Allegro

#### `POST /v1/scrape/allegro/product`

Returns one Allegro product's price, stock, and details.

**Modes:** sync · async

<table><thead><tr><th width="139">Name</th><th width="92">Type</th><th width="83">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Product ID</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/allegro/search`

Returns Allegro search results for a keyword.

**Modes:** sync · async

<table><thead><tr><th width="139">Name</th><th width="87">Type</th><th width="82">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Search keyword</td></tr><tr><td><code>delivery_time</code></td><td>string</td><td>no</td><td>Delivery-speed window filter</td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Storefront TLD</td></tr><tr><td><code>shipping_from</code></td><td>string</td><td>no</td><td>Country or region the item ships from</td></tr><tr><td><code>start_page</code></td><td>integer</td><td>no</td><td>First results page</td></tr><tr><td><code>store_city</code></td><td>string</td><td>no</td><td>Seller's city</td></tr><tr><td><code>store_region</code></td><td>string</td><td>no</td><td>Seller's region</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

### Amazon

#### `POST /v1/scrape/amazon`

Returns parsed fields for an Amazon page from a URL you provide.

**Modes:** sync · async · batch

<table><thead><tr><th width="177">Name</th><th width="98">Type</th><th width="82">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>url</code></td><td>string</td><td>yes</td><td>A URL on any Amazon marketplace. Send it unchanged — query string parameters select the variant and price</td></tr><tr><td><code>autoselect_variant</code></td><td>boolean</td><td>no</td><td>Follows the listing's default variant instead of returning the bare parent listing. Set when a parent ASIN returns no price</td></tr><tr><td><code>category_id</code></td><td>string</td><td>no</td><td>Restricts to an Amazon browse node</td></tr><tr><td><code>check_empty_geo</code></td><td>boolean</td><td>no</td><td>Fails the request instead of returning content that ignored <code>location</code></td></tr><tr><td><code>condition</code></td><td>string</td><td>no</td><td>Offer condition to return, e.g. <code>used</code></td></tr><tr><td><code>currency</code></td><td>string</td><td>no</td><td>Currency to report prices in, e.g. <code>EUR</code></td></tr><tr><td><code>locale</code></td><td>string</td><td>no</td><td>Interface language, e.g. <code>en_US</code></td></tr><tr><td><code>max_price</code></td><td>integer</td><td>no</td><td>Highest price to include, in the marketplace's currency</td></tr><tr><td><code>merchant_id</code></td><td>string</td><td>no</td><td>Restricts to one seller's items</td></tr><tr><td><code>min_price</code></td><td>integer</td><td>no</td><td>Lowest price to include, in the marketplace's currency</td></tr><tr><td><code>pages</code></td><td>integer</td><td>no</td><td>Consecutive pages to fetch from <code>start_page</code>. Each page is a separate fetch and charge</td></tr><tr><td><code>refinements</code></td><td>array of strings</td><td>no</td><td>Amazon's filter facets: brand, rating, Prime eligibility. Forwarded verbatim; values differ per marketplace</td></tr><tr><td><code>safe_search</code></td><td>boolean</td><td>no</td><td>Amazon's content filter</td></tr><tr><td><code>sort_by</code></td><td>string</td><td>no</td><td>Amazon's own sort key, e.g. <code>price-asc-rank</code>, <code>review-rank</code>. Forwarded verbatim; values differ per marketplace</td></tr><tr><td><code>start_page</code></td><td>integer</td><td>no</td><td>First results page. Default <code>1</code></td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Delivery postal code, e.g. <code>10115</code>. Must belong to the marketplace set by <code>domain</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/amazon/bestsellers`

Returns the bestseller ranking for a category.

**Modes:** sync · async · batch

<table><thead><tr><th width="156">Name</th><th width="89">Type</th><th width="82">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Category</td></tr><tr><td><code>category_id</code></td><td>string</td><td>no</td><td>Restricts to an Amazon browse node</td></tr><tr><td><code>check_empty_geo</code></td><td>boolean</td><td>no</td><td>Fails the request instead of returning content that ignored <code>location</code></td></tr><tr><td><code>currency</code></td><td>string</td><td>no</td><td>Currency to report prices in, e.g. <code>EUR</code></td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Marketplace TLD: <code>com</code>, <code>de</code>, <code>co.uk</code>, <code>co.jp</code></td></tr><tr><td><code>locale</code></td><td>string</td><td>no</td><td>Interface language, e.g. <code>en_US</code></td></tr><tr><td><code>pages</code></td><td>integer</td><td>no</td><td>Consecutive pages to fetch from <code>start_page</code>. Each page is a separate fetch and charge</td></tr><tr><td><code>safe_search</code></td><td>boolean</td><td>no</td><td>Amazon's content filter</td></tr><tr><td><code>start_page</code></td><td>integer</td><td>no</td><td>First results page. Default <code>1</code></td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Delivery postal code, e.g. <code>10115</code>. Must belong to the marketplace set by <code>domain</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/amazon/pricing`

Returns every offer on a listing: all sellers and conditions.

**Modes:** sync · async · batch

<table><thead><tr><th width="155">Name</th><th width="94">Type</th><th width="83">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>ASIN whose offers to return</td></tr><tr><td><code>check_empty_geo</code></td><td>boolean</td><td>no</td><td>Fails the request instead of returning content that ignored <code>location</code></td></tr><tr><td><code>condition</code></td><td>string</td><td>no</td><td>Offer condition to return, e.g. <code>used</code></td></tr><tr><td><code>currency</code></td><td>string</td><td>no</td><td>Currency to report prices in, e.g. <code>EUR</code></td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Marketplace TLD: <code>com</code>, <code>de</code>, <code>co.uk</code>, <code>co.jp</code></td></tr><tr><td><code>locale</code></td><td>string</td><td>no</td><td>Interface language, e.g. <code>en_US</code></td></tr><tr><td><code>pages</code></td><td>integer</td><td>no</td><td>Consecutive pages to fetch from <code>start_page</code>. Each page is a separate fetch and charge</td></tr><tr><td><code>safe_search</code></td><td>boolean</td><td>no</td><td>Amazon's content filter</td></tr><tr><td><code>start_page</code></td><td>integer</td><td>no</td><td>First results page. Default <code>1</code></td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Delivery postal code, e.g. <code>10115</code>. Must belong to the marketplace set by <code>domain</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/amazon/product`

Returns one Amazon product's title, price, availability, rating, images, and variants.

**Modes:** sync · async · batch

<table><thead><tr><th width="183">Name</th><th width="92">Type</th><th width="84">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>ASIN, e.g. <code>B0935DN1BN</code>. Not a URL or title</td></tr><tr><td><code>autoselect_variant</code></td><td>boolean</td><td>no</td><td>Follows the listing's default variant instead of returning the bare parent listing. Set when a parent ASIN returns no price</td></tr><tr><td><code>check_empty_geo</code></td><td>boolean</td><td>no</td><td>Fails the request instead of returning content that ignored <code>location</code></td></tr><tr><td><code>currency</code></td><td>string</td><td>no</td><td>Currency to report prices in, e.g. <code>EUR</code></td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Marketplace TLD: <code>com</code>, <code>de</code>, <code>co.uk</code>, <code>co.jp</code></td></tr><tr><td><code>locale</code></td><td>string</td><td>no</td><td>Interface language, e.g. <code>en_US</code></td></tr><tr><td><code>safe_search</code></td><td>boolean</td><td>no</td><td>Amazon's content filter</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Delivery postal code, e.g. <code>10115</code>. Must belong to the marketplace set by <code>domain</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/amazon/search`

Returns Amazon search results, with paid placements marked.

**Modes:** sync · async · batch

<table><thead><tr><th width="156">Name</th><th width="91">Type</th><th width="90">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Search keyword</td></tr><tr><td><code>category_id</code></td><td>string</td><td>no</td><td>Restricts to an Amazon browse node</td></tr><tr><td><code>check_empty_geo</code></td><td>boolean</td><td>no</td><td>Fails the request instead of returning content that ignored <code>location</code></td></tr><tr><td><code>currency</code></td><td>string</td><td>no</td><td>Currency to report prices in, e.g. <code>EUR</code></td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Marketplace TLD: <code>com</code>, <code>de</code>, <code>co.uk</code>, <code>co.jp</code></td></tr><tr><td><code>locale</code></td><td>string</td><td>no</td><td>Interface language, e.g. <code>en_US</code></td></tr><tr><td><code>max_price</code></td><td>integer</td><td>no</td><td>Highest price to include, in the marketplace's currency</td></tr><tr><td><code>merchant_id</code></td><td>string</td><td>no</td><td>Restricts to one seller's items</td></tr><tr><td><code>min_price</code></td><td>integer</td><td>no</td><td>Lowest price to include, in the marketplace's currency</td></tr><tr><td><code>pages</code></td><td>integer</td><td>no</td><td>Consecutive pages to fetch from <code>start_page</code>. Each page is a separate fetch and charge</td></tr><tr><td><code>refinements</code></td><td>array of strings</td><td>no</td><td>Amazon's filter facets: brand, rating, Prime eligibility. Forwarded verbatim; values differ per marketplace</td></tr><tr><td><code>safe_search</code></td><td>boolean</td><td>no</td><td>Amazon's content filter</td></tr><tr><td><code>sort_by</code></td><td>string</td><td>no</td><td>Amazon's own sort key, e.g. <code>price-asc-rank</code>, <code>review-rank</code>. Forwarded verbatim; values differ per marketplace</td></tr><tr><td><code>start_page</code></td><td>integer</td><td>no</td><td>First results page. Default <code>1</code></td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Delivery postal code, e.g. <code>10115</code>. Must belong to the marketplace set by <code>domain</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/amazon/sellers`

Returns a seller's storefront.

**Modes:** sync · async · batch

<table><thead><tr><th width="158">Name</th><th width="92">Type</th><th width="83">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Seller ID</td></tr><tr><td><code>check_empty_geo</code></td><td>boolean</td><td>no</td><td>Fails the request instead of returning content that ignored <code>location</code></td></tr><tr><td><code>currency</code></td><td>string</td><td>no</td><td>Currency to report prices in, e.g. <code>EUR</code></td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Marketplace TLD: <code>com</code>, <code>de</code>, <code>co.uk</code>, <code>co.jp</code></td></tr><tr><td><code>locale</code></td><td>string</td><td>no</td><td>Interface language, e.g. <code>en_US</code></td></tr><tr><td><code>safe_search</code></td><td>boolean</td><td>no</td><td>Amazon's content filter</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Delivery postal code, e.g. <code>10115</code>. Must belong to the marketplace set by <code>domain</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

### Baker's Plus

#### `POST /v1/scrape/bakersplus`

Returns parsed fields for a Baker's Plus page from a URL you provide.

**Modes:** sync · async

<table><thead><tr><th width="167">Name</th><th width="87">Type</th><th width="84">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>url</code></td><td>string</td><td>yes</td><td>A Baker's Plus product or search URL</td></tr><tr><td><code>delivery_zip</code></td><td>string</td><td>no</td><td>Postal code delivery is quoted for</td></tr><tr><td><code>fulfillment_type</code></td><td>string</td><td>no</td><td>Delivery, pickup, or ship-to-home filter</td></tr><tr><td><code>store_id</code></td><td>string</td><td>no</td><td>The store whose catalogue and prices are returned</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/bakersplus/product`

Returns one Baker's Plus product's price, stock, and details.

**Modes:** sync · async

<table><thead><tr><th width="164">Name</th><th width="87">Type</th><th width="83">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Product ID</td></tr><tr><td><code>delivery_zip</code></td><td>string</td><td>no</td><td>Postal code delivery is quoted for</td></tr><tr><td><code>fulfillment_type</code></td><td>string</td><td>no</td><td>Delivery, pickup, or ship-to-home filter</td></tr><tr><td><code>store_id</code></td><td>string</td><td>no</td><td>The store whose catalogue and prices are returned</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/bakersplus/search`

Returns Baker's Plus search results for a keyword.

**Modes:** sync · async

<table><thead><tr><th width="167">Name</th><th width="88">Type</th><th width="83">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Search keyword</td></tr><tr><td><code>brand</code></td><td>string</td><td>no</td><td>Restricts results to a brand</td></tr><tr><td><code>delivery_zip</code></td><td>string</td><td>no</td><td>Postal code delivery is quoted for</td></tr><tr><td><code>fulfillment_type</code></td><td>string</td><td>no</td><td>Delivery, pickup, or ship-to-home filter</td></tr><tr><td><code>price_range</code></td><td>string</td><td>no</td><td>Price band filter</td></tr><tr><td><code>store_id</code></td><td>string</td><td>no</td><td>The store whose catalogue and prices are returned</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

### Bed Bath and Beyond

#### `POST /v1/scrape/bedbathandbeyond`

Returns parsed fields for a Bed Bath & Beyond page from a URL you provide.

**Modes:** sync · async

<table><thead><tr><th width="133">Name</th><th width="86">Type</th><th width="83">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>url</code></td><td>string</td><td>yes</td><td>A Bed Bath &#x26; Beyond product or search URL</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/bedbathandbeyond/product`

Returns one Bed Bath & Beyond product's price, stock, and details.

**Modes:** sync · async

<table><thead><tr><th width="133">Name</th><th width="92">Type</th><th width="82">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Product ID</td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Storefront TLD</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/bedbathandbeyond/search`

Returns Bed Bath & Beyond search results for a keyword.

**Modes:** sync · async

<table><thead><tr><th width="135">Name</th><th width="88">Type</th><th width="84">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Search keyword</td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Storefront TLD</td></tr><tr><td><code>start_page</code></td><td>integer</td><td>no</td><td>First results page</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

### Best Buy

#### `POST /v1/scrape/bestbuy`

Returns parsed fields for a Best Buy page from a URL you provide.

**Modes:** sync · async

<table><thead><tr><th width="131">Name</th><th width="91">Type</th><th width="85">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>url</code></td><td>string</td><td>yes</td><td>A Best Buy product or search URL</td></tr><tr><td><code>delivery_zip</code></td><td>string</td><td>no</td><td>Postal code delivery is quoted for</td></tr><tr><td><code>store_id</code></td><td>string</td><td>no</td><td>The store whose catalogue and prices are returned</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/bestbuy/product`

Returns one Best Buy product's price, stock, and details.

**Modes:** sync · async

<table><thead><tr><th width="132">Name</th><th width="90">Type</th><th width="85">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Product ID</td></tr><tr><td><code>delivery_zip</code></td><td>string</td><td>no</td><td>Postal code delivery is quoted for</td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Storefront TLD</td></tr><tr><td><code>store_id</code></td><td>string</td><td>no</td><td>The store whose catalogue and prices are returned</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

#### `POST /v1/scrape/bestbuy/search`

Returns Best Buy search results for a keyword.

**Modes:** sync · async

<table><thead><tr><th width="165">Name</th><th width="89">Type</th><th width="88">Required</th><th>Description</th></tr></thead><tbody><tr><td><code>query</code></td><td>string</td><td>yes</td><td>Search keyword</td></tr><tr><td><code>delivery_zip</code></td><td>string</td><td>no</td><td>Postal code delivery is quoted for</td></tr><tr><td><code>domain</code></td><td>string</td><td>no</td><td>Storefront TLD</td></tr><tr><td><code>fulfillment_type</code></td><td>string</td><td>no</td><td>Delivery, pickup, or ship-to-home filter</td></tr><tr><td><code>start_page</code></td><td>integer</td><td>no</td><td>First results page</td></tr><tr><td><code>store_id</code></td><td>string</td><td>no</td><td>The store whose catalogue and prices are returned</td></tr><tr><td><code>output</code></td><td>array of strings</td><td>no</td><td>Formats to return: <code>markdown</code>, <code>html</code>, <code>json</code>, <code>screenshot</code>. Default <code>["html"]</code>. <code>json</code> returns parsed fields. <code>screenshot</code> requires <code>run_js: true</code></td></tr><tr><td><code>json</code></td><td>object</td><td>no</td><td>Custom extraction: <code>{"prompt": string}</code> or <code>{"schema": object}</code>, never both. Overrides the built-in parser</td></tr><tr><td><code>location</code></td><td>string</td><td>no</td><td>Two-letter country code to fetch from, e.g. <code>DE</code></td></tr><tr><td><code>device</code></td><td>string</td><td>no</td><td><code>desktop</code> (default) or <code>mobile</code></td></tr><tr><td><code>run_js</code></td><td>boolean</td><td>no</td><td>Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more</td></tr><tr><td><code>callback_url</code></td><td>string</td><td>no</td><td>Webhook URL for the finished job. Async only. Malformed URLs are rejected with <code>400</code></td></tr><tr><td><code>storage</code></td><td>object</td><td>no</td><td>Delivers the result to a bucket instead of the response: <code>{"type": string, "url": string}</code>. <code>type</code> is <code>s3</code>, <code>s3_gzip</code>, <code>s3_compatible</code>, <code>gcs</code>, or <code>tos</code>. Async only. <code>url</code> is not validated</td></tr></tbody></table>

### Bodega Aurrera

#### `POST /v1/scrape/bodegaaurrera`

Returns parsed fields for a Bodega Aurrera page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Bodega Aurrera product or search URL                                                                                                                                                      |
| `delivery_zip` | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/bodegaaurrera/product`

Returns one Bodega Aurrera product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `domain`           | string           | no       | Storefront TLD                                                                                                                                                                              |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `subdomain`        | string           | no       | Regional storefront subdomain                                                                                                                                                               |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/bodegaaurrera/search`

Returns Bodega Aurrera search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `domain`           | string           | no       | Storefront TLD                                                                                                                                                                              |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `subdomain`        | string           | no       | Regional storefront subdomain                                                                                                                                                               |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Cdiscount

#### `POST /v1/scrape/cdiscount`

Returns parsed fields for a Cdiscount page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Cdiscount product or search URL                                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/cdiscount/product`

Returns one Cdiscount product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/cdiscount/search`

Returns Cdiscount search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### City Market

#### `POST /v1/scrape/citymarket`

Returns parsed fields for a City Market page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A City Market product or search URL                                                                                                                                                         |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/citymarket/product`

Returns one City Market product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/citymarket/search`

Returns City Market search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Costco

#### `POST /v1/scrape/costco`

Returns parsed fields for a Costco page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Costco product or search URL                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/costco/product`

Returns one Costco product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/costco/search`

Returns Costco search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Dcard

#### `POST /v1/scrape/dcard/search`

Returns Dcard search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Dillons

#### `POST /v1/scrape/dillons`

Returns parsed fields for a Dillons page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Dillons product or search URL                                                                                                                                                             |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/dillons/product`

Returns one Dillons product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/dillons/search`

Returns Dillons search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### eBay

#### `POST /v1/scrape/ebay`

Returns parsed fields for a eBay page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A eBay product or search URL                                                                                                                                                                |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/ebay/product`

Returns one eBay product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/ebay/search`

Returns eBay search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 150 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Etsy

#### `POST /v1/scrape/etsy`

Returns parsed fields for a Etsy page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Etsy product or search URL                                                                                                                                                                |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/etsy/product`

Returns one Etsy product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/etsy/search`

Returns Etsy search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `ship_to`      | string           | no       | Shipping destination                                                                                                                                                                        |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Falabella

#### `POST /v1/scrape/falabella`

Returns parsed fields for a Falabella page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Falabella product or search URL                                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/falabella/product`

Returns one Falabella product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/falabella/search`

Returns Falabella search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Flipkart

#### `POST /v1/scrape/flipkart`

Returns parsed fields for a Flipkart page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Flipkart product or search URL                                                                                                                                                            |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/flipkart/product`

Returns one Flipkart product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/flipkart/search`

Returns Flipkart search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Food 4 Less

#### `POST /v1/scrape/foodfourless`

Returns parsed fields for a Food 4 Less page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Food 4 Less product or search URL                                                                                                                                                         |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/foodfourless/product`

Returns one Food 4 Less product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/foodfourless/search`

Returns Food 4 Less search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

Takes the product shape: no `brand` or `price_range`.

***

### Fred Meyer

#### `POST /v1/scrape/fredmeyer`

Returns parsed fields for a Fred Meyer page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Fred Meyer product or search URL                                                                                                                                                          |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/fredmeyer/product`

Returns one Fred Meyer product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/fredmeyer/search`

Returns Fred Meyer search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Fry's Food

#### `POST /v1/scrape/frysfood`

Returns parsed fields for a Fry's Food page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Fry's Food product or search URL                                                                                                                                                          |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/frysfood/product`

Returns one Fry's Food product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/frysfood/search`

Returns Fry's Food search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Gerbes

#### `POST /v1/scrape/gerbes`

Returns parsed fields for a Gerbes page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Gerbes product or search URL                                                                                                                                                              |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/gerbes/product`

Returns one Gerbes product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/gerbes/search`

Returns Gerbes search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Grainger

#### `POST /v1/scrape/grainger`

Returns parsed fields for a Grainger page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Grainger product or search URL                                                                                                                                                            |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/grainger/product`

Returns one Grainger product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/grainger/search`

Returns Grainger search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Harris Teeter

#### `POST /v1/scrape/harristeeter`

Returns parsed fields for a Harris Teeter page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Harris Teeter product or search URL                                                                                                                                                       |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/harristeeter/product`

Returns one Harris Teeter product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/harristeeter/search`

Returns Harris Teeter search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Idealo

#### `POST /v1/scrape/idealo/search`

Returns Idealo search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Indiamart

#### `POST /v1/scrape/indiamart`

Returns parsed fields for a Indiamart page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Indiamart product or search URL                                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/indiamart/product`

Returns one Indiamart product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/indiamart/search`

Returns Indiamart search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Instacart

#### `POST /v1/scrape/instacart`

Returns parsed fields for a Instacart page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Instacart product or search URL                                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/instacart/product`

Returns one Instacart product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/instacart/search`

Returns Instacart search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### King Soopers

#### `POST /v1/scrape/kingsoopers`

Returns parsed fields for a King Soopers page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A King Soopers product or search URL                                                                                                                                                        |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/kingsoopers/product`

Returns one King Soopers product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/kingsoopers/search`

Returns King Soopers search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Kroger

#### `POST /v1/scrape/kroger`

Returns parsed fields for a Kroger page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Kroger product or search URL                                                                                                                                                              |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/kroger/product`

Returns one Kroger product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/kroger/search`

Returns Kroger search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Lazada

#### `POST /v1/scrape/lazada`

Returns parsed fields for a Lazada page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Lazada product or search URL                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/lazada/product`

Returns one Lazada product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/lazada/search`

Returns Lazada search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Lowe's

#### `POST /v1/scrape/lowes`

Returns parsed fields for a Lowe's page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Lowe's product or search URL                                                                                                                                                              |
| `delivery_zip` | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/lowes/product`

Returns one Lowe's product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip` | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/lowes/search`

Returns Lowe's search results for a keyword.

**Modes:** sync · async

| Name                      | Type             | Required | Description                                                                                                                                                                                 |
| ------------------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`                   | string           | yes      | Search keyword                                                                                                                                                                              |
| `delivery_today_tomorrow` | boolean          | no       | Only items that can be delivered today or tomorrow                                                                                                                                          |
| `delivery_zip`            | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `domain`                  | string           | no       | Storefront TLD                                                                                                                                                                              |
| `free_delivery`           | boolean          | no       | Only items eligible for free delivery                                                                                                                                                       |
| `pickup_today`            | boolean          | no       | Only items available for pickup today                                                                                                                                                       |
| `store_id`                | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`                  | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`                    | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`                | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`                  | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`                  | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`            | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`                 | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

`pickup_today` is an availability filter: it changes which products are returned, not just how they are displayed.

***

### Magazine Luiza

#### `POST /v1/scrape/magazineluiza`

Returns parsed fields for a Magazine Luiza page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Magazine Luiza product or search URL                                                                                                                                                      |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/magazineluiza/product`

Returns one Magazine Luiza product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/magazineluiza/search`

Returns Magazine Luiza search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Mariano's

#### `POST /v1/scrape/marianos`

Returns parsed fields for a Mariano's page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Mariano's product or search URL                                                                                                                                                           |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/marianos/product`

Returns one Mariano's product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/marianos/search`

Returns Mariano's search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### MediaMarkt

#### `POST /v1/scrape/mediamarkt`

Returns parsed fields for a MediaMarkt page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A MediaMarkt product or search URL                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/mediamarkt/product`

Returns one MediaMarkt product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/mediamarkt/search`

Returns MediaMarkt search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Menards

#### `POST /v1/scrape/menards`

Returns parsed fields for a Menards page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Menards product or search URL                                                                                                                                                             |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/menards/product`

Returns one Menards product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/menards/search`

Returns Menards search results for a keyword.

**Modes:** sync · async

| Name                       | Type             | Required | Description                                                                                                                                                                                 |
| -------------------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`                    | string           | yes      | Search keyword                                                                                                                                                                              |
| `delivery_eligible`        | boolean          | no       | Only items eligible for delivery                                                                                                                                                            |
| `domain`                   | string           | no       | Storefront TLD                                                                                                                                                                              |
| `fulfillment_center`       | string           | no       | The fulfillment or warehouse location the request is evaluated against                                                                                                                      |
| `in_stock_today`           | boolean          | no       | Only items in stock for same-day availability                                                                                                                                               |
| `pickup_at_store_eligible` | boolean          | no       | Only items eligible for in-store pickup                                                                                                                                                     |
| `start_page`               | integer          | no       | First results page                                                                                                                                                                          |
| `store_id`                 | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`                   | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`                     | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`                 | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`                   | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`                   | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`             | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`                  | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

`in_stock_today` is an availability filter: it changes which products are returned, not just how they are displayed.

***

### Mercado Libre

#### `POST /v1/scrape/mercadolibre`

Returns parsed fields for a Mercado Libre page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Mercado Libre product or search URL                                                                                                                                                       |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/mercadolibre/product`

Returns one Mercado Libre product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/mercadolibre/search`

Returns Mercado Libre search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Mercado Livre

#### `POST /v1/scrape/mercadolivre/product`

Returns one Mercado Livre product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/mercadolivre/search`

Returns Mercado Livre search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Metro Market

#### `POST /v1/scrape/metromarket`

Returns parsed fields for a Metro Market page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Metro Market product or search URL                                                                                                                                                        |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/metromarket/product`

Returns one Metro Market product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/metromarket/search`

Returns Metro Market search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Neobits

#### `POST /v1/scrape/neobits/search`

Returns Neobits search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Petco

#### `POST /v1/scrape/petco`

Returns parsed fields for a Petco page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Petco product or search URL                                                                                                                                                               |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/petco/search`

Returns Petco search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`           | string           | no       | Storefront TLD                                                                                                                                                                              |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `start_page`       | integer          | no       | First results page                                                                                                                                                                          |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Pick 'n Save

#### `POST /v1/scrape/picknsave`

Returns parsed fields for a Pick 'n Save page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Pick 'n Save product or search URL                                                                                                                                                        |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/picknsave/product`

Returns one Pick 'n Save product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/picknsave/search`

Returns Pick 'n Save search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Publix

#### `POST /v1/scrape/publix`

Returns parsed fields for a Publix page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Publix product or search URL                                                                                                                                                              |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/publix/product`

Returns one Publix product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/publix/search`

Returns Publix search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `store_id`     | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### QFC

#### `POST /v1/scrape/qfc`

Returns parsed fields for a QFC page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A QFC product or search URL                                                                                                                                                                 |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/qfc/product`

Returns one QFC product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/qfc/search`

Returns QFC search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Rakuten

#### `POST /v1/scrape/rakuten`

Returns parsed fields for a Rakuten page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A Rakuten product or search URL                                                                                                                                                             |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/rakuten/search`

Returns Rakuten search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Ralphs

#### `POST /v1/scrape/ralphs`

Returns parsed fields for a Ralphs page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Ralphs product or search URL                                                                                                                                                              |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/ralphs/product`

Returns one Ralphs product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/ralphs/search`

Returns Ralphs search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Safeway

#### `POST /v1/scrape/safeway/product`

Returns one Safeway product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `zip_code`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/safeway/search`

Returns Safeway search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `zip_code`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/safeway/category`

Returns the products in a Safeway category.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Category                                                                                                                                                                                    |
| `zip_code`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `zip_code_url` | string           | no       | Postal code formatted for inclusion in the category URL                                                                                                                                     |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Shein

#### `POST /v1/scrape/shein/search`

Returns Shein search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`       | string           | no       | Storefront TLD                                                                                                                                                                              |
| `start_page`   | integer          | no       | First results page                                                                                                                                                                          |
| `subdomain`    | string           | no       | Regional storefront subdomain                                                                                                                                                               |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Smith's

#### `POST /v1/scrape/smithsfoodanddrug`

Returns parsed fields for a Smith's page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Smith's product or search URL                                                                                                                                                             |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/smithsfoodanddrug/product`

Returns one Smith's product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/smithsfoodanddrug/search`

Returns Smith's search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `brand`            | string           | no       | Restricts results to a brand                                                                                                                                                                |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `price_range`      | string           | no       | Price band filter                                                                                                                                                                           |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### Target

#### `POST /v1/scrape/target`

Returns parsed fields for a Target page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Target product or search URL                                                                                                                                                              |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/target/category`

Returns the products in a Target category.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Category                                                                                                                                                                                    |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/target/product`

Returns one Target product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/target/search`

Returns Target search results for a keyword.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Search keyword                                                                                                                                                                              |
| `delivery_zip`     | string           | no       | Postal code delivery is quoted for                                                                                                                                                          |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

***

### TikTok Shop

#### `POST /v1/scrape/tiktok`

Returns parsed fields for a TikTok Shop page from a URL you provide.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`          | string           | yes      | A TikTok Shop product or search URL                                                                                                                                                         |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/tiktok/shop/product`

Returns one TikTok Shop product's price, stock, and details.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Product ID                                                                                                                                                                                  |
| `country`      | string           | no       | National marketplace to query                                                                                                                                                               |
| `uuid`         | string           | no       | Identifies a specific product listing when `query` alone is ambiguous                                                                                                                       |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/tiktok/shop/search`

Returns TikTok Shop search results for a keyword.

**Modes:** sync · async

| Name           | Type             | Required | Description                                                                                                                                                                                 |
| -------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`        | string           | yes      | Search keyword                                                                                                                                                                              |
| `country`      | string           | no       | National marketplace to query                                                                                                                                                               |
| `output`       | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`         | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`     | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`       | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`       | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url` | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`      | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

TikTok Shop is a national marketplace, so it takes `country` instead of `store_id`.

***

### Walmart

#### `POST /v1/scrape/walmart`

Returns parsed fields for a Walmart page from a URL you provide.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`              | string           | yes      | A Walmart product or search URL                                                                                                                                                             |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/walmart/product`

Returns one Walmart product's price, stock, and details.

**Modes:** sync · async

| Name               | Type             | Required | Description                                                                                                                                                                                 |
| ------------------ | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`            | string           | yes      | Product ID                                                                                                                                                                                  |
| `domain`           | string           | no       | Storefront TLD                                                                                                                                                                              |
| `fulfillment_type` | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `store_id`         | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`           | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`             | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`         | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`           | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`           | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`     | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`          | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

#### `POST /v1/scrape/walmart/search`

Returns Walmart search results for a keyword.

**Modes:** sync · async

| Name                | Type             | Required | Description                                                                                                                                                                                 |
| ------------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`             | string           | yes      | Search keyword                                                                                                                                                                              |
| `domain`            | string           | no       | Storefront TLD                                                                                                                                                                              |
| `fulfillment_speed` | string           | no       | Express or standard delivery speed                                                                                                                                                          |
| `fulfillment_type`  | string           | no       | Delivery, pickup, or ship-to-home filter                                                                                                                                                    |
| `max_price`         | integer          | no       | Highest price to include, in the marketplace's currency                                                                                                                                     |
| `min_price`         | integer          | no       | Lowest price to include, in the marketplace's currency                                                                                                                                      |
| `sort_by`           | string           | no       | Walmart's own sort key, forwarded verbatim                                                                                                                                                  |
| `start_page`        | integer          | no       | First results page                                                                                                                                                                          |
| `store_id`          | string           | no       | The store whose catalogue and prices are returned                                                                                                                                           |
| `output`            | array of strings | no       | Formats to return: `markdown`, `html`, `json`, `screenshot`. Default `["html"]`. `json` returns parsed fields. `screenshot` requires `run_js: true`                                         |
| `json`              | object           | no       | Custom extraction: `{"prompt": string}` or `{"schema": object}`, never both. Overrides the built-in parser                                                                                  |
| `location`          | string           | no       | Two-letter country code to fetch from, e.g. `DE`                                                                                                                                            |
| `device`            | string           | no       | `desktop` (default) or `mobile`                                                                                                                                                             |
| `run_js`            | boolean          | no       | Executes page JavaScript before capture. Slower — use a client timeout of 120 seconds or more                                                                                               |
| `callback_url`      | string           | no       | Webhook URL for the finished job. Async only. Malformed URLs are rejected with `400`                                                                                                        |
| `storage`           | object           | no       | Delivers the result to a bucket instead of the response: `{"type": string, "url": string}`. `type` is `s3`, `s3_gzip`, `s3_compatible`, `gcs`, or `tos`. Async only. `url` is not validated |

`fulfillment_speed` changes both the item set and the quoted price.


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/api-reference/dedicated-scrapers/commerce-scrapers.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
