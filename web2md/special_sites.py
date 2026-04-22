"""
特殊网站处理模块
自动识别并使用定制规则处理微信公众号、知乎、Medium等特殊网站
"""

import re
import time
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs

# Selenium设为完全可选 - 避免启动时崩溃
SELENIUM_AVAILABLE = False

import requests
from bs4 import BeautifulSoup


class SpecialSiteHandler:
    """特殊网站处理器"""

    # 特殊网站配置
    SPECIAL_SITES = {
        'weixin.qq.com': {'name': '微信公众号', 'method': 'wechat', 'need_js': True},
        'zhihu.com': {'name': '知乎', 'method': 'zhihu', 'need_js': True},
        'medium.com': {'name': 'Medium', 'method': 'medium', 'need_js': True},
        'm.weibo.cn': {'name': '微博', 'method': 'weibo', 'need_js': True},
        'weibo.com': {'name': '微博', 'method': 'weibo', 'need_js': True},
        'mp.weixin.qq.com': {'name': '微信公众号', 'method': 'wechat', 'need_js': True},
        'juejin.cn': {'name': '掘金', 'method': 'juejin', 'need_js': False},
        'juejin.im': {'name': '掘金', 'method': 'juejin', 'need_js': False},
        'csdn.net': {'name': 'CSDN', 'method': 'csdn', 'need_js': False},
        'segmentfault.com': {'name': 'SegmentFault', 'method': 'segmentfault', 'need_js': False},
        'stackoverflow.com': {'name': 'StackOverflow', 'method': 'stackoverflow', 'need_js': False},
        'github.com': {'name': 'GitHub', 'method': 'github_readme', 'need_js': False},
        'dev.to': {'name': 'Dev.to', 'method': 'devto', 'need_js': False},
    }

    def __init__(self):
        self.driver = None

    def identify_site(self, url: str) -> Tuple[Optional[str], Optional[Dict]]:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith('www.'):
            domain = domain[4:]

        if domain in self.SPECIAL_SITES:
            return self.SPECIAL_SITES[domain]['name'], self.SPECIAL_SITES[domain]

        for site_domain, config in self.SPECIAL_SITES.items():
            if site_domain in domain:
                return config['name'], config
        return None, None

    def extract(self, url: str, config: Dict) -> Dict[str, Any]:
        method = config.get('method', 'generic')

        if config.get('need_js') and not SELENIUM_AVAILABLE:
            return {
                'title': config.get('name', '网页文章'),
                'content': f'该网站({config.get("name")})需要JavaScript渲染，Selenium当前不可用。\n\n原文链接: {url}',
                'url': url
            }

        method_map = {
            'wechat': self._extract_wechat,
            'zhihu': self._extract_zhihu,
            'medium': self._extract_medium,
            'weibo': self._extract_weibo,
            'juejin': self._extract_juejin,
            'csdn': self._extract_csdn,
            'stackoverflow': self._extract_stackoverflow,
            'github_readme': self._extract_github_readme,
            'devto': self._extract_devto,
        }

        extractor = method_map.get(method)
        if extractor:
            return extractor(url)
        return {'title': '', 'content': '', 'error': '未支持的网站类型'}

    def _extract_wechat(self, url: str) -> Dict[str, Any]:
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'lxml')

            title = ""
            title_elem = soup.find('h2', class_='rich_media_title')
            if title_elem:
                title = title_elem.get_text(strip=True)

            content_elem = soup.find('div', class_='rich_media_content')
            if content_elem:
                for tag in content_elem(['script', 'style']):
                    tag.decompose()
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = f"请手动访问: {url}"

            return {'title': title, 'content': content, 'url': url}
        except:
            return {'title': '微信公众号文章', 'content': f'无法提取: {url}', 'url': url}

    def _extract_zhihu(self, url: str) -> Dict[str, Any]:
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'lxml')

            title = ""
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

            content_elem = soup.find('article') or soup.find(class_=re.compile(r'content|article'))
            if content_elem:
                for tag in content_elem(['script', 'style']):
                    tag.decompose()
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = f"请手动访问: {url}"

            return {'title': title, 'content': content, 'url': url}
        except:
            return {'title': '知乎文章', 'content': f'无法提取: {url}', 'url': url}

    def _extract_medium(self, url: str) -> Dict[str, Any]:
        return {'title': 'Medium文章', 'content': f'Selenium不可用，请访问: {url}', 'url': url}

    def _extract_weibo(self, url: str) -> Dict[str, Any]:
        return {'title': '微博', 'content': f'Selenium不可用，请访问: {url}', 'url': url}

    def _extract_juejin(self, url: str) -> Dict[str, Any]:
        return self._extract_generic(url, 'article')

    def _extract_csdn(self, url: str) -> Dict[str, Any]:
        return self._extract_generic(url, ['div#article_content', 'div.blog_content', 'article'])

    def _extract_stackoverflow(self, url: str) -> Dict[str, Any]:
        return self._extract_generic(url, 'div.s-prose')

    def _extract_devto(self, url: str) -> Dict[str, Any]:
        return self._extract_generic(url, ['div.crayons-article__body', 'article'])

    def _extract_generic(self, url: str, selectors) -> Dict[str, Any]:
        headers = {'User-Agent': 'Mozilla/5.0'}
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'lxml')

            title = ""
            title_elem = soup.find('h1')
            if not title_elem:
                title_elem = soup.find('title')
            if title_elem:
                title = title_elem.get_text(strip=True)

            if isinstance(selectors, list):
                content_elem = soup.select_one(selectors[0])
                for sel in selectors[1:]:
                    if not content_elem:
                        content_elem = soup.select_one(sel)
            else:
                content_elem = soup.select_one(selectors)

            if content_elem:
                for tag in content_elem(['script', 'style', 'iframe']):
                    tag.decompose()
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = "无法提取内容"

            return {'title': title, 'content': content, 'url': url}
        except Exception as e:
            return {'title': '文章', 'content': f'提取失败: {str(e)}', 'url': url}

    def _extract_github_readme(self, url: str) -> Dict[str, Any]:
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        if len(path_parts) >= 2:
            user, repo = path_parts[0], path_parts[1]
            for branch in ['main', 'master']:
                for readme in ['README.md', 'README.rst', 'readme.md']:
                    raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{readme}"
                    try:
                        response = requests.get(raw_url, timeout=10)
                        if response.status_code == 200:
                            return {'title': f"{user}/{repo} README", 'content': response.text, 'url': url}
                    except:
                        pass

        return {'title': 'GitHub仓库', 'content': f'无法提取README: {url}', 'url': url}

    def close(self):
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


def detect_and_extract(url: str) -> Dict[str, Any]:
    handler = SpecialSiteHandler()
    try:
        site_name, config = handler.identify_site(url)
        if config:
            return handler.extract(url, config)
        return {'title': '', 'content': '', 'error': '未知网站类型'}
    finally:
        handler.close()
