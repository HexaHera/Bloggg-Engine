from flask import Flask, render_template, request, jsonify
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser, OrGroup
from whoosh.searching import Searcher
from datetime import datetime

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend', static_url_path='')

# Use Flask's application context to manage the searcher resource.
# This is a more robust way to handle resources in a web application.
def get_searcher():
    # This will create and cache the index object on the first request.
    if 'ix' not in app.config:
        print("Loading Whoosh index for the first time...")
        app.config['ix'] = open_dir("indexdir")
        print("Index loaded.")
    
    # A searcher should be opened for each request.
    return app.config['ix'].searcher()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query_str = request.args.get('q', '')
    if not query_str:
        return jsonify([])

    searcher = get_searcher()
    try:
        # Boost title matches to prioritize them in search results.
        parser = MultifieldParser(
            ["title", "content"], 
            schema=searcher.schema,
            group=OrGroup,
            fieldboosts={"title": 2.0}
        )
        query = parser.parse(query_str)
        
        search_results = searcher.search(query, limit=20)

        results = []
        for doc in search_results:
            publication_date = doc.get('publication_date')
            formatted_date = "N/A"
            if publication_date:
                try:
                    formatted_date = publication_date.strftime('%d-%m-%Y')
                except AttributeError:
                    formatted_date = "Invalid Date"
            
            # Generate a highlighted snippet. Fallback to description if no highlight.
            snippet = doc.highlights("content") or doc.get("description", "")

            results.append({
                "title": doc.get('title', 'No Title'),
                "url": doc['url'],
                "publication_date": formatted_date,
                "description": snippet
            })
        return jsonify(results)
    finally:
        # It's important to close the searcher after each request.
        searcher.close()


if __name__ == '__main__':
    print("Starting Personal Blog Search Engine server...")
    print("Server is running on http://127.0.0.1:8080")
    # Debug mode and reloader are both OFF for stability.
    app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False) 