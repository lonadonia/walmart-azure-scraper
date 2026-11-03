> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/products/web-scraper-api/integration-methods/push-pull.md).

# Push-Pull

Discover the Push-Pull integration method for the Oxylabs Web Scraper API. Submit a job, then poll the results endpoint later using JSON-formatted data.

Push-Pull is our recommended integration method for reliably handling large amounts of data.

{% hint style="success" %}
Visit the Oxylabs GitHub repository for a complete working example of [**Push-Pull integration in Python**](https://github.com/oxylabs/product-integrations/tree/master/scraper-apis/Python/push_pull).
{% endhint %}

Push-Pull is an asynchronous integration method. Upon job submission, you will promptly receive a `JSON` response containing all job details, including job parameters, ID, and URLs for result download and status checking. Once your job is processed, we will update you via a `JSON` payload sent to your server, if you provided a [**callback**](#callback) URL. Results remain available for retrieval for **at least 24 hours** after completion.

With Push-Pull, you can upload your results directly to your [**cloud storage**](/products/web-scraper-api/features/result-processing-and-storage/cloud-storage.md) (Google Cloud Storage, AWS S3, Alibaba Cloud OSS, or other S3-compatible storage).

{% hint style="info" %}
If you prefer not to set up a service for incoming callback notifications, you can simply retrieve your results periodically (*polling*).
{% endhint %}

You can also explore how Push-Pull works using [**Postman**](/integrations/web-scraper-api-integrations/postman.md).

## Single Job

### Endpoint

This endpoint accepts only a single `query` or `URL` value.

```
POST https://data.oxylabs.io/v1/queries
```

### Input

Provide the job parameters in a JSON payload as shown in the examples below. Python and PHP examples include comments for clarity.

{% tabs %}
{% tab title="cURL" %}

```shell
curl --user "USERNAME:PASSWORD" \
'https://data.oxylabs.io/v1/queries' \
-H "Content-Type: application/json" \
 -d '{"source": "universal", "url": "https://www.example.com", "geo_location": "United States", "callback_url": "https://your.callback.url", "storage_type": "s3", "storage_url": "s3://your.storage.bucket.url"}'
```

{% endtab %}

{% tab title="Python" %}

```python
import requests
from pprint import pprint


# Structure payload.
payload = {
    "source": "universal", # Source you choose e.g. "universal"
    "url": "https://www.example.com", # Check the docs of the specific source to see whether you should use "url" or "query"
    "geo_location": "United States", # Some sources accept zip codes or coordinates
    #"render" : "html", # Uncomment if you want to render JavaScript within the page
    #"render" : "png", # Uncomment if you want to take a screenshot of a scraped web page
    #"parse" : True, # Check what sources support parsed data
    "callback_url": "https://your.callback.url", # Required if you use the callback listener
    "storage_type": "s3", 
    "storage_url": "s3://your.storage.bucket.url"
}

# Get response.
response = requests.request(
    'POST',
    'https://data.oxylabs.io/v1/queries',
    auth=('YOUR_USERNAME', 'YOUR_PASSWORD'), #Your credentials go here
    json=payload,
)

# Print prettified response to stdout.
pprint(response.json())
```

{% endtab %}

{% tab title="PHP" %}

```php
<?php

$params = array(
    'source' => 'universal', //Source you choose e.g. "universal"
    'url' => 'https://www.example.com', // Check the docs of the specific source to see whether you should use "url" or "query"
    'geo_location' => 'United States', //Some sources accept zip codes or coordinates
    //'render' => 'html', // Uncomment if you want to render JavaScript within the page
    //'render' => 'png', // Uncomment if you want to take a screenshot of a scraped web page
    //'parse' => TRUE, // Check what sources support parsed data
    'callback_url' => 'https://your.callback.url', //Required if you use the callback listener
    'storage_type' => 's3',
    'storage_url' => 's3://your.storage.bucket.url'
);

$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, "https://data.oxylabs.io/v1/queries");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($params));
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_USERPWD, "YOUR_USERNAME" . ":" . "YOUR_PASSWORD"); //Your credentials go here

$headers = array();
$headers[] = "Content-Type: application/json";
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

$result = curl_exec($ch);
echo $result;

if (curl_errno($ch)) {
    echo 'Error:' . curl_error($ch);
}
curl_close($ch);
?>
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
            const string Username = "YOUR_USERNAME";
            const string Password = "YOUR_PASSWORD";

            var parameters = new Dictionary<string, string>()
            {
                { "source", "universal" },
                { "url", "https://example.com" },
                { "geo_location", "United States" },
                { "callback_url", "https://your.callback.url" },
            };


            var client = new HttpClient();

            Uri baseUri = new Uri("https://data.oxylabs.io");
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
	const Username = "YOUR_USERNAME"
	const Password = "YOUR_PASSWORD"

	payload := map[string]string{
		"source": "universal",
		"url": "https://example.com",
		"geo_location": "United States",
		"callback_url": "https://your.callback.url",
	}

	jsonValue, _ := json.Marshal(payload)

	client := &http.Client{}
	request, _ := http.NewRequest("POST",
		"https://data.oxylabs.io/v1/queries",
		bytes.NewBuffer(jsonValue),
	)

	request.Header.Add("Content-type", "application/json")
	request.SetBasicAuth(Username, Password)
	response, _ := client.Do(request)

	responseText, _ := ioutil.ReadAll(response.Body)
	fmt.Println(string(responseText))
}

```

{% endtab %}

{% tab title="Java" %}

```java
package org.example;

import okhttp3.*;
import org.json.JSONObject;

public class Main implements Runnable {
    private static final String AUTHORIZATION_HEADER = "Authorization";
    public static final String USERNAME = "YOUR_USERNAME";
    public static final String PASSWORD = "YOUR_PASSWORD";

    public void run() {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("source", "universal");
        jsonObject.put("url", "https://example.com");
        jsonObject.put("geo_location", "United States");
        jsonObject.put("callback_url", "https://your.callback.url");

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
                .build();

        var mediaType = MediaType.parse("application/json; charset=utf-8");
        var body = RequestBody.create(jsonObject.toString(), mediaType);
        var request = new Request.Builder()
                .url("https://data.oxylabs.io/v1/queries")
                .post(body)
                .build();

        try (var response = client.newCall(request).execute()) {
            assert response.body() != null;
            System.out.println(response.body().string());
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

{% tab title="Node.js" %}

```javascript
import fetch from 'node-fetch';

const username = 'YOUR_USERNAME';
const password = 'YOUR_PASSWORD';
const body = {
  source: 'universal',
  url: 'https://www.example.com',
  geo_location: 'United States',
  callback_url: 'https://your.callback.url',
};
const response = await fetch('https://data.oxylabs.io/v1/queries', {
  method: 'post',
  body: JSON.stringify(body),
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + Buffer.from(`${username}:${password}`).toString('base64'),
  }
});

console.log(await response.json());
```

{% endtab %}
{% endtabs %}

### Output

The API will respond with a JSON containing the job information, similar to this:

```json
{
  "callback_url": "https://your.callback.url",
  "client_id": 5,
  "context": [
    {...}
  ],
  "created_at": "2026-09-03 00:00:01",
  "domain": "com",
  "geo_location": "United States",
  "id": "12345678900987654321",
  "limit": 10,
  "locale": null,
  "pages": 1,
  "parse": false,
  "parser_type": null,
  "parser_preset": null,
  "parsing_instructions": null,
  "browser_instructions": null,
  "render": null,
  "xhr": false,
  "markdown": false,
  "url": "https://www.example.com",
  "query": "",
  "source": "universal",
  "start_page": 1,
  "status": "pending",
  "storage_type": "s3",
  "storage_url": "YOUR_BUCKET_NAME/12345678900987654321.json",
  "aggregate_name": null,
  "subdomain": "www",
  "content_encoding": "utf-8",
  "updated_at": "2026-09-03 00:00:01",
  "user_agent_type": "desktop",
  "session_info": null,
  "statuses": [],
  "client_notes": null,
  "_links": [
    {
      "rel": "self",
      "href": "http://data.oxylabs.io/v1/queries/12345678900987654321",
      "method": "GET"
    },
    {
      "rel": "results",
      "href": "http://data.oxylabs.io/v1/queries/12345678900987654321/results",
      "method": "GET"
    },
    {
      "rel": "results-content",
      "href_list": [
        "http://data.oxylabs.io/v1/queries/12345678900987654321/results/1/content"
      ],
      "method": "GET"
    },
    {
      "rel": "results-html",
      "href": "http://data.oxylabs.io/v1/queries/12345678900987654321/results?type=raw",
      "method": "GET"
    },
    {
      "rel": "results-content-html",
      "href_list": [
        "http://data.oxylabs.io/v1/queries/12345678900987654321/results/1/content?type=raw"
      ],
      "method": "GET"
    }
  ]
}
```

### Data dictionary

The table below describes the fields returned in the job response. For the input parameters you can send, refer to the documentation page of the source you are using.

<table><thead><tr><th>Key</th><th width="500.90234375">Description</th><th width="114.53125">Type</th></tr></thead><tbody><tr><td><code>created_at</code></td><td>The datetime the job was created at.</td><td>String</td></tr><tr><td><code>client_id</code></td><td>The numerical ID associated with the username of the client making the request.</td><td>String</td></tr><tr><td><code>client_notes</code></td><td>Submitted notes by the client when sending a job.</td><td>String</td></tr><tr><td><code>content_encoding</code></td><td>The encoding of the returned content. Set it in your payload when <a href="/products/web-scraper-api/features/result-processing-and-storage/output-types/download-images.md"><strong>downloading images</strong></a>; it is echoed back in the job response.</td><td>String</td></tr><tr><td><code>id</code></td><td>The unique ID of the job.</td><td>String</td></tr><tr><td><code>statuses</code></td><td>The status codes of the scraping or parsing job. You can see the status codes described <a href="/products/web-scraper-api/response-codes.md"><strong>here</strong></a>.</td><td>Integer</td></tr><tr><td><code>status</code></td><td>The status of the job. <code>pending</code> means the job is still being processed. <code>done</code> means we've completed the job. <code>faulted</code> means we came across errors while trying to complete the job -- and gave up at it.</td><td>String</td></tr><tr><td><code>subdomain</code></td><td>The subdomain of the website.</td><td>String</td></tr><tr><td><code>updated_at</code></td><td>The datetime the job was last updated at. For jobs that are finished (<code>status</code> is <code>done</code> or <code>faulted</code>), this datetime indicates when the job was finished.</td><td>String</td></tr><tr><td><code>_links</code></td><td>The list of links, related to the provided input.</td><td>JSON Array</td></tr><tr><td><code>_links</code>:<code>rel</code></td><td>The link type. <code>self</code> URL contains the metadata of the job, while <code>results</code> URL contains the job results.</td><td>String</td></tr><tr><td><code>_links</code>:<code>href</code></td><td>The URL to the resource.</td><td>String</td></tr><tr><td><code>_links</code>:<code>href_list</code></td><td>The list of URLs to the resource, one per page. Returned <strong>instead of</strong> <code>href</code> on entries whose <code>rel</code> starts with <code>results-content</code>. See <a href="#retrieve-job-content"><strong>Retrieve Job Content</strong></a>.</td><td>JSON Array</td></tr><tr><td><code>_links</code>:<code>method</code></td><td>The HTTP method that should be used to interact with a given URL.</td><td>String</td></tr></tbody></table>

## Callback

The callback is a `POST` request we send to your machine, informing that the data extraction task is completed and providing a URL to download scraped content. This means that you don't need to [**check job status**](#check-job-status) manually. Once the data is here, we will let you know, and all you need to do now is to [**retrieve it**](#retrieve-job-content).

### Input

{% tabs %}
{% tab title="Python" %}

```python
# This is a simple Sanic web server with a route listening for callbacks on localhost:8080.
# It will print job results to stdout.
import requests
from pprint import pprint
from sanic import Sanic, response


AUTH_TUPLE = ('user', 'pass1')

app = Sanic()


# Define /job_listener endpoint that accepts POST requests.
@app.route('/job_listener', methods=['POST'])
async def job_listener(request):
    try:
        res = request.json
        links = res.get('_links', [])
        for link in links:
            if link['rel'] == 'results':
                # Sanic is async, but requests are synchronous, to fully take
                # advantage of Sanic, use aiohttp.
                res_response = requests.request(
                    method='GET',
                    url=link['href'],
                    auth=AUTH_TUPLE,
                )
                pprint(res_response.json())
                break
    except Exception as e:
        print("Listener exception: {}".format(e))
    return response.json(status=200, body={'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

{% endtab %}

{% tab title="PHP" %}

```php
<?php
$stdout = fopen('php://stdout', 'w');

if (isset($_POST)) {
    $result = array_merge($_POST, (array) json_decode(file_get_contents('php://input')));

    $ch = curl_init();

    curl_setopt($ch, CURLOPT_URL, "https://data.oxylabs.io/v1/queries/".$result['id'].'/results');
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "GET");
    curl_setopt($ch, CURLOPT_USERPWD, "user" . ":" . "pass1");

    $result = curl_exec($ch);
    fwrite($stdout, $result);

    if (curl_errno($ch)) {
        echo 'Error:' . curl_error($ch);
    }
    curl_close($ch);
}
?>
```

{% endtab %}

{% tab title="C#" %}

```csharp
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using System;
using System.Collections.Generic;
using System.Net.Http;

namespace OxyApiWeb
{
    public class Callback
    {
        public Link[] _links { get; set; }
    }

    public class Link
    {
        public string rel { get; set; }
        public string href { get; set; }
    }

    public class Startup
    {
        private const string USERNAME = "YOUR_USERNAME";
        private const string PASSWORD = "YOUR_PASSWORD";

        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;

            client = new HttpClient();
        }

        public IConfiguration Configuration { get; }

        private HttpClient client;

        public void ConfigureServices(IServiceCollection services)
        {
            services.AddControllers();
        }

        public void Configure(IApplicationBuilder app, IWebHostEnvironment env)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }

            app.UseRouting();

            app.UseAuthorization();

            app.UseEndpoints(endpoints =>
            {
                endpoints.MapPost("/job_listener", async context =>
                {
                    var callback = await System.Text.Json.JsonSerializer.DeserializeAsync<Callback>(context.Request.Body);

                    foreach (var link in callback._links)
                    {
                        if (link.rel != "results")
                        {
                            continue;
                        }

                        var requestMessage = new HttpRequestMessage(HttpMethod.Get, new Uri(link.href));

                        var authenticationString = $"{USERNAME}:{PASSWORD}";
                        var base64EncodedAuthenticationString = Convert.ToBase64String(System.Text.ASCIIEncoding.UTF8.GetBytes(authenticationString));
                        requestMessage.Headers.Add("Authorization", "Basic " + base64EncodedAuthenticationString);

                        var response = await client.SendAsync(requestMessage);
                        var contents = await response.Content.ReadAsStringAsync();

                        Console.WriteLine(contents);

                    }

                    var okMessage = new Dictionary<string, string>()
                    {
                        { "message", "ok" }
                    };

                    await System.Text.Json.JsonSerializer.SerializeAsync(context.Response.Body, okMessage);
                });
            });
        }
    }
}

```

{% endtab %}

{% tab title="Golang" %}

```go
package main

import (
	"fmt"
	"github.com/labstack/echo/v4"
	"io/ioutil"
	"net/http"
)

const Username = "YOUR_USERNAME"
const Password = "YOUR_PASSWORD"

type Callback struct {
	Links []Link `json:"_links"`
}

type Link struct {
	Href string `json:"href"`
	Method string `json:"method"`
	Rel string `json:"rel"`
}

func main() {
	echoServer := echo.New()
	client := &http.Client{}

	echoServer.POST("/job_listener", func(context echo.Context) error {
		callback := new(Callback)
		if err := context.Bind(callback); err != nil {
			return err
		}

		for _, link := range callback.Links {
			if link.Rel != "results" {
				continue
			}

			request, _ := http.NewRequest("GET",
				link.Href,
				nil,
			)

			request.Header.Add("Content-type", "application/json")
			request.SetBasicAuth(Username, Password)
			response, _ := client.Do(request)

			responseText, _ := ioutil.ReadAll(response.Body)
			fmt.Println(string(responseText))
		}
		return context.JSON(http.StatusOK, map[string]string { "status": "ok" })
	})

	echoServer.Logger.Fatal(echoServer.Start(":8080"))
}
```

{% endtab %}

{% tab title="Java" %}

```java
package org.example;

import okhttp3.*;
import com.sun.net.httpserver.HttpServer;
import org.apache.commons.io.IOUtils;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.Objects;

public class Main implements Runnable {
    private static final String AUTHORIZATION_HEADER = "Authorization";
    public static final String USERNAME = "YOUR_USERNAME";
    public static final String PASSWORD = "YOUR_PASSWORD";

    public void run() {
        HttpServer server = null;
        try {
            server = HttpServer.create(new InetSocketAddress("0.0.0.0", 8080), 0);
        } catch (IOException exception) {
            exception.printStackTrace();
            System.exit(1);
        }

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
                .build();

        server.createContext("/job_listener", exchange -> {
            var requestBody = IOUtils.toString(exchange.getRequestBody(), StandardCharsets.UTF_8);
            JSONObject requestJson = new JSONObject(requestBody);
            JSONArray links = requestJson.getJSONArray("_links");
            for (var link : links.toList()) {
                var linkMap = (Map<?, ?>)link;
                if (!Objects.equals(linkMap.get("rel"), "results")) {
                    continue;
                }

                var request = new Request.Builder()
                        .url((String) linkMap.get("href"))
                        .get()
                        .build();

                try (var response = client.newCall(request).execute()) {
                    assert response.body() != null;
                    System.out.println(response.body().string());
                } catch (Exception exception) {
                    System.out.println("Error: " + exception.getMessage());
                }
            }

            var responseJson = new JSONObject();
            responseJson.put("status", "ok");
            exchange.sendResponseHeaders(200, responseJson.toString().length());

            OutputStream responseBody = exchange.getResponseBody();
            responseBody.write(responseJson.toString().getBytes());
            responseBody.flush();
            responseBody.close();

            exchange.close();
        });
        server.setExecutor(null);
        server.start();
    }

    public static void main(String[] args) {
        new Thread(new Main()).start();
    }
}
```

{% endtab %}

{% tab title="Node.js" %}

```javascript
import express from 'express'
import fetch from 'node-fetch';

const username = 'YOUR_USERNAME';
const password = 'YOUR_PASSWORD';

const app = express();
app.use(express.json());

app.post('/job_listener', async(request, response) => {
  for (const index in request.body._links) {
    const link = request.body._links[index];
    if (link.rel !== 'results') {
      continue;
    }

    const jobResultResponse = await fetch(link.href, {
      method: 'get',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Basic ' + Buffer.from(`${username}:${password}`).toString('base64'),
      }
    });

    console.log(await jobResultResponse.json());
  }

  response.send({status: 'ok'});
});

app.listen(8080);
```

{% endtab %}
{% endtabs %}

### Output

```json
{
  "callback_url": "https://your.callback.url",
  "client_id": 5,
  "context": [
    {...}
  ],
  "created_at": "2026-09-03 00:00:01",
  "domain": "com",
  "geo_location": "United States",
  "id": "12345678900987654321",
  "limit": 10,
  "locale": null,
  "pages": 1,
  "parse": false,
  "parser_type": null,
  "parser_preset": null,
  "parsing_instructions": null,
  "browser_instructions": null,
  "render": null,
  "xhr": false,
  "markdown": false,
  "url": "https://www.example.com",
  "query": "",
  "source": "universal",
  "start_page": 1,
  "status": "done",
  "storage_type": null,
  "storage_url": null,
  "aggregate_name": null,
  "subdomain": "www",
  "content_encoding": "utf-8",
  "updated_at": "2026-09-03 00:00:15",
  "user_agent_type": "desktop",
  "session_info": null,
  "statuses": [],
  "client_notes": null,
  "_links": [
    {
      "rel": "self",
      "href": "http://data.oxylabs.io/v1/queries/12345678900987654321",
      "method": "GET"
    },
    {
      "rel": "results",
      "href": "http://data.oxylabs.io/v1/queries/12345678900987654321/results",
      "method": "GET"
    },
    {
      "rel": "results-content",
      "href_list": [
        "http://data.oxylabs.io/v1/queries/12345678900987654321/results/1/content"
      ],
      "method": "GET"
    },
    {
      "rel": "results-html",
      "href": "http://data.oxylabs.io/v1/queries/12345678900987654321/results?type=raw",
      "method": "GET"
    },
    {
      "rel": "results-content-html",
      "href_list": [
        "http://data.oxylabs.io/v1/queries/12345678900987654321/results/1/content?type=raw"
      ],
      "method": "GET"
    }
  ]
}
```

## Check Job Status

If you provided a valid callback URL when submitting your job, we will notify you upon completion by sending a `JSON` payload to the specified callback URL. This payload will indicate that the job has been completed and its status set to `done`.

However, if you submitted a job without using [**callback service**](#callback), you can check the job status manually. Retrieve the URL from the `href` field in the `rel:self` section of the response message received after job submission. The URL for checking the job status will resemble the following: `http://data.oxylabs.io/v1/queries/12345678900987654321`. Querying this URL will return the job information, including its current `status`.

### Endpoint

```
GET https://data.oxylabs.io/v1/queries/{id}
```

### Input

{% tabs %}
{% tab title="cURL" %}

```bash
curl --user "USERNAME:PASSWORD" \
'https://data.oxylabs.io/v1/queries/12345678900987654321'
```

{% endtab %}

{% tab title="Python" %}

```python
import requests
from pprint import pprint

# Get response from stats endpoint.
response = requests.request(
    method='GET',
    url='https://data.oxylabs.io/v1/queries/12345678900987654321',
    auth=('user', 'pass1'),
)

# Print prettified JSON response to stdout.
pprint(response.json())
```

{% endtab %}

{% tab title="PHP" %}

```php
<?php

$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, "https://data.oxylabs.io/v1/queries/12345678900987654321");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "GET");
curl_setopt($ch, CURLOPT_USERPWD, "user" . ":" . "pass1");

$result = curl_exec($ch);
echo $result;

if (curl_errno($ch)) {
    echo 'Error:' . curl_error($ch);
}
curl_close($ch);
?>
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
            const string JobId = "12345678900987654321";
            const string Username = "YOUR_USERNAME";
            const string Password = "YOUR_PASSWORD";

            var client = new HttpClient();

            Uri baseUri = new Uri("https://data.oxylabs.io");
            client.BaseAddress = baseUri;

            var requestMessage = new HttpRequestMessage(HttpMethod.Get, $"/v1/queries/{JobId}");

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

{% tab title="Golang" %}

```go
package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
)

func main() {
	const JobId = "12345678900987654321"
	const Username = "YOUR_USERNAME"
	const Password = "YOUR_PASSWORD"

	client := &http.Client{}
	request, _ := http.NewRequest("GET",
		fmt.Sprintf("https://data.oxylabs.io/v1/queries/%s", JobId),
		nil,
	)

	request.Header.Add("Content-type", "application/json")
	request.SetBasicAuth(Username, Password)
	response, _ := client.Do(request)

	responseText, _ := ioutil.ReadAll(response.Body)
	fmt.Println(string(responseText))
}
```

{% endtab %}

{% tab title="Java" %}

```java
package org.example;

import okhttp3.*;

public class Main implements Runnable {
    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String JOB_ID = "12345678900987654321";
    public static final String USERNAME = "YOUR_USERNAME";
    public static final String PASSWORD = "YOUR_PASSWORD";

    public void run() {
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
                .build();

        var request = new Request.Builder()
                .url(String.format("https://data.oxylabs.io/v1/queries/%s", JOB_ID))
                .get()
                .build();

        try (var response = client.newCall(request).execute()) {
            assert response.body() != null;
            System.out.println(response.body().string());
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

{% tab title="Node.js" %}

```javascript
import fetch from 'node-fetch';

const jobId = '12345678900987654321';
const username = 'YOUR_USERNAME';
const password = 'YOUR_PASSWORD';
const response = await fetch(`https://data.oxylabs.io/v1/queries/${jobId}`, {
  method: 'get',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + Buffer.from(`${username}:${password}`).toString('base64'),
  }
});

console.log(await response.json());
```

{% endtab %}
{% endtabs %}

### Output

Upon completion of the job, the API will respond with query information in JSON format. The job status will be changed to `done`, indicating that the job is finished. You can retrieve the content by querying one of the provided links. Additionally, the response will include the timestamp of when the job was last updated, allowing you to track its processing time.

```json
{
    "callback_url": null,
    "client_id": 5,
    "context": [
        {...}
    ],
    "created_at": "2026-09-03 00:00:01",
    "domain": "com",
    "geo_location": "United States",
    "id": "12345678900987654321",
    "limit": 10,
    "locale": null,
    "pages": 1,
    "parse": false,
    "parser_type": null,
    "parser_preset": null,
    "parsing_instructions": null,
    "browser_instructions": null,
    "render": null,
    "xhr": false,
    "markdown": false,
    "url": "https://www.example.com",
    "query": "",
    "source": "universal",
    "start_page": 1,
    "status": "done",
    "storage_type": null,
    "storage_url": null,
    "aggregate_name": null,
    "subdomain": "www",
    "content_encoding": "utf-8",
    "updated_at": "2026-09-03 00:00:15",
    "user_agent_type": "desktop",
    "session_info": null,
    "statuses": [],
    "client_notes": null,
    "_links": [
        {
            "rel": "self",
            "href": "http://data.oxylabs.io/v1/queries/12345678900987654321",
            "method": "GET"
        },
        {
            "rel": "results",
            "href": "http://data.oxylabs.io/v1/queries/12345678900987654321/results",
            "method": "GET"
        },
        {
            "rel": "results-content",
            "href_list": [
                "http://data.oxylabs.io/v1/queries/12345678900987654321/results/1/content"
            ],
            "method": "GET"
        },
        {
            "rel": "results-html",
            "href": "http://data.oxylabs.io/v1/queries/12345678900987654321/results?type=raw",
            "method": "GET"
        },
        {
            "rel": "results-content-html",
            "href_list": [
                "http://data.oxylabs.io/v1/queries/12345678900987654321/results/1/content?type=raw"
            ],
            "method": "GET"
        }
    ]
}
```

## Status values

<table><thead><tr><th width="150">Parameter</th><th>Description</th></tr></thead><tbody><tr><td><code>pending</code></td><td>The job is still being processed and has not been completed.</td></tr><tr><td><code>done</code></td><td>The job is completed. You can retrieve the result by querying the URL provided in the <code>href</code> field under the <code>rel:results</code> section, for example: <code>http://data.oxylabs.io/v1/queries/12345678900987654321/results</code>.</td></tr><tr><td><code>faulted</code></td><td>There was an issue with the job, and we couldn't complete it. You are not charged for any <code>faulted</code> jobs.</td></tr></tbody></table>

## Retrieve Job Content

Once the job is ready to be retrieved, you can use the URL provided in the response under the `rel:results` section. The URL will look like this: `http://data.oxylabs.io/v1/queries/12345678900987654321/results`.

{% hint style="info" %}
The `_links` URLs are returned with an `http://` scheme. Replace it with `https://` before calling them, so that your credentials are not sent unencrypted.
{% endhint %}

### Endpoints

You can retrieve different results types by using the following endpoints:

```
GET https://data.oxylabs.io/v1/queries/{job_id}/results
```

```
GET https://data.oxylabs.io/v1/queries/{job_id}/results?type=raw
```

```
GET https://data.oxylabs.io/v1/queries/{job_id}/results?type=parsed
```

```
GET https://data.oxylabs.io/v1/queries/{job_id}/results?type=png
```

```
GET https://data.oxylabs.io/v1/queries/{job_id}/results?type=xhr
```

```
GET https://data.oxylabs.io/v1/queries/{job_id}/results?type=markdown
```

You may also retrieve [multiple result types](/products/web-scraper-api/features/result-processing-and-storage/output-types/multi-format-output.md) in a single response, for instance:

```
GET https://data.oxylabs.io/v1/queries/{job_id}/results?type=parsed,raw
```

To get one page on its own as raw content rather than inside a JSON object, use the content endpoint, where `{n}` is the page number starting at `1`. The same `type` values apply.

```
GET https://data.oxylabs.io/v1/queries/{job_id}/results/{n}/content
```

### Input

Below are code examples demonstrating how to use the `/results` endpoint:

{% tabs %}
{% tab title="cURL" %}

```shell
curl --user "USERNAME:PASSWORD" \
'https://data.oxylabs.io/v1/queries/12345678900987654321/results'
```

{% endtab %}

{% tab title="Python" %}

```python
import requests
from pprint import pprint

# Get response from stats endpoint.
response = requests.request(
    method='GET',
    url='https://data.oxylabs.io/v1/queries/12345678900987654321/results',
    auth=('user', 'pass1'),
)

# Print prettified JSON response to stdout.
pprint(response.json())
```

{% endtab %}

{% tab title="PHP" %}

```php
<?php

$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, "https://data.oxylabs.io/v1/queries/12345678900987654321/results");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "GET");
curl_setopt($ch, CURLOPT_USERPWD, "user" . ":" . "pass1");

$result = curl_exec($ch);
echo $result;

if (curl_errno($ch)) {
    echo 'Error:' . curl_error($ch);
}
curl_close($ch);
?>
```

{% endtab %}

{% tab title="C#" %}

```csharp
using System;
using System.Net.Http;
using System.Threading.Tasks;

namespace OxyApi
{
    class Program
    {
        static async Task Main()
        {
            const string JobId = "12345678900987654321";
            const string Username = "YOUR_USERNAME";
            const string Password = "YOUR_PASSWORD";

            var client = new HttpClient();

            Uri baseUri = new Uri("https://data.oxylabs.io");
            client.BaseAddress = baseUri;

            var requestMessage = new HttpRequestMessage(HttpMethod.Get, $"/v1/queries/{JobId}/results");

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

{% tab title="Golang" %}

```go
package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
)

func main() {
	const JobId = "12345678900987654321"
	const Username = "YOUR_USERNAME"
	const Password = "YOUR_PASSWORD"

	client := &http.Client{}
	request, _ := http.NewRequest("GET",
		fmt.Sprintf("https://data.oxylabs.io/v1/queries/%s/results", JobId),
		nil,
	)

	request.Header.Add("Content-type", "application/json")
	request.SetBasicAuth(Username, Password)
	response, _ := client.Do(request)

	responseText, _ := ioutil.ReadAll(response.Body)
	fmt.Println(string(responseText))
}
```

{% endtab %}

{% tab title="Java" %}

```java
package org.example;

import okhttp3.*;

public class Main implements Runnable {
    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String JOB_ID = "12345678900987654321";
    public static final String USERNAME = "YOUR_USERNAME";
    public static final String PASSWORD = "YOUR_PASSWORD";

    public void run() {
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
                .build();

        var request = new Request.Builder()
                .url(String.format("https://data.oxylabs.io/v1/queries/%s/results", JOB_ID))
                .get()
                .build();

        try (var response = client.newCall(request).execute()) {
            assert response.body() != null;
            System.out.println(response.body().string());
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

{% tab title="Node.js" %}

```javascript
import fetch from 'node-fetch';

const jobId = '12345678900987654321';
const username = 'YOUR_USERNAME';
const password = 'YOUR_PASSWORD';
const response = await fetch(`https://data.oxylabs.io/v1/queries/${jobId}/results`, {
  method: 'get',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + Buffer.from(`${username}:${password}`).toString('base64'),
  }
});

console.log(await response.json());
```

{% endtab %}
{% endtabs %}

### Output

This table explains the default result type based on the parameters included in the payload of the API request.

| Render parameter | Parse parameter | XHR parameter | Default output |
| ---------------- | --------------- | ------------- | -------------- |
| -                | -               | -             | html           |
| `html`           | -               | -             | html           |
| `html`           | -               | `true`        | xhr            |
| `html`           | `true`          | `true`        | parsed         |
| `png`            | -               | -             | png            |
| -                | `true`          | -             | parsed         |
| `html`           | `true`          | -             | parsed         |
| `png`            | `true`          | -             | png            |

By default, the `/results` endpoint returns only the default output for your payload. To receive additional result types, add the `type` query parameter shown under [**Endpoints**](/products/web-scraper-api/integration-methods/push-pull.md#endpoints) above. Each requested type is returned as a separate entry in the `results` array. This is the [**multiple result types**](/products/web-scraper-api/features/result-processing-and-storage/output-types/multi-format-output.md) feature, and it works the same way in Push-Pull and [**Realtime**](/products/web-scraper-api/integration-methods/realtime.md).

Below is a sample response of the `/results` endpoint. Alongside `results`, it returns a `job` object holding the same job details described in the [**Data dictionary**](#data-dictionary), abbreviated here. Some sources also return `_request`, `_response` and `session_info` on each result.

```json
{
  "results": [
    {
      "content": "<!doctype html><html>CONTENT</html>",
      "created_at": "2026-09-03 00:00:01",
      "updated_at": "2026-09-03 00:00:15",
      "page": 1,
      "url": "https://www.example.com",
      "job_id": "12345678900987654321",
      "is_render_forced": false,
      "status_code": 200,
      "type": "raw",
      "_request": {
        "cookies": [],
        "headers": {...}
      },
      "_response": {
        "cookies": [],
        "headers": {...}
      },
      "session_info": {
        "expires_at": null,
        "id": null,
        "remaining": null
      }
    }
  ],
  "job": {...}
}
```

The results can be automatically retrieved without periodically checking job status by setting up [**Callback**](#callback) service. To do that, specify the URL of a server that is able to accept incoming HTTP(S) requests while submitting a job. When our system completes the job, it will `POST` a JSON payload to the provided URL, and the Callback service will download the results as described in the [**Callback implementation example**](#callback).

## Batch Query

Scraper APIs supports submitting up to 5,000 `query` or `url` parameter values within a single batch request.

### Endpoint

```
POST https://data.oxylabs.io/v1/queries/batch
```

The system will handle every `query` or `url` submitted as a separate job. If you provide a callback URL, you will get a separate call for each keyword. Otherwise, our initial response will contain job `id`s for all keywords. For example, if you sent 50 keywords, we will return 50 unique job `id`s.

{% hint style="info" %}
**IMPORTANT:** With `/batch` endpoint, you can only submit lists of `query`or `url`parameter values (depending on the `source` you use). All other parameters should have singular values.
{% endhint %}

### Input

You need to post query parameters as a JSON payload. Here is how you submit a batch job:

{% tabs %}
{% tab title="cURL" %}

```shell
curl --user "USERNAME:PASSWORD" \
'https://data.oxylabs.io/v1/queries/batch' \
-H 'Content-Type: application/json' \
-d '@keywords.json'
```

{% endtab %}

{% tab title="Python" %}

```python
import requests
import json
from pprint import pprint


# Get payload from file.
with open('keywords.json', 'r') as f:
    payload = json.loads(f.read())

response = requests.request(
    'POST',
    'https://data.oxylabs.io/v1/queries/batch',
    auth=('user', 'pass1'),
    json=payload,
)

# Print prettified response.
pprint(response.json())
```

{% endtab %}

{% tab title="PHP" %}

```php
<?php

$paramsFile = file_get_contents(realpath("keywords.json"));
$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, "https://data.oxylabs.io/v1/queries/batch");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_POSTFIELDS, $paramsFile);
curl_setopt($ch, CURLOPT_POST, 1);
curl_setopt($ch, CURLOPT_USERPWD, "user" . ":" . "pass1");

$headers = array();
$headers[] = "Content-Type: application/json";
curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);

$result = curl_exec($ch);
echo $result;

if (curl_errno($ch)) {
    echo 'Error:' . curl_error($ch);
}
curl_close($ch);
?>
```

{% endtab %}

{% tab title="C#" %}

```csharp
using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

namespace OxyApi
{
    class Program
    {
        static async Task Main()
        {
            const string Username = "YOUR_USERNAME";
            const string Password = "YOUR_PASSWORD";


            var content = File.ReadAllText(@"C:\path\to\keywords.json");
                
            var client = new HttpClient();

            var requestMessage = new HttpRequestMessage(HttpMethod.Post, new Uri("https://data.oxylabs.io/v1/queries/batch"));
            requestMessage.Content = new StringContent(content, Encoding.UTF8, "application/json");


            var authenticationString = $"{Username}:{Password}";
            var base64EncodedAuthenticationString = Convert.ToBase64String(ASCIIEncoding.UTF8.GetBytes(authenticationString));
            requestMessage.Headers.Add("Authorization", "Basic " + base64EncodedAuthenticationString);

            var response = await client.SendAsync(requestMessage);
            var contents = await response.Content.ReadAsStringAsync();

            Console.WriteLine(contents);
        }
    }
}
```

{% endtab %}

{% tab title="Golang" %}

```go
package main

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
)

func main() {
	const Username = "YOUR_USERNAME"
	const Password = "YOUR_PASSWORD"

	content, err := os.ReadFile("keywords.json")
	if err != nil {
		panic(err)
	}

	client := &http.Client{}
	request, _ := http.NewRequest("POST",
		"https://data.oxylabs.io/v1/queries/batch",
		bytes.NewBuffer(content),
	)

	request.Header.Add("Content-type", "application/json")
	request.SetBasicAuth(Username, Password)
	response, _ := client.Do(request)

	responseText, _ := ioutil.ReadAll(response.Body)
	fmt.Println(string(responseText))
}
```

{% endtab %}

{% tab title="Java" %}

```java
import okhttp3.*;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class Main implements Runnable {
    private static final String AUTHORIZATION_HEADER = "Authorization";
    public static final String USERNAME = "YOUR_USERNAME";
    public static final String PASSWORD = "YOUR_PASSWORD";

    public void run() {
        Path filePath = Path.of("/path/to/keywords.json");
        String jsonContent = null;
        try {
            jsonContent = Files.readString(filePath);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

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
                .build();

        var mediaType = MediaType.parse("application/json; charset=utf-8");
        var body = RequestBody.create(jsonContent, mediaType);
        var request = new Request.Builder()
                .url("https://data.oxylabs.io/v1/queries/batch")
                .post(body)
                .build();

        try (var response = client.newCall(request).execute()) {
            assert response.body() != null;
            System.out.println(response.body().string());
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

{% tab title="Node.js" %}

```javascript
import fetch from 'node-fetch';
import fs from 'fs'

const username = 'YOUR_USERNAME';
const password = 'YOUR_PASSWORD';

const payload = fs.readFileSync('keywords.json').toString();

const response = await fetch('https://data.oxylabs.io/v1/queries/batch', {
  method: 'post',
  body: payload,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + Buffer.from(`${username}:${password}`).toString('base64'),
  }
});

console.log(await response.json());
```

{% endtab %}
{% endtabs %}

You may notice that the code example above doesn't explain how the JSON payload should be formatted and points out to a pre-made JSON file. Below is the content of `keywords.json` file, containing multiple `query` parameter values:

```json
{  
   "query":[  
      "adidas",
      "nike",
      "reebok"
   ],
   "source": "google_shopping_search",
   "callback_url": "https://your.callback.url"
}
```

...and here is a `keywords.json` batch input file, containing multiple URLs:

```json
{  
   "url":[  
      "https://example.com/url1.html",
      "https://example.com/url2.html",
      "https://example.com/url3.html"
   ],
   "source": "universal",
   "callback_url": "https://your.callback.url"
}
```

### Output

The API will respond with a JSON object, containing the job information for each job created. The response will be similar to this:

```json
{
  "queries": [
    {
      "callback_url": "https://your.callback.url",
      "created_at": "2026-09-03 00:00:01",
      "id": "12345678900987654321",
      "query": "adidas",
      "source": "google_shopping_search",
      "status": "pending",
      {...}
      "_links": [
        {
          "rel": "self",
          "href": "http://data.oxylabs.io/v1/queries/12345678900987654321",
          "method": "GET"
        },
        {
          "rel": "results",
          "href": "http://data.oxylabs.io/v1/queries/12345678900987654321/results",
          "method": "GET"
        },
        {...}
      ]
    },
    {
      "callback_url": "https://your.callback.url",
      "created_at": "2026-09-03 00:00:01",
      "id": "12345678901234567890",
      "query": "nike",
      "source": "google_shopping_search",
      "status": "pending",
      {...}
      "_links": [
        {
          "rel": "self",
          "href": "http://data.oxylabs.io/v1/queries/12345678901234567890",
          "method": "GET"
        },
        {
          "rel": "results",
          "href": "http://data.oxylabs.io/v1/queries/12345678901234567890/results",
          "method": "GET"
        },
        {...}
      ]
    },
    {
      "callback_url": "https://your.callback.url",
      "created_at": "2026-09-03 00:00:01",
      "id": "01234567899876543210",
      "query": "reebok",
      "source": "google_shopping_search",
      "status": "pending",
      {...}
      "_links": [
        {
          "rel": "self",
          "href": "http://data.oxylabs.io/v1/queries/01234567899876543210",
          "method": "GET"
        },
        {
          "rel": "results",
          "href": "http://data.oxylabs.io/v1/queries/01234567899876543210/results",
          "method": "GET"
        },
        {...}
      ]
    }
  ]
}
```

{% hint style="info" %}
Each entry carries the same fields as a single job response; `{...}` marks fields omitted here for brevity.
{% endhint %}

## Get Notifier IP Address List

You may want to whitelist the IPs sending you callback messages or get the list of these IPs for other purposes. You can do this by `GET`ting this endpoint:

### Endpoint

```
GET https://data.oxylabs.io/v1/info/callbacker_ips
```

### Input

The code examples below show how you can access the `/callbacker_ips` endpoint:

{% tabs %}
{% tab title="cURL" %}

```bash
curl --user "USERNAME:PASSWORD" \
'https://data.oxylabs.io/v1/info/callbacker_ips'
```

{% endtab %}

{% tab title="Python" %}

```python
import requests
from pprint import pprint

# Get response from the callback IPs endpoint.
response = requests.request(
    method='GET',
    url='https://data.oxylabs.io/v1/info/callbacker_ips',
    auth=('user', 'pass1'),
)

# Print prettified JSON response to stdout.
pprint(response.json())
```

{% endtab %}

{% tab title="PHP" %}

```php
<?php

$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, "https://data.oxylabs.io/v1/info/callbacker_ips");
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_CUSTOMREQUEST, "GET");
curl_setopt($ch, CURLOPT_USERPWD, "user" . ":" . "pass1");

$result = curl_exec($ch);
echo $result;

if (curl_errno($ch)) {
    echo 'Error:' . curl_error($ch);
}
curl_close($ch);
?>
```

{% endtab %}

{% tab title="C#" %}

```csharp
using System;
using System.Net.Http;
using System.Threading.Tasks;

namespace OxyApi
{
    class Program
    {
        static async Task Main()
        {
            const string Username = "YOUR_USERNAME";
            const string Password = "YOUR_PASSWORD";

            var client = new HttpClient();

            Uri baseUri = new Uri("https://data.oxylabs.io");
            client.BaseAddress = baseUri;

            var requestMessage = new HttpRequestMessage(HttpMethod.Get, "/v1/info/callbacker_ips");

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

{% tab title="Golang" %}

```go
package main

import (
	"fmt"
	"io/ioutil"
	"net/http"
)

func main() {
	const Username = "YOUR_USERNAME"
	const Password = "YOUR_PASSWORD"

	client := &http.Client{}
	request, _ := http.NewRequest("GET",
		"https://data.oxylabs.io/v1/info/callbacker_ips",
		nil,
	)

	request.Header.Add("Content-type", "application/json")
	request.SetBasicAuth(Username, Password)
	response, _ := client.Do(request)

	responseText, _ := ioutil.ReadAll(response.Body)
	fmt.Println(string(responseText))
}
```

{% endtab %}

{% tab title="Java" %}

```java
package org.example;

import okhttp3.*;

public class Main implements Runnable {
    private static final String AUTHORIZATION_HEADER = "Authorization";
    public static final String USERNAME = "YOUR_USERNAME";
    public static final String PASSWORD = "YOUR_PASSWORD";

    public void run() {
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
                .build();

        var request = new Request.Builder()
                .url("https://data.oxylabs.io/v1/info/callbacker_ips")
                .get()
                .build();

        try (var response = client.newCall(request).execute()) {
            assert response.body() != null;
            System.out.println(response.body().string());
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

{% tab title="Node.js" %}

```javascript
import fetch from 'node-fetch';

const username = 'YOUR_USERNAME';
const password = 'YOUR_PASSWORD';
const response = await fetch('https://data.oxylabs.io/v1/info/callbacker_ips', {
  method: 'get',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Basic ' + Buffer.from(`${username}:${password}`).toString('base64'),
  }
});

console.log(await response.json());
```

{% endtab %}
{% endtabs %}

### Output

The API will return the list of IPs making callback requests to your system:

```json
{
    "ips": [
        "x.x.x.x",
        "y.y.y.y"
    ]
}
```

## Scheduler

Scheduler is a service that you can use to schedule recurring scraping jobs.

It extends the functionality of Push-Pull integration and is best used together with the [**Cloud integration**](/products/web-scraper-api/features/result-processing-and-storage/cloud-storage.md) functionality.

Visit this page to learn how to use Scheduler feature:

{% content-ref url="/pages/z3H5mSHyKBRg3oOvKpT1" %}
[Scheduler](/products/web-scraper-api/features/scheduler.md)
{% endcontent-ref %}


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/products/web-scraper-api/integration-methods/push-pull.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
