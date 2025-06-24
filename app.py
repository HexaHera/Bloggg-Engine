import os
import json
import glob
from flask import Flask, render_template, request, jsonify
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.qparser import MultifieldParser, OrGroup
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

# --- Global In-Memory Index ---
ix = None

def build_in_memory_index():
    """
    Builds the entire search index from raw files and holds it in memory.
    This combines the logic of the classifier and indexer into one step.
    """
    global ix
    print("--- Building search index in memory ---")

    schema = Schema(
        url=ID(stored=True, unique=True),
        title=TEXT(stored=True, field_boost=2.0),
        content=TEXT(stored=True),
        publication_date=DATETIME(stored=True)
    )
    
    # Ensure the directory for the index exists
    index_dir = "inmemory_index"
    if not os.path.exists(index_dir):
        os.makedirs(index_dir)

    ix = create_in(index_dir, schema) # Create an in-memory index
    writer = ix.writer()

    html_files = glob.glob(os.path.join("data/raw_pages", '*.html'))
    if not html_files:
        print("!!! No HTML files found in data/raw_pages !!!")
        writer.commit()
        return

    for html_file_path in html_files:
        meta_file_path = html_file_path.replace('.html', '.meta')
        if not os.path.exists(meta_file_path):
            continue

        try:
            with open(meta_file_path, 'r', encoding='utf-8') as f:
                base_url = json.load(f).get('url')
            with open(html_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, 'lxml')

            # --- Classification & Extraction Logic ---
            if not soup.title or not soup.title.string:
                continue # Skip pages without a title

            title = soup.title.string.strip()

            # Fix canonical URL
            canonical_tag = soup.find('link', {'rel': 'canonical'})
            final_url = urljoin(base_url, canonical_tag['href']) if canonical_tag and canonical_tag.get('href') else base_url

            # Get content
            content = soup.body.get_text(' ', strip=True) if soup.body else ''

            # Get date
            date_tag = soup.find('meta', property='article:published_time')
            pub_date = None
            if date_tag and date_tag.get('content'):
                try:
                    pub_date = datetime.fromisoformat(date_tag['content'])
                except ValueError:
                    pub_date = None # Ignore invalid date formats

            writer.add_document(
                url=final_url,
                title=title,
                content=content,
                publication_date=pub_date
            )
        except Exception as e:
            print(f"Skipping file {os.path.basename(html_file_path)} due to error: {e}")
            continue

    writer.commit()
    print(f"--- Index build complete. {ix.doc_count()} documents indexed. ---")


# --- Flask Application ---
app = Flask(__name__, template_folder='frontend', static_folder='frontend', static_url_path='')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query_str = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 10))
    if not ix or not query_str:
        return jsonify({"results": [], "count": 0})

    with ix.searcher() as searcher:
        parser = MultifieldParser(
            ["title", "content"],
            schema=ix.schema,
            group=OrGroup
        )
        query = parser.parse(query_str)
        search_results = searcher.search(query, limit=100)

        # --- Re-ranking: Boost exact/near-exact title matches ---
        def normalize(s):
            return ''.join(s.lower().split())
        norm_query = normalize(query_str)
        ranked = []
        for hit in search_results:
            title = hit.get('title', '')
            norm_title = normalize(title)
            score = hit.score
            # Exact or very close match gets a huge boost
            if norm_query == norm_title or norm_query in norm_title or norm_title in norm_query:
                score += 1000
            ranked.append((score, hit))
        ranked.sort(key=lambda x: x[0], reverse=True)

        # Pagination
        total_count = len(ranked)
        start = (page - 1) * limit
        end = start + limit
        paged = ranked[start:end]

        results = []
        for _, hit in paged:
            pub_date = hit.get('publication_date')
            results.append({
                "title": hit.get('title', 'No Title'),
                "url": hit['url'],
                "publication_date": pub_date.strftime('%d-%m-%Y') if pub_date else "N/A",
                "description": hit.highlights("content") or ""
            })

        return jsonify({
            "results": results,
            "count": total_count,
            "page": page,
            "per_page": limit
        })


if __name__ == '__main__':
    build_in_memory_index()
    print("Starting Personal Blog Search Engine server...")
    print("Server is running on http://127.0.0.1:8080")
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False) 