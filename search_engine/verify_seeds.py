import asyncio
import aiohttp
import argparse
from typing import List

async def check_url(session: aiohttp.ClientSession, url: str) -> str | None:
    """
    Checks if a URL is live and returns it if it gets a 200 OK status.
    Returns None otherwise.
    """
    try:
        async with session.head(url, timeout=10, allow_redirects=True) as response:
            if response.status == 200:
                print(f"OK: {url}")
                return str(response.url) # Return the final URL after redirects
            else:
                print(f"FAILED ({response.status}): {url}")
                return None
    except Exception as e:
        print(f"ERROR: {url} ({e})")
        return None

async def verify_seeds(source_file: str, output_file: str):
    """
    Reads URLs from a source file, verifies them, and writes the good ones to an output file.
    """
    with open(source_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Verifying {len(urls)} URLs from '{source_file}'...")

    async with aiohttp.ClientSession() as session:
        tasks = [check_url(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    
    good_urls = [url for url in results if url]
    
    print(f"\nFound {len(good_urls)} live URLs.")

    with open(output_file, 'w') as f:
        for url in good_urls:
            f.write(f"{url}\n")
            
    print(f"Cleaned seed list saved to '{output_file}'.")


def main():
    parser = argparse.ArgumentParser(description="Verify a list of seed URLs to ensure they are live.")
    parser.add_argument("--source", default="seeds.txt", help="The source file containing seed URLs.")
    parser.add_argument("--output", default="seeds_cleaned.txt", help="The output file to save the cleaned list.")
    
    args = parser.parse_args()

    asyncio.run(verify_seeds(source_file=args.source, output_file=args.output))

if __name__ == "__main__":
    main() 