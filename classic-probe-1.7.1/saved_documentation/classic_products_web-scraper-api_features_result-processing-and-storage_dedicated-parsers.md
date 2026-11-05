> For the complete documentation index, see [llms.txt](https://developers.oxylabs.io/llms.txt). Markdown versions of documentation pages are available by appending `.md` to page URLs; this page is available as [Markdown](https://developers.oxylabs.io/products/web-scraper-api/features/result-processing-and-storage/dedicated-parsers.md).

# Dedicated Parsers

Enable dedicated parsers in the Oxylabs Web Scraper API by setting parse=true. Structured JSON output for supported targets like Amazon, Google, Walmart and more.

For some sources of Web Scraper API, we have developed dedicated parsers. If you want to get structured data, add the `parse` parameter and set it to `true`. Find more details in the respective target pages.

<table><thead><tr><th width="180.33333333333331">Target</th><th width="294">Sources</th><th>Types</th></tr></thead><tbody><tr><td><a href="https://developers.oxylabs.io/api-targets/e-commerce/amazon"><strong>Amazon</strong></a></td><td><code>amazon</code>,<br><code>amazon_search</code>,<br><code>amazon_product</code>,<br><code>amazon_pricing</code>,<br><code>amazon_bestsellers</code>,<br><code>amazon_sellers</code></td><td>Search<br>Product<br>Offer listing<br>Best sellers<br>Sellers</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/search-engines/google"><strong>Google</strong></a></td><td><code>google</code>,<br><code>google_search</code>,<br><code>google_ai_mode</code>,<br><code>google_ads</code>,<br><code>google_lens</code>,<br><code>google_scholar</code>,<br><code>google_shopping_search</code>,<br><code>google_shopping_product</code>,<br><code>google_travel_hotels</code></td><td>Web search<br>Image search<br>News search<br>Books search<br>AI Overviews<br>AI Mode<br>Maximum ad rate<br>Lens search<br>Scholar search<br>Google Shopping search<br>Google Shopping product<br>Travel Hotels</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/video-and-social-media/youtube"><strong>YouTube</strong></a></td><td><code>youtube_metadata</code>,<br><code>youtube_channel</code></td><td>Video Metadata<br>Channel</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/llms-and-ai/chatgpt"><strong>ChatGPT</strong></a></td><td><code>chatgpt</code></td><td>Chat</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/llms-and-ai/perplexity"><strong>Perplexity</strong></a></td><td><code>perplexity</code></td><td>Chat</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/llms-and-ai/gemini"><strong>Gemini</strong></a></td><td><code>gemini</code></td><td>Chat</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/search-engines/bing"><strong>Bing</strong></a></td><td><code>bing</code>,<br><code>bing_search</code></td><td>Search</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/e-commerce/walmart"><strong>Walmart</strong></a><br></td><td><code>walmart</code>,<br><code>walmart_search</code>,<br><code>walmart_product</code></td><td>Search<br>Product<br>Category</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/e-commerce/bestbuy"><strong>Best Buy</strong></a></td><td><code>bestbuy_product</code></td><td>Product</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/e-commerce/etsy"><strong>Etsy</strong></a></td><td><code>etsy</code>,<br><code>etsy_product</code></td><td>Product</td></tr><tr><td><a href="https://developers.oxylabs.io/api-targets/e-commerce/target"><strong>Target</strong></a></td><td><code>target</code>,<br><code>target_search</code>,<br><code>target_product</code></td><td>Search<br>Product</td></tr><tr><td>Homedepot</td><td><code>universal</code></td><td>Product</td></tr><tr><td>Backmarket</td><td><code>universal</code></td><td>Product</td></tr></tbody></table>

{% hint style="success" %}
If you want to get parsed data from other targets, please use [**Custom Parser**](/products/web-scraper-api/features/custom-parser.md)**.**
{% endhint %}


---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation by asking a question.

Perform an HTTP GET request on the following URL with the `ask` and `goal` query parameters:

```
GET https://developers.oxylabs.io/products/web-scraper-api/features/result-processing-and-storage/dedicated-parsers.md?ask=<question>&goal=<user_goal>
```

`ask` is the immediate question: it should be specific, self-contained, and written in natural language.
`goal` is what the user is ultimately trying to achieve, the reason they need the answer. Sharing it helps GitBook give you a better, more relevant answer. A goal is most helpful when it describes the outcome the user wants rather than restating the question. For example, with `ask=how do I create an API token`, a goal like `automate deployments from our CI pipeline` lets GitBook tailor the answer to that use case.

The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
