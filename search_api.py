from flask import Flask, request, jsonify, send_from_directory
from search_engine.indexer import Indexer
import os
import argparse

# Initialize the Flask app. 'static_folder' tells Flask where to find
# the HTML, CSS, and JS files for the frontend.
app = Flask(__name__, static_folder='frontend')

# Create a single, global instance of the Indexer.
# This opens the Whoosh index from the 'indexdir' and keeps it ready for searches.
indexer = Indexer()

# --- Static File Serving ---
# The following two routes are for serving the frontend files.

@app.route('/')
def serve_index():
    """Serves the main search page (index.html)."""
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serves any other static file (like CSS, JS, or images)."""
    return send_from_directory('frontend', filename)

# --- Search API Endpoint ---

@app.route('/search', methods=['POST'])
def search():
    """
    The main search endpoint. It takes a JSON request with a 'query',
    searches the index, and returns ranked results.
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        if not query:
            return jsonify({'error': 'Search query cannot be empty'}), 400

        results = indexer.search(query)
        return jsonify({'results': results})
        
    except Exception as e:
        # Basic error handling to catch any issues during the search process.
        print(f"Error during search: {e}")
        return jsonify({'error': 'An internal server error occurred'}), 500

@app.route('/health')
def health():
    """A simple health check endpoint to confirm the server is running."""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Starts the search engine's web server.")
    parser.add_argument("--port", type=int, default=5050, help="Port to run the server on.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the server to (use 0.0.0.0 to make it accessible on your network).")
    
    args = parser.parse_args()
    
    # Standard startup message.
    print("Starting Personal Blog Search Engine server...")
    print(f"Index loaded successfully from '{indexer.index_dir}'.")
    print(f"Server is running on http://{args.host}:{args.port}")
    print("Press CTRL+C to shut down.")
    
    app.run(debug=True, host=args.host, port=args.port) 