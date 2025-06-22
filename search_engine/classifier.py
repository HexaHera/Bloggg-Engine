import os
import glob
import json
import re
import hashlib
import argparse
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dateutil.parser import parse as parse_date

class GemmaClassifier:
    """
    Identifies which downloaded web pages are personal blogs or articles.

    This classifier uses a series of simple, fast heuristics to make its
    decision. It does not use any external AI models, making it cheap and
    reliable to run.
    """
    def __init__(self, raw_pages_dir: str, classified_data_dir: str):
        self.raw_pages_dir = raw_pages_dir
        self.classified_data_dir = classified_data_dir
        os.makedirs(self.classified_data_dir, exist_ok=True)

    def _extract_publication_date(self, soup):
        """
        Tries to find the publication date from various common HTML tags.
        """
        # List of tags and attributes to check, in order of preference.
        date_checks = [
            {'tag': 'meta', 'attrs': {'property': 'article:published_time'}},
            {'tag': 'meta', 'attrs': {'name': 'publication_date'}},
            {'tag': 'meta', 'attrs': {'name': 'dc.date'}},
            {'tag': 'time', 'attrs': {'datetime': True}},
        ]

        for check in date_checks:
            tag = soup.find(check['tag'], check['attrs'])
            if tag:
                date_str = tag.get('content') or tag.get('datetime')
                if date_str:
                    try:
                        return parse_date(date_str)
                    except (ValueError, TypeError):
                        continue
        
        # --- Heuristic 2: Search for common class names ---
        # Look for elements with class names that often contain dates.
        common_classes = ['date', 'published', 'post-date', 'entry-date', 'meta-date']
        for class_name in common_classes:
            # The "contains" selector (*) is useful for matching classes like 'entry-date updated'.
            tag = soup.find(lambda t: t.has_attr('class') and any(class_name in c for c in t['class']))
            if tag and tag.string:
                try:
                    # We pass fuzzy=True to handle cases where the date is surrounded by other text
                    # e.g., "Published on: January 1, 2024"
                    return parse_date(tag.string, fuzzy=True)
                except (ValueError, TypeError):
                    continue
        
        # --- Heuristic 3: Regex search for date-like patterns ---
        # This is a broader search for anything that looks like a date.
        try:
            # Matches patterns like "Month Day, Year" or "Day Month Year"
            date_regex = re.compile(r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}', re.IGNORECASE)
            text_to_search = ' '.join(soup.get_text().split()[:500]) # Search first ~500 words
            match = date_regex.search(text_to_search)
            if match:
                return parse_date(match.group(0))
        except (ValueError, TypeError):
            pass # Ignore parsing errors from the regex match

        return None

    def _extract_metadata(self, soup, url):
        """Pulls out the title, description, and date from the page's HTML."""
        title = soup.title.string if soup.title else ''

        description_tag = soup.find('meta', attrs={'name': 'description'})
        description = description_tag['content'] if description_tag and description_tag.get('content') else ''

        publication_date = self._extract_publication_date(soup)
        
        # Extract all text from the body, which is a good proxy for the main content
        content = soup.body.get_text(' ', strip=True) if soup.body else ''

        return {
            "url": url,
            "title": title.strip(),
            "description": description.strip(),
            "publication_date": publication_date.isoformat() if publication_date else None,
            "content": content
        }

    def classify_page(self, html_content: str, original_url: str):
        """
        Applies a series of heuristics to a page to determine if it's a blog/article.
        Returns extracted metadata if it is, otherwise returns None.
        """
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # --- Heuristic 1: Check for URL patterns common to blogs. ---
            # This is a cheap and effective first pass.
            if any(keyword in original_url for keyword in ['blog', '/post/', '/article/']):
                print(f"  -> Classified as blog (URL pattern): {original_url}")
                return self._extract_metadata(soup, original_url)

            # --- Heuristic 2: Look for footers from common blog platforms. ---
            # The presence of these strongly indicates a blog.
            text_content = soup.get_text().lower()
            if any(platform in text_content for platform in ['powered by wordpress', 'ghost.io', 'on substack', 'on medium', 'published with ghost']):
                print(f"  -> Classified as blog (Platform footer): {original_url}")
                return self._extract_metadata(soup, original_url)
            
            # --- Heuristic 3: Check for a comments section. ---
            # Most articles have a comments section, whereas corporate pages don't.
            if soup.find(id='comments') or soup.find(class_='comments-area'):
                print(f"  -> Classified as blog (Comments section): {original_url}")
                return self._extract_metadata(soup, original_url)

            # If none of the heuristics match, we assume it's not an article.
            return None
        except Exception as e:
            print(f"  -> Error classifying page {original_url}: {e}")
            return None

    def process_crawled_files(self):
        """
        Loops through all downloaded HTML files, runs the classifier on them,
        and saves the results for the ones that pass.
        """
        html_files = glob.glob(os.path.join(self.raw_pages_dir, '*.html'))
        print(f"Found {len(html_files)} downloaded pages to classify.")
        classified_count = 0

        for html_file_path in html_files:
            meta_file_path = html_file_path.replace('.html', '.meta')
            
            if not os.path.exists(meta_file_path):
                # This can happen if a crawl was interrupted. It's safe to just skip.
                continue

            try:
                with open(meta_file_path, 'r', encoding='utf-8') as f:
                    meta_data = json.load(f)
                    url = meta_data.get('url')
                    if not url:
                        continue
                
                with open(html_file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                classification_result = self.classify_page(html_content, url)
                
                if classification_result:
                    classified_count += 1
                    # We use a hash of the URL as the filename to avoid filesystem issues.
                    output_filename_base = hashlib.sha1(url.encode()).hexdigest()
                    output_meta_path = os.path.join(self.classified_data_dir, f"{output_filename_base}.meta")
                    
                    # Ensure the final data includes the publication date.
                    final_meta_data = {
                        'url': url,
                        'title': classification_result.get('title', 'No Title'),
                        'description': classification_result.get('description', ''),
                        'publication_date': classification_result.get('publication_date'),
                        'content': classification_result.get('content', '')
                    }
                    
                    with open(output_meta_path, 'w', encoding='utf-8') as f:
                        json.dump(final_meta_data, f, indent=4)

            except json.JSONDecodeError:
                # This can happen if a .meta file is corrupted or empty.
                continue
            except Exception as e:
                print(f"Error processing file {os.path.basename(html_file_path)}: {e}")
        
        print(f"Classification finished. Identified {classified_count} articles.")


if __name__ == "__main__":
    # This allows the classifier to be run as a standalone script on existing data.
    parser = argparse.ArgumentParser(description="Classify crawled web pages using heuristics.")
    parser.add_argument("--raw_pages_dir", default="data/raw_pages", help="Directory with raw HTML files.")
    parser.add_argument("--classified_data_dir", default="data/classified", help="Directory to save metadata for classified pages.")
    args = parser.parse_args()

    classifier = GemmaClassifier(args.raw_pages_dir, args.classified_data_dir)
    classifier.process_crawled_files() 