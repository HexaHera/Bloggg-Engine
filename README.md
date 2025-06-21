# Personal Blog Search Engine

A custom search engine that surfaces deep-dive personal blogs and insightful articles, filtering out generic SEO-filled corporate content.

## Project Overview

This search engine is designed to find authentic personal blogs and articles that often get buried under corporate SEO content in traditional search engines.

### Key Features

- **Personal Blog Detection**: ML-powered classification to identify authentic personal blogs
- **Cost-Optimized ML**: Uses efficient models like Gemma-2B for classification
- **Hierarchical Classification**: Domain analysis with fallback to header/footer analysis
- **Web Crawling**: Automated collection of blog articles
- **Search Interface**: Clean web interface for users

### Project Structure

```
Engine/
├── search_engine/     # Core search functionality
├── classifier/        # ML classification models
├── crawler/          # Web crawling components
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
- [ ] Web crawler implementation
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

## Team

This project is developed to focusing on AI/ML cost optimization and efficient web crawling. 