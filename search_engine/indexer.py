import os
import json
import glob
from whoosh.index import create_in, open_dir
from whoosh.fields import Schema, TEXT, ID, DATETIME
from whoosh.qparser import QueryParser, MultifieldParser, OrGroup
from whoosh.scoring import BM25F
import datetime

# --- Configuration ---
CLASSIFIED_DIR = "data/classified"
INDEX_DIR = "indexdir"

class Indexer:
    """
    Handles building and searching a Whoosh index.
    """
    def __init__(self, index_dir=INDEX_DIR, classified_dir=CLASSIFIED_DIR):
        self.index_dir = index_dir
        self.classified_dir = classified_dir
        self.schema = Schema(
            url=ID(stored=True, unique=True),
            title=TEXT(stored=True, field_boost=2.0), # Boost title matches
            description=TEXT(stored=True),
            content=TEXT(stored=True), # Field for the full text content
            publication_date=DATETIME(stored=True)
        )
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
            # Create an empty index if it doesn't exist
            create_in(self.index_dir, self.schema)

    def build_index(self):
        """
        Builds a new search index from the classified .meta files.
        This will overwrite any existing index.
        """
        print(f"Building index in '{self.index_dir}' from files in '{self.classified_dir}'...")
        
        # Create a new index, overwriting the old one
        ix = create_in(self.index_dir, self.schema)
        writer = ix.writer()

        meta_files = glob.glob(os.path.join(self.classified_dir, "*.meta"))
        if not meta_files:
            print("Warning: No .meta files found to index.")
            writer.commit()
            return
        
        for meta_file in meta_files:
            try:
                with open(meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Parse the date string from the .meta file into a datetime object
                    # If the date is missing or invalid -> we'll store None
                    pub_date_str = data.get('publication_date')
                    pub_date_obj = None
                    if pub_date_str:
                        pub_date_obj = datetime.datetime.fromisoformat(pub_date_str)

                    writer.add_document(
                        url=data.get('url', ''),
                        title=data.get('title', ''),
                        description=data.get('description', ''),
                        content=data.get('content', ''),
                        publication_date=pub_date_obj
                    )
            except Exception as e:
                print(f"Failed to process {meta_file}: {e}")

        writer.commit()
        print(f"Index built successfully with {len(meta_files)} documents.")

    def search(self, query_str: str, limit=20):
        """
        Searches the index for a given query string.
        """
        ix = open_dir(self.index_dir)
        
        # Use BM25F for scoring
        searcher = ix.searcher(weighting=BM25F)
        
        # Query parser that searches in title, description, and content
        qp = MultifieldParser(["title", "description", "content"], schema=ix.schema, group=OrGroup)
        q = qp.parse(query_str)
        
        results = searcher.search(q, limit=limit)
        
        # Add the publication_date to the results payload.
        # Format it as a simple "YYYY-MM-DD" string.
        # Use .get() for safety in case the field is missing from a document.
        return [
            {
                'url': hit['url'],
                'title': hit['title'],
                'description': hit.highlights("description") or hit['description'],
                'publication_date': hit.get('publication_date').strftime('%Y-%m-%d') if hit.get('publication_date') else None,
                'score': hit.score
            } 
            for hit in results
        ]

def main():
    """Command-line interface to build the index."""
    import argparse
    parser = argparse.ArgumentParser(description="Builds the search index.")
    parser.add_argument("--rebuild", action="store_true", help="Force a full rebuild of the search index.")
    
    args = parser.parse_args()

    indexer = Indexer()
    if args.rebuild:
        indexer.build_index()
    else:
        print("Indexer ready. Use --rebuild to build the index from scratch.")
        print(f"Example: python {__file__} --rebuild")


if __name__ == "__main__":
    main() 