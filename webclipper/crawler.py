"""
网页爬虫模块
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from web2md.extractor import WebExtractor
from web2md.obsidian_sync import ObsidianSync


class WebCrawler:
    """网页爬虫"""

    def __init__(self, obsidian_path: str = None):
        self.extractor = WebExtractor()
        self.obsidian_path = obsidian_path
        self.obsidian = None
        if obsidian_path:
            self.obsidian = ObsidianSync(obsidian_path)

    def crawl(self, url: str) -> Dict[str, Any]:
        """
        爬取单个URL

        Args:
            url: 网页URL

        Returns:
            爬取结果字典
        """
        print(f"正在爬取: {url}")
        result = self.extractor.extract(url)

        if 'error' in result and result['error']:
            print(f"爬取失败: {result['error']}")
            return result

        # 转换为Markdown
        markdown = self._to_markdown(result)
        result['markdown'] = markdown

        # 保存到Obsidian
        if self.obsidian:
            filename = self._generate_filename(result.get('title', 'untitled'))
            success, path = self.obsidian.save_markdown(filename, markdown)
            if success:
                result['saved_path'] = path
                print(f"已保存到: {path}")
            else:
                print(f"保存失败: {path}")

        return result

    def crawl_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        爬取多个URL

        Args:
            urls: URL列表

        Returns:
            爬取结果列表
        """
        results = []
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{len(urls)}] {url}")
            result = self.crawl(url)
            results.append(result)
        return results

    def _to_markdown(self, result: Dict[str, Any]) -> str:
        """转换为Markdown格式"""
        title = result.get('title', '未命名')
        content = result.get('content', '')
        url = result.get('url', '')

        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        markdown = f"""---
title: "{title}"
date: {date}
source: webclipper
url: {url}
tags: [webclipper]
---

# {title}

> **来源**: [{url}]({url})
> **爬取时间**: {date}

---

{content}

---

*由 WebClipper 自动爬取*
"""
        return markdown

    def _generate_filename(self, title: str) -> str:
        """生成文件名"""
        # 清理标题
        clean_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
        clean_title = clean_title.strip()[:50]
        clean_title = clean_title.replace(' ', '_')

        # 添加日期
        date = datetime.now().strftime('%Y%m%d')
        return f"{date}_{clean_title}.md"

    def close(self):
        """关闭资源"""
        if self.extractor:
            self.extractor.close()


def crawl_url(url: str, obsidian_path: str = None) -> Dict[str, Any]:
    """
    便捷函数：爬取单个URL

    Args:
        url: 网页URL
        obsidian_path: Obsidian库路径

    Returns:
        爬取结果
    """
    crawler = WebCrawler(obsidian_path)
    try:
        return crawler.crawl(url)
    finally:
        crawler.close()


def crawl_urls(urls: List[str], obsidian_path: str = None) -> List[Dict[str, Any]]:
    """
    便捷函数：爬取多个URL

    Args:
        urls: URL列表
        obsidian_path: Obsidian库路径

    Returns:
        爬取结果列表
    """
    crawler = WebCrawler(obsidian_path)
    try:
        return crawler.crawl_multiple(urls)
    finally:
        crawler.close()
