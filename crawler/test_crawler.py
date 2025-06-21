"""
Test file for Web Crawler Module
Simple tests to verify crawler functionality.
TODO: Add more comprehensive tests later
"""

from web_crawler import WebCrawler
from crawler_manager import CrawlerManager

def test_crawler_initialization():
    """Test if crawler initializes correctly."""
    print("Testing crawler initialization...")
    
    # Test basic initialization
    crawler = WebCrawler(delay=1.0, timeout=10)
    assert crawler.delay == 1.0, "Delay should be 1.0"
    assert crawler.timeout == 10, "Timeout should be 10"
    assert hasattr(crawler, 'session'), "Should have session attribute"
    assert hasattr(crawler, 'visited_urls'), "Should have visited_urls attribute"
    
    # Test with different parameters
    crawler2 = WebCrawler(delay=2.5, timeout=15)
    assert crawler2.delay == 2.5, "Delay should be 2.5"
    assert crawler2.timeout == 15, "Timeout should be 15"
    
    print("Crawler initialization test passed")

def test_crawler_manager_initialization():
    """Test if crawler manager initializes correctly."""
    print("Testing crawler manager initialization...")
    
    # Test basic initialization
    manager = CrawlerManager(max_workers=4, output_dir="data/crawled")
    assert manager.max_workers == 4, "Max workers should be 4"
    assert manager.output_dir == "data/crawled", "Output dir should be data/crawled"
    assert hasattr(manager, 'crawlers'), "Should have crawlers attribute"
    assert hasattr(manager, 'crawled_data'), "Should have crawled_data attribute"
    
    # Test with different parameters
    manager2 = CrawlerManager(max_workers=8, output_dir="test_data")
    assert manager2.max_workers == 8, "Max workers should be 8"
    assert manager2.output_dir == "test_data", "Output dir should be test_data"
    
    print("Crawler manager initialization test passed")

def test_crawler_methods_exist():
    """Test if all required methods exist in crawler."""
    print("Testing crawler methods...")
    
    crawler = WebCrawler()
    
    # Check if all required methods exist
    required_methods = [
        'crawl_url',
        'extract_blog_content', 
        'is_valid_blog_url',
        'save_content'
    ]
    
    for method in required_methods:
        assert hasattr(crawler, method), f"Should have {method} method"
    
    print("Crawler methods test passed")

def test_manager_methods_exist():
    """Test if all required methods exist in manager."""
    print("Testing manager methods...")
    
    manager = CrawlerManager()
    
    # Check if all required methods exist
    required_methods = [
        'add_crawler',
        'crawl_urls',
        'save_crawled_data',
        'load_crawled_data',
        'get_crawling_stats'
    ]
    
    for method in required_methods:
        assert hasattr(manager, method), f"Should have {method} method"
    
    print("Manager methods test passed")

if __name__ == "__main__":
    print("Running crawler tests...")
    print("=" * 50)
    
    try:
        test_crawler_initialization()
        test_crawler_manager_initialization()
        test_crawler_methods_exist()
        test_manager_methods_exist()
        
        print("=" * 50)
        print("All crawler tests passed!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        raise 