import os
import glob
from whoosh import index
from whoosh.fields import Schema, TEXT, ID
from whoosh.qparser import MultifieldParser
from bs4 import BeautifulSoup
from typing import List, Dict

CLASSIFIED_DIR = 'data/classified/'
INDEX_DIR = 'index/'
META_EXT = '.meta'
HTML_EXT = '.html'

schema = Schema(
    url=ID(stored=True, unique=True),
    title=TEXT(stored=True),
    snippet=TEXT(stored=True),
    content=TEXT
)

class IndexBuilder:
    def __init__(self, classified_dir: str = CLASSIFIED_DIR, index_dir: str = INDEX_DIR):
        self.classified_dir = classified_dir
        self.index_dir = index_dir
        self.schema = schema

    def build(self):
        if not os.path.exists(self.index_dir):
            os.makedirs(self.index_dir)
        if not index.exists_in(self.index_dir):
            ix = index.create_in(self.index_dir, self.schema)
        else:
            ix = index.open_dir(self.index_dir)
        writer = ix.writer()
        html_files = glob.glob(os.path.join(self.classified_dir, f'*{HTML_EXT}'))
        for html_path in html_files:
            meta_path = html_path.replace(HTML_EXT, META_EXT)
            if not os.path.exists(meta_path):
                continue
            with open(meta_path, encoding='utf-8') as f:
                meta = f.read()
            with open(html_path, encoding='utf-8') as f:
                html = f.read()
            url, title, snippet = '', '', ''
            for line in meta.splitlines():
                if line.startswith('URL: '):
                    url = line[5:].strip()
                elif line.startswith('Title: '):
                    title = line[7:].strip()
                elif line.startswith('Snippet: '):
                    snippet = line[8:].strip()
            content = BeautifulSoup(html, 'html.parser').get_text()
            writer.update_document(url=url, title=title, snippet=snippet, content=content)
        writer.commit()
        print('Index built.')

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        ix = index.open_dir(self.index_dir)
        with ix.searcher() as searcher:
            parser = MultifieldParser(["title", "snippet", "content"], schema=ix.schema)
            q = parser.parse(query)
            results = searcher.search(q, limit=limit)
            return [dict(r) for r in results]

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Personal Blog Index Builder & Search')
    parser.add_argument('--build', action='store_true', help='Build the index')
    parser.add_argument('--search', type=str, help='Search the index with a query')
    parser.add_argument('--classified-dir', type=str, default=CLASSIFIED_DIR, help='Classified directory')
    parser.add_argument('--index-dir', type=str, default=INDEX_DIR, help='Index directory')
    parser.add_argument('--limit', type=int, default=10, help='Search result limit')
    args = parser.parse_args()

    ib = IndexBuilder(classified_dir=args.classified_dir, index_dir=args.index_dir)
    if args.build:
        ib.build()
    if args.search:
        results = ib.search(args.search, limit=args.limit)
        for r in results:
            print(r) 