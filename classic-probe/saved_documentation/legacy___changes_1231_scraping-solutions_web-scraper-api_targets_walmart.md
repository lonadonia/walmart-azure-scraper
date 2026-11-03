> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/~/changes/1231/scraping-solutions/web-scraper-api/targets/walmart.md).

# Walmart

Learn how to get Walmart data using the Web Scraper API. Find out more about all supported data sources and an simple request examples

With Web Scraper API, you can scrape and parse various types of **Walmart** pages; below is an overview of all supported scrapers and their respective `source` values.

| Source            | Description                                                                                                                       | Dedicated parser |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| `walmart_search`  | [**Search page**](/~/changes/1231/scraping-solutions/web-scraper-api/targets/walmart/search.md) for a search term of your choice. | Yes.             |
| `walmart_product` | [**Product page**](/~/changes/1231/scraping-solutions/web-scraper-api/targets/walmart/product.md) of a product ID of your choice. | Yes.             |

## Getting started

**Create your API user credentials**: Sign up for a free trial or purchase the product in the [**Oxylabs dashboard**](https://dashboard.oxylabs.io/en/registration) to create your API user credentials (`USERNAME` and `PASSWORD`).

{% hint style="warning" %}
If you need more than one API user for your account, please contact our [**customer support**](mailto:support@oxylabs.io) or message our 24/7 live chat support.
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
    'parse': True,
}

# Get response.
response = requests.request(
    'POST',
    'https://realtime.oxylabs.io/v1/queries',
    auth=('USERNAME', 'PASSWORD'),
    json=payload,
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
    parse: true,
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
		"source":       "walmart_search",
		"query":          "iphone",
		"parse":        true,
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

We use synchronous [**Realtime**](/~/changes/1231/scraping-solutions/web-scraper-api/integration-methods/realtime.md) integration method in our examples. If you would like to use [**Proxy Endpoint**](/~/changes/1231/scraping-solutions/web-scraper-api/integration-methods/proxy-endpoint.md) or asynchronous [**Push-Pull**](/~/changes/1231/scraping-solutions/web-scraper-api/integration-methods/push-pull.md) integration, refer to the [**integration methods**](/~/changes/1231/scraping-solutions/web-scraper-api/integration-methods.md) section.

Optionally, you can include additional parameters such as `user_agent_type`, `parse`, `render` and more to customize your scraping request. Read more:

{% content-ref url="/pages/r6mM4F7G5NQi9p2qufcB" %}
[Features](/~/changes/1231/scraping-solutions/web-scraper-api/features.md)
{% endcontent-ref %}


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/~/changes/1231/scraping-solutions/web-scraper-api/targets/walmart.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
