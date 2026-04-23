"""
WebClipper - 自动化网页爬取工具
"""

__version__ = "1.0.0"

from .crawler import WebCrawler, crawl_url, crawl_urls
from .searcher import search, get_search_engine
from .scheduler import TaskScheduler, get_scheduler
from .config import Config, get_config, init_config

__all__ = [
    'WebCrawler',
    'crawl_url',
    'crawl_urls',
    'search',
    'get_search_engine',
    'TaskScheduler',
    'get_scheduler',
    'Config',
    'get_config',
    'init_config',
]
