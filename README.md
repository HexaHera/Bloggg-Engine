# Personal Blog Search Engine

A custom search engine that surfaces deep-dive personal blogs and insightful articles, filtering out generic SEO-filled corporate content.

## Project Overview

This search engine is designed to find authentic personal blogs and articles that often get buried under corporate SEO content in traditional search engines. The goal is to create a search experience that prioritizes personal, authentic content over heavily SEO-optimized corporate pages.

### Key Features

- **Personal Blog Detection**: ML-powered classification to identify authentic personal blogs
- **Cost-Optimized ML**: Uses efficient models like Gemma-2B for classification
- **Hierarchical Classification**: Domain analysis with fallback to header/footer analysis
- **Web Crawling**: Automated collection of blog articles with rate limiting
- **Search Interface**: Clean web interface for users
- **Concurrent Processing**: Multi-threaded crawling for better performance

### Project Structure

```
Engine/
├── search_engine/     # Core search functionality
├── classifier/        # ML classification models
├── crawler/          # Web crawling components
│   ├── web_crawler.py      # Main crawler class
│   ├── crawler_manager.py  # Crawler orchestration
│   └── test_crawler.py     # Crawler tests
├── data/             # Data storage and processing
│   ├── crawled/      # Crawled web content
│   └── index/        # Search index
├── frontend/         # Web interface
├── index/            # Main entry point
├── config.py         # Configuration settings
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation
```

## Development Progress

- [x] Project structure setup
- [x] Dependencies installation
- [x] Basic crawler skeleton (WebCrawler and CrawlerManager classes)
- [ ] URL fetching and HTML downloading implementation
- [ ] Content extraction and parsing
- [ ] ML classifier development
- [ ] Search engine core
- [ ] Frontend interface
- [ ] Integration and testing

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python index/main.py`

## Configuration

Edit `config.py` to customize:
- Crawler settings (delay, timeout, max pages)
- ML model parameters
- Search configuration
- Personal blog indicators

## Testing

Run the crawler tests to verify functionality:
```bash
cd crawler
python test_crawler.py
```

## Current Status

The project currently has a solid foundation with:
- Complete project structure
- All dependencies installed and configured
- Basic crawler skeleton with WebCrawler and CrawlerManager classes
- Comprehensive test suite for crawler functionality
- Configuration system for easy customization

Next steps involve implementing the actual crawling logic and content extraction.

## Team

This project is developed as part of a 1-4 member team focusing on AI/ML cost optimization and efficient web crawling. The development approach emphasizes incremental progress with regular commits to demonstrate the step-by-step building process. 