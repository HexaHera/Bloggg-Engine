from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import re
import glob

INDEX_DIR = os.environ.get('INDEX_DIR', 'index/')
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend'))
RAW_META_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data/raw_pages'))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)

def parse_meta_file(meta_path):
    blog = {}
    with open(meta_path, encoding='utf-8') as f:
        for line in f:
            if line.startswith('Title: '):
                blog['title'] = line[7:].strip()
            elif line.startswith('Snippet: '):
                blog['description'] = line[9:].strip()
            elif line.startswith('URL: '):
                blog['url'] = line[5:].strip()
    return blog

def score_blog(blog, query):
    score = 0
    query_lower = query.lower().strip()
    title = blog.get('title', '').lower()
    description = blog.get('description', '').lower()
    query_words = re.findall(r'\w+', query_lower)
    title_words = re.findall(r'\w+', title)
    # Strict: all query words present and same count as title words
    if query_words and set(query_words) == set(title_words) and len(query_words) == len(title_words):
        score += 20
    # All query words present in title (any order)
    elif query_words and all(word in title_words for word in query_words):
        score += 15
    # Exact phrase match
    if query_lower and query_lower in title:
        score += 10
    if query_lower and query_lower in description:
        score += 6
    # Per-word scores
    for word in query_words:
        if word in title:
            score += 3
        if word in description:
            score += 2
    return score

def rank_blogs(blog_list, query):
    for blog in blog_list:
        blog['score'] = score_blog(blog, query)
    return sorted(blog_list, key=lambda b: b['score'], reverse=True)

@app.route('/search')
def search():
    q = request.args.get('q', '')
    if not q:
        return jsonify({'error': 'Missing query'}), 400
    # Load all .meta files from raw_pages
    meta_files = glob.glob(os.path.join(RAW_META_DIR, '*.meta'))
    blogs = [parse_meta_file(meta) for meta in meta_files]
    ranked = rank_blogs(blogs, q)
    ranked = [b for b in ranked if b['score'] > 0]
    return jsonify(ranked)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Personal Blog Search Web App & API')
    parser.add_argument('--index-dir', type=str, default=INDEX_DIR, help='Index directory')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--port', type=int, default=5050, help='Port to run the server on')
    args = parser.parse_args()
    app.run(debug=True, host=args.host, port=args.port) 