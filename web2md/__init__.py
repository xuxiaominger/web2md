"""
Web2MD - 网页转Markdown工具
将网页内容转换为格式良好的Markdown文件
"""

__version__ = "1.0.0"
__author__ = "Web2MD Team"

from .extractor import WebExtractor
from .special_sites import SpecialSiteHandler
from .markdown_formatter import MarkdownFormatter
from .obsidian_sync import ObsidianSync

__all__ = [
    "WebExtractor",
    "SpecialSiteHandler",
    "MarkdownFormatter",
    "ObsidianSync"
]
