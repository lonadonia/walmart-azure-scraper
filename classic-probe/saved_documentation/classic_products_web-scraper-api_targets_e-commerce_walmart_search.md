> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/products/web-scraper-api/targets/e-commerce/walmart/search.md).

# Search

Extract Walmart search results with parsed data, including pricing, ratings, seller info, variants, fulfillment options, and facets, with filters for price range and sorting.

The `walmart_search` source is designed to retrieve Walmart search result pages. We can return the HTML for any Walmart page you like. Additionally, we can deliver **structured (parsed) output for Walmart search pages**.

{% hint style="info" %}
Besides the parameters listed below, you can include additional parameters such as `user_agent_type`, `geo_location`, `render`, and more to customize your scraping request. Read more [here](/products/web-scraper-api/features.md).
{% endhint %}

## Request samples

{% tabs %}
{% tab title="cURL" %}

```shell
curl 'https://realtime.oxylabs.io/v1/queries' \
--user 'USERNAME:PASSWORD' \
-H 'Content-Type: application/json' \
-d '{
        "source": "walmart_search",
        "query": "iphone",
        "parse": true
    }'
```

{% endtab %}

{% tab title="Python" %}

```python
import requests
from pprint import pprint

# Structure payload.
payload = {
    'source': 'walmart_search',
    'query': 'iphone',
    'parse': True
}

# Get response.
response = requests.request(
    'POST',
    'https://realtime.oxylabs.io/v1/queries',
    auth=('USERNAME', 'PASSWORD'),
    json=payload
)

# Instead of response with job status and results url, this will return the
# JSON response with the result.
pprint(response.json())
```

{% endtab %}

{% tab title="Node.js" %}

```javascript
const https = require("https");

const username = "USERNAME";
const password = "PASSWORD";
const body = {
    source: "walmart_search",
    query: "iphone",
    parse: true
};

const options = {
    hostname: "realtime.oxylabs.io",
    path: "/v1/queries",
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        Authorization:
            "Basic " + Buffer.from(`${username}:${password}`).toString("base64"),
    },
};

const request = https.request(options, (response) => {
    let data = "";

    response.on("data", (chunk) => {
        data += chunk;
    });

    response.on("end", () => {
        const responseData = JSON.parse(data);
        console.log(JSON.stringify(responseData, null, 2));
    });
});

request.on("error", (error) => {
    console.error("Error:", error);
});

request.write(JSON.stringify(body));
request.end();
```

{% endtab %}

{% tab title="HTTP" %}

```http
# The whole string you submit has to be URL-encoded.

https://realtime.oxylabs.io/v1/queries?source=walmart_search&query=iphone&parse=true&access_token=12345abcde
```

{% endtab %}

{% tab title="PHP" %}

```php
<?php

$params = array(
    'source' => 'walmart_search',
    'query' => 'iphone',
    'parse' => true
);

$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, "https://realtime.oxylabs.io/v1/queries");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($params));
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_USERPWD, "USERNAME" . ":" . "PASSWORD");

$headers = array();
$headers[] = "Content-Type: application/json";
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

$result = curl_exec($ch);
echo $result;

if (curl_errno($ch)) {
    echo 'Error:' . curl_error($ch);
}
curl_close($ch);
```

{% endtab %}

{% tab title="Golang" %}

```go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io/ioutil"
    "net/http"
)

func main() {
    const Username = "USERNAME"
    const Password = "PASSWORD"

    payload := map[string]interface{}{
        "source": "walmart_search",
        "query": "iphone",
        "parse": true,
    }

    jsonValue, _ := json.Marshal(payload)

    client := &http.Client{}
    request, _ := http.NewRequest("POST",
        "https://realtime.oxylabs.io/v1/queries",
        bytes.NewBuffer(jsonValue),
    )

    request.SetBasicAuth(Username, Password)
    response, _ := client.Do(request)

    responseText, _ := ioutil.ReadAll(response.Body)
    fmt.Println(string(responseText))
}
```

{% endtab %}

{% tab title="C#" %}

```csharp
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;

namespace OxyApi
{
    class Program
    {
        static async Task Main()
        {
            const string Username = "USERNAME";
            const string Password = "PASSWORD";

            var parameters = new {
                source = "walmart_search",
                query = "iphone",
                parse = true
            };

            var client = new HttpClient();

            Uri baseUri = new Uri("https://realtime.oxylabs.io");
            client.BaseAddress = baseUri;

            var requestMessage = new HttpRequestMessage(HttpMethod.Post, "/v1/queries");
            requestMessage.Content = JsonContent.Create(parameters);

            var authenticationString = $"{Username}:{Password}";
            var base64EncodedAuthenticationString = Convert.ToBase64String(System.Text.ASCIIEncoding.UTF8.GetBytes(authenticationString));
            requestMessage.Headers.Add("Authorization", "Basic " + base64EncodedAuthenticationString);

            var response = await client.SendAsync(requestMessage);
            var contents = await response.Content.ReadAsStringAsync();

            Console.WriteLine(contents);
        }
    }
}
```

{% endtab %}

{% tab title="Java" %}

```java
package org.example;

import okhttp3.*;
import org.json.JSONObject;
import java.util.concurrent.TimeUnit;

public class Main implements Runnable {
    private static final String AUTHORIZATION_HEADER = "Authorization";
    public static final String USERNAME = "USERNAME";
    public static final String PASSWORD = "PASSWORD";

    public void run() {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("source", "walmart_search");
        jsonObject.put("query", "iphone");
        jsonObject.put("parse", true);

        Authenticator authenticator = (route, response) -> {
            String credential = Credentials.basic(USERNAME, PASSWORD);
            return response
                    .request()
                    .newBuilder()
                    .header(AUTHORIZATION_HEADER, credential)
                    .build();
        };

        var client = new OkHttpClient.Builder()
                .authenticator(authenticator)
                .readTimeout(180, TimeUnit.SECONDS)
                .build();

        var mediaType = MediaType.parse("application/json; charset=utf-8");
        var body = RequestBody.create(jsonObject.toString(), mediaType);
        var request = new Request.Builder()
                .url("https://realtime.oxylabs.io/v1/queries")
                .post(body)
                .build();

        try (var response = client.newCall(request).execute()) {
            if (response.body() != null) {
                try (var responseBody = response.body()) {
                    System.out.println(responseBody.string());
                }
            }
        } catch (Exception exception) {
            System.out.println("Error: " + exception.getMessage());
        }

        System.exit(0);
    }

    public static void main(String[] args) {
        new Thread(new Main()).start();
    }
}
```

{% endtab %}

{% tab title="JSON" %}

```json
{
    "source": "walmart_search",
    "query": "iphone",
    "parse": true
}
```

{% endtab %}
{% endtabs %}

## Request parameter values

<table><thead><tr><th width="180">Parameter</th><th>Description</th><th width="160">Default Value</th></tr></thead><tbody><tr><td><mark style="background-color:green;"><strong><code>source</code></strong></mark></td><td>Sets the scraper.</td><td><code>walmart_search</code></td></tr><tr><td><mark style="background-color:green;"><strong><code>query</code></strong></mark></td><td>The keyword or phrase to search for products.</td><td>-</td></tr><tr><td><code>start_page</code></td><td>Starting page number.</td><td><code>1</code></td></tr><tr><td><code>parse</code></td><td>Returns parsed data when set to <code>true</code>. Explore the <a href="#output-data-dictionary">output data dictionary</a>.</td><td><code>false</code></td></tr><tr><td><code>domain</code>, <code>store_id</code>, <code>delivery_zip</code>, <code>fulfillment_type</code>, <code>fulfillment_speed</code>, <code>sort_by</code>, <code>min_price</code>, <code>max_price</code></td><td>Optional localization and filter parameters, see <a href="#localization-and-filtering">Localization and Filtering</a>.</td><td>-</td></tr></tbody></table>

&#x20;   \- mandatory parameter

## Response example

A parsed search page for the query `iphone` (the `results` list is shortened to one item and its `variants` to one):

```json
{
    "results": [
        {
            "content": {
                "location": {
                    "city": "Buford",
                    "state": "GA",
                    "store_id": "1314",
                    "zipcode": "30518"
                },
                "page_details": {
                    "last_visible_page": 14,
                    "page": 1,
                    "total_results": 163937
                },
                "parse_status_code": 12000,
                "results": [
                    {
                        "fulfillment": {
                            "delivery": false,
                            "free_shipping": false,
                            "pickup": false,
                            "shipping": false
                        },
                        "general": {
                            "badge": "In 100+ people's carts",
                            "image": "https://i5.walmartimages.com/seo/Straight-Talk-Apple-iPhone-16-128GB-Black-Prepaid-Smartphone-Locked-to-Straight-Talk_5020ab6e-5621-4a30-ad28-ff8ff50dda06.04e5097b0e5538a647ec36e73c454530.jpeg?odnHeight=180&odnWidth=180&odnBg=FFFFFF",
                            "out_of_stock": false,
                            "pos": 8,
                            "product_id": "11632865509",
                            "section_title": "Results for \"iphone\"",
                            "sponsored": false,
                            "title": "Straight Talk Apple iPhone 16, 128GB, Black - Prepaid Smartphone [Locked to Straight Talk]",
                            "url": "/ip/Straight-Talk-Apple-iPhone-16-128GB-Black-Prepaid-Smartphone-Locked-to-Straight-Talk/11632865509?classType=VARIANT&athbdg=L1103"
                        },
                        "price": {
                            "currency": "USD",
                            "price": 629
                        },
                        "rating": {
                            "count": 768,
                            "rating": 4.4
                        },
                        "seller": {
                            "id": "F55CDC31AB754BB68FE0B39041159D63",
                            "name": "Walmart.com"
                        },
                        "variants": [
                            {
                                "image": "https://i5.walmartimages.com/asr/5020ab6e-5621-4a30-ad28-ff8ff50dda06.04e5097b0e5538a647ec36e73c454530.jpeg?odnHeight=180&odnWidth=180&odnBg=FFFFFF",
                                "product_id": "11632865509",
                                "title": "Black",
                                "url": "/ip/Straight-Talk-iPhone-16-128GB-Prepaid-Smartphone-Black/11632865509?classType=undefined&variantFieldId=actual_color"
                            }
                        ]
                    }
                ],
                "url": "https://www.walmart.com/search?q=iphone"
            },
            "created_at": "2026-09-26 06:23:20",
            "updated_at": "2026-09-26 06:23:23",
            "page": 1,
            "url": "https://www.walmart.com/search?q=iphone",
            "job_id": "7509497822371138561",
            "status_code": 200,
            "is_render_forced": false,
            "parser_type": "walmart_search_new"
        }
    ]
}
```

## Localization and Filtering <a href="#localization-and-filtering" id="localization-and-filtering"></a>

Walmart tailors availability and prices to a store. The parsed `location` object shows which store the page was served for; without `store_id` or `delivery_zip` it is a random US store.

You can also find the official page of Walmart Stores [**here**](https://www.walmart.com/store-directory)**.** Store numbers for each site are in these lists (`store_id` column):

{% file src="/files/ap2MNKVGUFN3JWB0skN5" %}

{% file src="/files/wCSX58aVk5NMrIqYupUR" %}

{% file src="/files/PT9PVlmdDOZjvEdjriIx" %}

{% file src="/files/2auGBBJ1I64oQhCmfV3g" %}

<table><thead><tr><th width="180">Parameter</th><th>Description</th><th width="150">Default Value</th></tr></thead><tbody><tr><td><code>domain</code></td><td>Walmart site to scrape. Available values: <code>com</code> (walmart.com), <code>ca</code> (walmart.ca), <code>com.mx</code> (walmart.com.mx), <code>co.cr</code> (walmart.co.cr). Prices come in the site's currency (USD, CAD, MXN, CRC).</td><td><code>com</code></td></tr><tr><td><code>store_id</code></td><td>Walmart store number of the chosen site as a string, e.g. <code>"3520"</code>. Take it from the store lists above.</td><td>-</td></tr><tr><td><code>delivery_zip</code></td><td>Delivery ZIP or postal code as a string, e.g. <code>"90210"</code>. The nearest store to the code becomes the page's store.</td><td>-</td></tr><tr><td><code>fulfillment_type</code></td><td>Filters results by how the product can be obtained. Available values: <code>pickup</code>, <code>delivery</code>, <code>shipping</code>. Combine with <code>store_id</code> (pickup) or <code>delivery_zip</code> (delivery).</td><td>-</td></tr><tr><td><code>fulfillment_speed</code></td><td>Filters results by delivery speed. Available values: <code>today</code>, <code>tomorrow</code>, <code>2_days</code>, <code>anytime</code>.</td><td>-</td></tr><tr><td><code>sort_by</code></td><td>Sorting of the results. Available values: <code>best_match</code>, <code>price_low</code>, <code>price_high</code>, <code>best_seller</code>.</td><td><code>best_match</code></td></tr><tr><td><code>min_price</code></td><td>Lowest price to include, as an integer in the site's currency, e.g. <code>100</code>.</td><td>-</td></tr><tr><td><code>max_price</code></td><td>Highest price to include, as an integer in the site's currency, e.g. <code>200</code>.</td><td>-</td></tr></tbody></table>

```json
{
    "source": "walmart_search",
    "query": "milk",
    "store_id": "3520",
    "fulfillment_type": "pickup",
    "sort_by": "price_low",
    "parse": true
}
```

{% hint style="info" %}
If target store is too far away from the given postal code - we will attempt to use the postal code of the target store, otherwise the location will not be set properly. In the case we can't set the `delivery_zip` - Walmart will return their default results without store targeting.
{% endhint %}

## Output data dictionary <a href="#output-data-dictionary" id="output-data-dictionary"></a>

#### **HTML example**

<figure><img src="https://lh7-qw.googleusercontent.com/docsz/AD_4nXfYKEySR7wMk6YcQlNwL_-Md1jjuDsNYTvGWce18gD6iEPG_h6xZNBify4gxkgVVIL8paPHhpH3nM1hJPHgtyDsq_d3hfieZdRKXGwmSq8k2Qor046eUzY-ZVLMuE8V5pHs7AxC-L8aHx5KZVa0ivMlY0c?key=0pdGx4c_qHnNgLislTadiQ" alt=""><figcaption></figcaption></figure>

#### **JSON structure**

The table below presents a detailed list of each search page element we parse, along with its description and data type. The table also includes some metadata.

<table><thead><tr><th width="181.515625">Key</th><th width="348.72265625">Description</th><th width="108.1640625">Type</th></tr></thead><tbody><tr><td><code>url</code></td><td>The URL of the search page.</td><td>string</td></tr><tr><td><code>results</code></td><td>The list of search results.</td><td>array</td></tr><tr><td><code>results.general</code></td><td>General details of the product.</td><td>object</td></tr><tr><td><code>results.price</code></td><td>Pricing details of the product.</td><td>object</td></tr><tr><td><code>results.rating</code></td><td>Rating details of the product.</td><td>object</td></tr><tr><td><code>results.seller</code></td><td>Seller details of the product.</td><td>object</td></tr><tr><td><code>results.variants</code> (optional)</td><td>List of product variants.</td><td>array</td></tr><tr><td><code>results.fulfillment</code></td><td>Fulfillment options of the product.</td><td>object</td></tr><tr><td><code>location</code></td><td>The store the page was served for.</td><td>object</td></tr><tr><td><code>facets</code></td><td>List of the search filters (refinements) shown on the results page.</td><td>array</td></tr><tr><td><code>page_details</code></td><td>Pagination details of the results page.</td><td>object</td></tr><tr><td><code>parse_status_code</code></td><td>The status code of the parsing job. You can see the parser status codes described <a href="/products/web-scraper-api/features/custom-parser.md"><strong>here</strong></a>.</td><td>integer</td></tr><tr><td><code>created_at</code></td><td>The timestamp when the scraping job was created.</td><td>timestamp</td></tr><tr><td><code>updated_at</code></td><td>The timestamp when the scraping job was finished.</td><td>timestamp</td></tr><tr><td><code>page</code></td><td>The page number in the pagination of results.</td><td>integer</td></tr><tr><td><code>url</code></td><td>The URL of the scraped page.</td><td>string</td></tr><tr><td><code>job_id</code></td><td>The ID of the job associated with the scraping job.</td><td>string</td></tr><tr><td><code>status_code</code></td><td>The HTTP status code of the scraped page.</td><td>integer</td></tr><tr><td><code>is_render_forced</code></td><td>Identifies whether rendering has been forced for this request.</td><td>boolean</td></tr><tr><td><code>parser_type</code></td><td>The type of parser used to extract the data.</td><td>string</td></tr></tbody></table>

### **General**

A snippet from [response example](#response-example):

```javascript
...
"general": {
"badge": "In 100+ people's carts",
"image": "https://i5.walmartimages.com/seo/Straight-Talk-Apple-iPhone-16-128GB-Black-Prepaid-Smartphone-Locked-to-Straight-Talk_5020ab6e-5621-4a30-ad28-ff8ff50dda06.04e5097b0e5538a647ec36e73c454530.jpeg?odnHeight=180&odnWidth=180&odnBg=FFFFFF",
"out_of_stock": false,
"pos": 8,
"product_id": "11632865509",
"section_title": "Results for \"iphone\"",
"sponsored": false,
"title": "Straight Talk Apple iPhone 16, 128GB, Black - Prepaid Smartphone [Locked to Straight Talk]",
"url": "/ip/Straight-Talk-Apple-iPhone-16-128GB-Black-Prepaid-Smartphone-Locked-to-Straight-Talk/11632865509?classType=VARIANT&athbdg=L1103"
},
...
```

<table><thead><tr><th width="237">Key (general)</th><th width="372">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>pos</code></td><td>The position of the item within its section.</td><td>integer</td></tr><tr><td><code>url</code></td><td>The URL path of the product page.</td><td>string</td></tr><tr><td><code>image</code></td><td>The URL of the main product image.</td><td>string</td></tr><tr><td><code>title</code></td><td>The title of the product.</td><td>string</td></tr><tr><td><code>product_id</code></td><td>The Walmart product ID.</td><td>string</td></tr><tr><td><code>sponsored</code></td><td>Identifies whether the product is a sponsored listing.</td><td>boolean</td></tr><tr><td><code>badge</code> (optional)</td><td>The badge shown on the listing, e.g. <code>Best seller</code>, <code>Overall pick</code>, <code>In 100+ people's carts</code>.</td><td>string</td></tr><tr><td><code>section_title</code></td><td>The name of the section the product is listed in, e.g. <code>Results for "iphone"</code>.</td><td>string</td></tr><tr><td><code>out_of_stock</code></td><td>Indicates whether the item is out of stock.</td><td>boolean</td></tr></tbody></table>

### Price

A snippet from [response example](#response-example):

```javascript
...
"price": {
"currency": "USD",
"price": 629
},
...
```

<table><thead><tr><th width="237">Key (price)</th><th width="372">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>price</code> (optional)</td><td>The current price of the product.</td><td>float</td></tr><tr><td><code>price_strikethrough</code> (optional)</td><td>The strikethrough price (Was, Bundle or List price).</td><td>float</td></tr><tr><td><code>currency</code></td><td>The ISO 4217 three-letter code of the currency.</td><td>string</td></tr><tr><td><code>price_min</code> (optional)</td><td>The minimum price in the case of range pricing.</td><td>float</td></tr><tr><td><code>price_max</code> (optional)</td><td>The maximum price in the case of range pricing.</td><td>float</td></tr></tbody></table>

### Rating

A snippet from [response example](#response-example):

```javascript
...
"rating": {
"count": 768,
"rating": 4.4
},
...
```

<table><thead><tr><th width="237">Key (rating)</th><th width="372">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>rating</code></td><td>The average rating of the product; <code>0</code> when there are no ratings.</td><td>float</td></tr><tr><td><code>count</code></td><td>The number of ratings.</td><td>integer</td></tr></tbody></table>

### Seller

A snippet from [response example](#response-example):

```json
...
"seller": {
"id": "F55CDC31AB754BB68FE0B39041159D63",
"name": "Walmart.com"
},
...
```

<table><thead><tr><th width="237">Key (seller)</th><th width="372">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>name</code></td><td>The name of the seller.</td><td>string</td></tr><tr><td><code>id</code></td><td>The ID of the seller.</td><td>string</td></tr></tbody></table>

### Variants

A snippet from [response example](#response-example):

```json
...
"variants": [
{
"image": "https://i5.walmartimages.com/asr/5020ab6e-5621-4a30-ad28-ff8ff50dda06.04e5097b0e5538a647ec36e73c454530.jpeg?odnHeight=180&odnWidth=180&odnBg=FFFFFF",
"product_id": "11632865509",
"title": "Black",
"url": "/ip/Straight-Talk-iPhone-16-128GB-Prepaid-Smartphone-Black/11632865509?classType=undefined&variantFieldId=actual_color"
}
]
}
],
...
```

<table><thead><tr><th width="237">Key (variants)</th><th width="372">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>url</code></td><td>The URL path of the product variant.</td><td>string</td></tr><tr><td><code>title</code></td><td>The title of the variant, e.g. a colour.</td><td>string</td></tr><tr><td><code>product_id</code></td><td>The product ID of the variant.</td><td>string</td></tr><tr><td><code>image</code></td><td>The image of the variant.</td><td>string</td></tr></tbody></table>

### Fulfillment

A snippet from [response example](#response-example):

```json
 ...
"fulfillment": {
"delivery": false,
"free_shipping": false,
"pickup": false,
"shipping": false
},
...
```

<table><thead><tr><th width="237">Key (fulfillment)</th><th width="372">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>pickup</code></td><td>Indicates whether in-store pickup is offered.</td><td>boolean</td></tr><tr><td><code>delivery</code></td><td>Indicates whether delivery from a local store is offered.</td><td>boolean</td></tr><tr><td><code>shipping</code></td><td>Indicates whether home shipping is offered.</td><td>boolean</td></tr><tr><td><code>free_shipping</code></td><td>Indicates whether shipping is free.</td><td>boolean</td></tr></tbody></table>

### Facets

```json
... 
"facets": [
    {
        "type": "sort",
        "values": [
            {
                "name": "Best Match"
            },
            {
                "name": "Price Low"
            },
            {
                "name": "Price High"
            },
            {
                "name": "Best Seller"
            }
        ],
        "display_name": "Sort by"
    },
...
```

<table><thead><tr><th width="141.69140625">Key (facets)</th><th width="372.97265625">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>display_name</code></td><td>The display name of the filter, as shown on the page.</td><td>string</td></tr><tr><td><code>type</code></td><td>The filter type.</td><td>string</td></tr><tr><td><code>values</code></td><td>List of the filter's values.</td><td>array</td></tr><tr><td><code>values.name</code></td><td>The name of the filter value.</td><td>string</td></tr><tr><td><code>values.item_count</code> (optional)</td><td>The number of items available for the filter value.</td><td>integer</td></tr></tbody></table>

### Location

A snippet from [response example](#response-example):

```json
...
"location": {
"city": "Buford",
"state": "GA",
"store_id": "1314",
"zipcode": "30518"
},
...
```

<table><thead><tr><th width="237">Key (location)</th><th width="372">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>city</code></td><td>The city of the store the page was served for.</td><td>string</td></tr><tr><td><code>state</code></td><td>The state of the store.</td><td>string</td></tr><tr><td><code>zipcode</code></td><td>The ZIP code of the store.</td><td>string</td></tr><tr><td><code>store_id</code></td><td>The ID of the store.</td><td>string</td></tr></tbody></table>

### Page details

A snippet from [response example](#response-example):

```json
 ...
"page_details": {
"last_visible_page": 14,
"page": 1,
"total_results": 163937
},
...
```

<table><thead><tr><th width="237">Key (page_details)</th><th width="372">Description</th><th>Type</th></tr></thead><tbody><tr><td><code>page</code></td><td>The page number of the results.</td><td>integer</td></tr><tr><td><code>total_results</code></td><td>The total number of results Walmart reports for the query.</td><td>integer</td></tr><tr><td><code>last_visible_page</code></td><td>The last page number available.</td><td>integer</td></tr></tbody></table>


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/products/web-scraper-api/targets/e-commerce/walmart/search.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
