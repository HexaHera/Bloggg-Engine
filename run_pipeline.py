import argparse
import asyncio
import os
import redis.asyncio as redis
from search_engine.crawler import Crawler, seed_redis
from search_engine.classifier import GemmaClassifier
from search_engine.indexer import Indexer

async def async_main():
    """Runs the three main stages of the search engine pipeline."""
    parser = argparse.ArgumentParser(description="Runs the full pipeline for the search engine.")
    parser.add_argument("--seeds_file", default="seeds.txt", help="Path to the file with seed URLs. Use 'none' to skip seeding and only run classification/indexing.")
    parser.add_argument("--max_pages", type=int, default=100, help="Maximum number of pages to crawl across all workers.")
    parser.add_argument("--concurrent_requests", type=int, default=10, help="Number of concurrent crawl requests per worker.")
    
    args = parser.parse_args()
    
    # --- Configuration ---
    CRAWL_OUTPUT_DIR = "data"
    CLASSIFIED_OUTPUT_DIR = "data/classified"
    INDEX_DIR = "indexdir"
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
    
    # --- Stage 1: Crawling ---
    # Asynchronously crawls web pages based on the seed URLs and saves the
    # raw HTML content. Uses Redis to coordinate work.
    print("--- Starting Stage 1: Crawling ---")
    redis_client = None
    try:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        if args.seeds_file.lower() != 'none':
            await seed_redis(redis_client, args.seeds_file)
        else:
            print("Skipping seeding. Assuming URLs are already in the queue.")

        crawler = Crawler(
            output_dir=CRAWL_OUTPUT_DIR,
            max_pages=args.max_pages,
            concurrent_requests=args.concurrent_requests
        )
        await crawler.crawl()
        
    except FileNotFoundError:
        print(f"ERROR: Seeds file not found at '{args.seeds_file}'. Please create it or specify another file.")
        return
    except Exception as e:
        print(f"An error occurred during the crawling stage: {e}")
        return
    finally:
        if redis_client:
            # Ensure the Redis connection is closed gracefully.
            await redis_client.close()
    print("--- Crawling Finished ---\n")

    # --- Stage 2: Classification ---
    # Iterates through the raw HTML files and classifies them, saving metadata
    # for pages that are identified as personal blogs or articles.
    print("--- Starting Stage 2: Classification ---")
    try:
        classifier = GemmaClassifier(
            raw_pages_dir=os.path.join(CRAWL_OUTPUT_DIR, "raw_pages"),
            classified_data_dir=CLASSIFIED_OUTPUT_DIR
        )
        classifier.process_crawled_files()
    except Exception as e:
        print(f"An error occurred during the classification stage: {e}")
        return
    print("--- Classification Finished ---\n")

    # --- Stage 3: Indexing ---
    # Takes the classified metadata and builds a searchable Whoosh index.
    print("--- Starting Stage 3: Indexing ---")
    try:
        indexer = Indexer(
            index_dir=INDEX_DIR, 
            classified_dir=CLASSIFIED_OUTPUT_DIR
        )
        indexer.build_index()
    except Exception as e:
        print(f"An error occurred during the indexing stage: {e}")
        return
    print("--- Indexing Finished ---\n")
        
    print("Pipeline completed successfully.")
    print("You can now start the web server by running: python search_api.py")


if __name__ == "__main__":
    # The main entry point for the script.
    asyncio.run(async_main()) 