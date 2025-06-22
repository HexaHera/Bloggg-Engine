import asyncio
import aiohttp
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin, urlparse
from typing import List, Set
import redis.asyncio as redis
import json
import argparse

class Crawler:
    """
    An asynchronous, distributed web crawler using a Redis backend.

    This crawler pops URLs from a shared Redis queue, fetches their content,
    saves the HTML, and discovers new links on the same domain, adding them
    back to the queue. It's designed to be run concurrently across multiple
    processes or machines.
    """
    def __init__(self, output_dir: str, max_pages: int = 1000, concurrent_requests: int = 10):
        # Connect to Redis using the URL from the environment or a default.
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.queue_key = "crawler:queue"
        self.visited_key = "crawler:visited"
        
        self.output_dir = output_dir
        self.max_pages = max_pages
        self.concurrent_requests = concurrent_requests
        self.crawled_count = 0
        
        self.raw_pages_dir = os.path.join(self.output_dir, "raw_pages")
        os.makedirs(self.raw_pages_dir, exist_ok=True)
        print(f"Crawler instance initialized. Output will be saved to '{self.raw_pages_dir}'.")

    def _sanitize_filename(self, url: str) -> str:
        """Strips a URL down to a safe filename."""
        url = url.replace("https://", "").replace("http://", "").replace("www.", "")
        url = re.sub(r'[\\/*?:"<>|]', "_", url)
        return url[:150]

    async def _worker(self, session: aiohttp.ClientSession):
        """A worker task that processes URLs from the queue until the crawl limit is reached."""
        while self.crawled_count < self.max_pages:
            try:
                # Block until a URL is available in the queue, with a timeout.
                # The timeout prevents it from waiting forever and allows graceful shutdown.
                _ , url = await self.redis.brpop(self.queue_key, timeout=1)
                if url is None:
                    continue
            except asyncio.CancelledError:
                break # Exit if the task is cancelled.
            except Exception as e:
                print(f"Error reading from Redis queue: {e}")
                await asyncio.sleep(1)
                continue
            
            # Since multiple workers can run, we double-check if another worker
            # has already processed this URL in the time since it was popped.
            if await self.redis.sismember(self.visited_key, url):
                continue

            # Mark the URL as visited immediately to prevent re-crawling.
            await self.redis.sadd(self.visited_key, url)
            print(f"Processing: {url}")

            try:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    html = await response.text()
                    
                    self.save_page(url, html)
                    self.crawled_count += 1
                    
                    if self.crawled_count >= self.max_pages:
                        break

                    # Discover new links on the same page to add to the queue.
                    soup = BeautifulSoup(html, 'html.parser')
                    base_domain = urlparse(url).netloc
                    for a_tag in soup.find_all('a', href=True):
                        link = urljoin(url, a_tag['href'])
                        # For this project, we only care about links on the same domain.
                        if urlparse(link).netloc == base_domain:
                             # Add to queue only if we haven't seen it before.
                            if not await self.redis.sismember(self.visited_key, link):
                                await self.redis.lpush(self.queue_key, link)
            
            except Exception as e:
                print(f"Failed to process {url}: {e}")
            

    async def crawl(self):
        """Initializes and runs the crawler workers."""
        async with aiohttp.ClientSession() as session:
            workers = [asyncio.create_task(self._worker(session)) for _ in range(self.concurrent_requests)]
            
            # This loop keeps the main crawl function alive until the page limit is hit.
            # It also includes a check to exit early if the queue runs dry.
            while self.crawled_count < self.max_pages:
                await asyncio.sleep(1)
                queue_size = await self.redis.llen(self.queue_key)
                if queue_size == 0 and self.crawled_count > 0:
                    print("URL queue is empty, crawl is finishing early.")
                    break
            
            # Cleanly stop all worker tasks.
            for worker in workers:
                worker.cancel()
            
            await asyncio.gather(*workers, return_exceptions=True)
            visited_count = await self.redis.scard(self.visited_key)
            print(f"\nCrawl complete. Total unique pages visited: {visited_count}")

    def save_page(self, url: str, content: str):
        """Saves the HTML content and a .meta file with the original URL."""
        if not content:
            return
            
        filename_base = self._sanitize_filename(url)
        html_filepath = os.path.join(self.raw_pages_dir, f"{filename_base}.html")
        meta_filepath = os.path.join(self.raw_pages_dir, f"{filename_base}.meta")
        
        try:
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            # The .meta file is crucial for the classifier to know the page's original URL.
            with open(meta_filepath, 'w', encoding='utf-8') as f:
                json.dump({"url": url}, f, indent=4)

        except IOError as e:
            print(f"Error saving file for URL {url}: {e}")

async def seed_redis(redis_client, seeds_file: str):
    """Adds a list of starting URLs to the crawl queue."""
    queue_key = "crawler:queue"
    visited_key = "crawler:visited"
    
    with open(seeds_file, 'r') as f:
        start_urls = [line.strip() for line in f if line.strip()]

    print(f"Found {len(start_urls)} URLs in '{seeds_file}'. Adding new ones to the queue...")
    new_urls_count = 0
    for url in start_urls:
        # We use SISMEMBER to avoid adding a URL if it's already been crawled.
        if not await redis_client.sismember(visited_key, url):
            await redis_client.lpush(queue_key, url)
            new_urls_count += 1
    print(f"Added {new_urls_count} new URLs to the queue. Seeding complete.")


def main():
    # This main block allows the crawler to be run as a standalone script.
    # To scale up, you can execute this script on multiple machines, and they
    # will all coordinate through the central Redis instance.
    parser = argparse.ArgumentParser(description="A distributed web crawler.")
    parser.add_argument("--seeds_file", default="seeds.txt", help="Path to the file with seed URLs. Use 'none' to run as a pure worker.")
    parser.add_argument("--output_dir", default="data", help="Directory to save the crawled pages.")
    parser.add_argument("--max_pages", type=int, default=100, help="Maximum number of pages for this worker to crawl.")
    parser.add_argument("--concurrent_requests", type=int, default=10, help="Number of concurrent download requests for this worker.")
    
    args = parser.parse_args()

    async def run():
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
        redis_client = redis.from_url(redis_url, decode_responses=True)

        if args.seeds_file.lower() != 'none':
            await seed_redis(redis_client, args.seeds_file)

        crawler = Crawler(
            output_dir=args.output_dir,
            max_pages=args.max_pages,
            concurrent_requests=args.concurrent_requests
        )
        await crawler.crawl()
        await redis_client.close()

    asyncio.run(run())

if __name__ == "__main__":
    main() 