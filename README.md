# Personal Blog & Article Search Engine

## Project Description

I built this search engine to solve a personal frustration: finding authentic, high-quality content on the internet has become increasingly difficult. Standard search engines often prioritize heavily SEO-optimized corporate websites over insightful personal blogs and articles. This project is my attempt to create a filter for the web, surfacing only the kind of deep-dive, authentic content I actually want to read.

The system works by crawling a list of seed URLs, discovering new pages, and then using a series of fast, offline heuristics to determine if a page is a personal blog or article. The classified content is then fully indexed and made available through a clean, simple web interface.

## Features

-   **Heuristic-Based Classification:** To keep costs at zero and ensure high speed, the engine avoids AI models. Instead, it uses a hierarchy of reliable rules (analyzing URL structure, checking for platform footers like 'Powered by Ghost', and looking for comment sections) to accurately identify personal blogs.
-   **Full-Text Search:** The search engine indexes the *entire text content* of every article, not just the title or meta description. This ensures that search results are highly relevant to the query.
-   **Intelligent Ranking:** Results are ranked using the industry-standard Okapi BM25F algorithm, which intelligently scores documents based on term frequency and document length. Title matches are given a boost to prioritize relevance.
-   **Scalable, Concurrent Crawling:** The architecture uses Redis as a message queue for URLs to be crawled. This allows multiple crawler processes to run concurrently—either on a single machine or distributed across several—dramatically speeding up the data collection process.
-   **Highlighted Snippets:** The search results page displays contextual snippets from the article body with the search terms highlighted, showing exactly why a result is relevant.
-   **Pagination and Result Count:** The search results page shows the total number of results and supports pagination, so you can easily browse through large result sets without being overwhelmed.

## Tech Stack

-   **Backend:** Python
-   **Web Framework:** Flask
-   **Search Indexing:** Whoosh
-   **Distributed Task Queue:** Redis
-   **HTML Parsing:** BeautifulSoup
-   **Frontend:** HTML, CSS, JavaScript

## Local Setup & Installation

Follow these steps to run the project on your local machine.

### 1. Prerequisites

-   Python 3.x
-   Redis Server

If you are on macOS, the easiest way to install Redis is with Homebrew:
`brew install redis`
`brew services start redis`

For other operating systems, please follow the official Redis installation guide.

### 2. Clone the Repository
`git clone https://github.com/your-username/your-repo-name.git`
`cd your-repo-name`


### 3. Install Dependencies
Install the required Python libraries using pip:
`pip install -r requirements.txt`

### 4. Run the Full Data Pipeline
This single command will run all the necessary steps: seeding the crawler, crawling pages, classifying the results, and building the search index.

1.  **Prepare Seeds:** Open the `seeds.txt` file and add the initial blog URLs you want to start crawling from (one URL per line).

2.  **Run the Pipeline:** Execute the main pipeline script. You can control how many pages to crawl with the `--max_pages` argument. For a quick first run, 100 pages is a good start.
    `python3 run_pipeline.py --max_pages 100`

    The script will print its progress for each stage.

### 5. Start the Server
Once the pipeline is complete, you can start the Flask web server to use the search engine.
`python3 search_api.py`

Open your web browser and navigate to **`http://127.0.0.1:5050`** to see the application.

## Demo

This project is designed to be run locally. Once the server is running, you can share it with others on your local network by using your machine's local IP address instead of `127.0.0.1`.

-   On macOS or Linux, find your IP with `ifconfig | grep "inet "`.
-   On Windows, use `ipconfig`.

The URL would look something like `http://192.168.1.10:5050`.

## Assumptions and Limitations

-   The search engine is designed to index only personal blogs and articles. Corporate, commercial, or heavily SEO-optimized sites are filtered out as much as possible using a set of heuristics.
-   Every page to be indexed must have a valid `.meta` file containing the canonical URL in JSON format. If a `.meta` file is missing or invalid, that page will be skipped during indexing.
-   The system assumes that Redis is running locally and accessible.
-   The project is intended for local or personal use, not for public deployment at scale.
-   Relative canonical URLs are resolved to absolute URLs during indexing to avoid duplicates or missed pages.
-   The search ranking logic is designed to prioritize results whose titles exactly or closely match the search query, so searching for a specific article title should bring that article to the top of the results.
-   Pagination is supported in the search results, and the total number of results is displayed to help with navigation. 