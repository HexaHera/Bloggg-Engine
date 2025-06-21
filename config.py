# Configuration file for Personal Blog Search Engine

# Flask Configuration
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True

# Crawler Configuration
CRAWLER_DELAY = 1  # Delay between requests in seconds
CRAWLER_TIMEOUT = 10  # Request timeout in seconds
CRAWLER_MAX_PAGES = 100  # Maximum pages to crawl per domain
CRAWLER_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

# ML Model Configuration
MODEL_NAME = "google/gemma-2b"  # Efficient model for classification
CLASSIFICATION_THRESHOLD = 0.7  # Confidence threshold for classification
MAX_SEQUENCE_LENGTH = 512  # Maximum text length for model input

# Search Configuration
SEARCH_RESULTS_LIMIT = 20  # Number of results to return
INDEX_PATH = "data/index"  # Path for search index
CRAWLED_DATA_PATH = "data/crawled"  # Path for crawled data

# Personal Blog Indicators
PERSONAL_BLOG_KEYWORDS = [
    'personal', 'blog', 'thoughts', 'experience', 'journey',
    'story', 'opinion', 'reflection', 'learning', 'insights'
]

CORPORATE_INDICATORS = [
    'company', 'corporate', 'business', 'enterprise', 'professional',
    'seo', 'marketing', 'agency', 'consulting', 'services'
] 