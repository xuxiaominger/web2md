"""
通用网页内容提取模块
使用多种方法提取网页正文内容
"""

import re
import time
from typing import Dict, Any, Optional, Tuple
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

# Selenium设为完全可选 - 延迟导入避免启动时崩溃
SELENIUM_AVAILABLE = False

from .special_sites import SpecialSiteHandler
from .markdown_formatter import MarkdownFormatter


class WebExtractor:
    """网页内容提取器"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        self.special_handler = SpecialSiteHandler()
        self.formatter = MarkdownFormatter()

    def extract(self, url: str) -> Dict[str, Any]:
        """
        提取网页内容

        Args:
            url: 网页URL

        Returns:
            提取的内容字典，包含 title, content, author, date, url 等字段
        """
        # 验证URL
        if not self._is_valid_url(url):
            return {'error': '无效的URL', 'title': '', 'content': '', 'url': url}

        # 首先检查是否是特殊网站
        site_name, config = self.special_handler.identify_site(url)
        if config:
            print(f"检测到特殊网站: {site_name}")
            return self.special_handler.extract(url, config)

        # 通用提取方法
        return self._generic_extract(url)

    def _is_valid_url(self, url: str) -> bool:
        """验证URL是否有效"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _generic_extract(self, url: str) -> Dict[str, Any]:
        """通用网页提取方法"""
        # 尝试多种方法提取

        # 方法1: 使用requests获取页面
        try:
            result = self._extract_with_requests(url)
            if result.get('content') and len(result.get('content', '')) > 100:
                return result
        except Exception as e:
            print(f"requests方法失败: {e}")

        # 方法2: 使用Selenium（如果可用）
        if SELENIUM_AVAILABLE:
            try:
                result = self._extract_with_selenium(url)
                if result.get('content') and len(result.get('content', '')) > 100:
                    return result
            except Exception as e:
                print(f"Selenium方法失败: {e}")

        # 方法3: 尝试trafilatura
        try:
            result = self._extract_with_trafilatura(url)
            if result.get('content'):
                return result
        except Exception as e:
            print(f"trafilatura方法失败: {e}")

        return {'error': '无法提取内容', 'title': '', 'content': '', 'url': url}

    def _extract_with_requests(self, url: str) -> Dict[str, Any]:
        """使用requests提取"""
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # 移除不需要的标签
        for tag in soup(['script', 'style', 'iframe', 'noscript', 'nav', 'footer', 'header']):
            tag.decompose()

        # 提取标题
        title = self._extract_title(soup)

        # 提取正文 - 尝试多种选择器
        content = self._extract_main_content(soup)

        return {
            'title': title,
            'content': content,
            'url': url
        }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        # 尝试多种方式

        # 1. og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()

        # 2. twitter:title
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            return twitter_title['content'].strip()

        # 3. h1标签
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)

        # 4. title标签
        title_tag = soup.find('title')
        if title_tag:
            # 清理标题，移除网站名称
            title = title_tag.get_text(strip=True)
            # 常见分隔符: - | _
            for sep in [' - ', ' | ', ' _ ']:
                if sep in title:
                    title = title.split(sep)[0]
                    break
            return title

        return ''

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """提取主要内容"""
        # 尝试常见的内容容器选择器
        selectors = [
            # 通用
            'article',
            'main',
            '[role="main"]',
            '.content',
            '.article-content',
            '.post-content',
            '.entry-content',
            '.article-body',
            '.story-body',
            # 中文网站常见
            '.text-content',
            '.article-text',
            '.content-text',
            '#article_content',
            '.blog_content',
            # 英文网站常见
            '.post-body',
            '.article__body',
            '.article-content',
            '.story-content',
            'entry-content'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator='\n', strip=True)
                if len(text) > 200:  # 内容足够长
                    return self._clean_text(text)

        # 回退：获取body中的所有段落
        body = soup.find('body')
        if body:
            # 获取所有段落和标题
            elements = body.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'])
            texts = []
            for elem in elements:
                text = elem.get_text(strip=True)
                if len(text) > 20:  # 过滤短文本
                    texts.append(text)

            if texts:
                return self._clean_text('\n\n'.join(texts))

        return ''

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        lines = text.split('\n')
        cleaned = []
        for line in lines:
            line = line.strip()
            if line:
                cleaned.append(line)

        return '\n\n'.join(cleaned)

    def _extract_with_selenium(self, url: str) -> Dict[str, Any]:
        """使用Selenium提取动态内容 - 运行时导入避免启动时崩溃"""
        if not SELENIUM_AVAILABLE:
            return {'error': 'Selenium不可用', 'url': url}

        # 运行时导入
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
        except Exception as e:
            return {'error': f'Selenium导入失败: {e}', 'url': url}

        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )

            try:
                driver.get(url)
                time.sleep(3)

                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )

                html = driver.page_source
                soup = BeautifulSoup(html, 'lxml')

                for tag in soup(['script', 'style', 'iframe', 'noscript', 'nav', 'footer', 'header']):
                    tag.decompose()

                title = self._extract_title(soup)
                content = self._extract_main_content(soup)

                return {'title': title, 'content': content, 'url': url}
            finally:
                driver.quit()
        except Exception as e:
            return {'error': f'Selenium执行失败: {e}', 'url': url}

    def _extract_with_trafilatura(self, url: str) -> Dict[str, Any]:
        """使用trafilatura库提取"""
        try:
            import trafilatura

            # 获取页面
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return {'error': '无法下载页面', 'url': url}

            # 提取正文
            result = trafilatura.extract(
                downloaded,
                output_format='markdown',
                include_tables=True,
                include_images=True,
                include_links=True
            )

            if result:
                # 尝试获取标题
                metadata = trafilatura.extract_metadata(downloaded)
                title = metadata.get('title', '') if metadata else ''

                return {
                    'title': title,
                    'content': result,
                    'url': url
                }
        except ImportError:
            pass

        return {'error': 'trafilatura不可用', 'url': url}

    def close(self):
        """关闭资源"""
        self.session.close()
        self.special_handler.close()


def extract_web_content(url: str) -> Dict[str, Any]:
    """
    便捷函数：提取网页内容

    Args:
        url: 网页URL

    Returns:
        提取的内容字典
    """
    extractor = WebExtractor()
    try:
        return extractor.extract(url)
    finally:
        extractor.close()
