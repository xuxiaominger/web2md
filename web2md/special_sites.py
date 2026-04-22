"""
特殊网站处理模块
自动识别并使用定制规则处理微信公众号、知乎、Medium等特殊网站
"""

import re
import time
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse, parse_qs

# Selenium设为可选
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

try:
    from webdriver_manager.chrome import ChromeDriverManager
    WEBDRIVER_MANAGER_AVAILABLE = True
except ImportError:
    WEBDRIVER_MANAGER_AVAILABLE = False

import requests
from bs4 import BeautifulSoup


class SpecialSiteHandler:
    """特殊网站处理器"""

    # 特殊网站配置
    SPECIAL_SITES = {
        'weixin.qq.com': {
            'name': '微信公众号',
            'method': 'wechat',
            'need_js': True
        },
        'zhihu.com': {
            'name': '知乎',
            'method': 'zhihu',
            'need_js': True
        },
        'medium.com': {
            'name': 'Medium',
            'method': 'medium',
            'need_js': True
        },
        'm.weibo.cn': {
            'name': '微博',
            'method': 'weibo',
            'need_js': True
        },
        'weibo.com': {
            'name': '微博',
            'method': 'weibo',
            'need_js': True
        },
        'mp.weixin.qq.com': {
            'name': '微信公众号',
            'method': 'wechat',
            'need_js': True
        },
        'juejin.cn': {
            'name': '掘金',
            'method': 'juejin',
            'need_js': False
        },
        'juejin.im': {
            'name': '掘金',
            'method': 'juejin',
            'need_js': False
        },
        'csdn.net': {
            'name': 'CSDN',
            'method': 'csdn',
            'need_js': False
        },
        'segmentfault.com': {
            'name': 'SegmentFault',
            'method': 'segmentfault',
            'need_js': False
        },
        'stackoverflow.com': {
            'name': 'StackOverflow',
            'method': 'stackoverflow',
            'need_js': False
        },
        'github.com': {
            'name': 'GitHub',
            'method': 'github_readme',
            'need_js': False
        },
        'dev.to': {
            'name': 'Dev.to',
            'method': 'devto',
            'need_js': False
        },
        'cloud.tencent.com': {
            'name': '腾讯云',
            'method': 'tencent_cloud',
            'need_js': False
        },
        'aliyun.com': {
            'name': '阿里云',
            'method': 'aliyun',
            'need_js': False
        }
    }

    def __init__(self):
        self.driver = None

    def identify_site(self, url: str) -> Tuple[Optional[str], Optional[Dict]]:
        """识别网站类型"""
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
        """根据配置提取网页内容"""
        method = config.get('method', 'generic')

        # 检查是否需要JS但Selenium不可用
        if config.get('need_js') and not SELENIUM_AVAILABLE:
            return {
                'title': config.get('name', '网页文章'),
                'content': f'该网站({config.get("name")})需要JavaScript渲染，当前Selenium不可用。\n\n请手动复制内容，或安装兼容版本的Selenium。\n\n原文链接: {url}',
                'url': url,
                'note': 'Selenium不可用'
            }

        if method == 'wechat':
            return self._extract_wechat(url)
        elif method == 'zhihu':
            return self._extract_zhihu(url)
        elif method == 'medium':
            return self._extract_medium(url)
        elif method == 'weibo':
            return self._extract_weibo(url)
        elif method == 'juejin':
            return self._extract_juejin(url)
        elif method == 'csdn':
            return self._extract_csdn(url)
        elif method == 'stackoverflow':
            return self._extract_stackoverflow(url)
        elif method == 'github_readme':
            return self._extract_github_readme(url)
        elif method == 'devto':
            return self._extract_devto(url)
        else:
            return {'title': '', 'content': '', 'error': '未支持的网站类型'}

    def _init_driver(self):
        """初始化Chrome驱动"""
        if not SELENIUM_AVAILABLE:
            return None

        if self.driver is None:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            options.add_argument('--disable-blink-features=AutomationControlled')

            try:
                if WEBDRIVER_MANAGER_AVAILABLE:
                    service = Service(ChromeDriverManager().install())
                    self.driver = webdriver.Chrome(service=service, options=options)
                    self.driver.set_page_load_timeout(30)
            except Exception as e:
                print(f"初始化Chrome驱动失败: {e}")
                self.driver = None

    def _extract_wechat(self, url: str) -> Dict[str, Any]:
        """提取微信公众号文章"""
        self._init_driver()

        if self.driver is None:
            return self._extract_wechat_simple(url)

        try:
            self.driver.get(url)
            time.sleep(3)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "activity-name"))
            )

            title_elem = self.driver.find_element(By.ID, "activity-name")
            title = title_elem.text.strip() if title_elem else ""

            author = ""
            try:
                author_elem = self.driver.find_element(By.ID, "js_author_name")
                author = author_elem.text.strip()
            except:
                pass

            publish_date = ""
            try:
                date_elem = self.driver.find_element(By.ID, "publish_date")
                publish_date = date_elem.text.strip()
            except:
                pass

            content_elem = self.driver.find_element(By.ID, "js_content")
            soup = BeautifulSoup(content_elem.get_attribute('innerHTML'), 'lxml')

            for tag in soup(['script', 'style', 'iframe', 'form']):
                tag.decompose()

            content = soup.get_text(separator='\n', strip=True)

            return {
                'title': title,
                'content': content,
                'author': author,
                'date': publish_date,
                'url': url
            }
        except Exception as e:
            return self._extract_wechat_simple(url)

    def _extract_wechat_simple(self, url: str) -> Dict[str, Any]:
        """简单方式提取微信公众号"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

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
            return {'title': '微信公众号文章', 'content': f'无法提取，请访问: {url}', 'url': url}

    def _extract_zhihu(self, url: str) -> Dict[str, Any]:
        """提取知乎文章"""
        self._init_driver()

        if self.driver is None:
            return self._extract_zhihu_simple(url)

        try:
            self.driver.get(url)
            time.sleep(3)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "Post-Title"))
            )

            title_elem = self.driver.find_element(By.CLASS_NAME, "Post-Title")
            title = title_elem.text.strip() if title_elem else ""

            author = ""
            try:
                author_elem = self.driver.find_element(By.CLASS_NAME, "AuthorInfo-name")
                author = author_elem.text.strip()
            except:
                pass

            content_elem = self.driver.find_element(By.CLASS_NAME, "Post-RichText")
            soup = BeautifulSoup(content_elem.get_attribute('innerHTML'), 'lxml')

            for tag in soup(['script', 'style', 'iframe', 'ad']):
                tag.decompose()

            content = soup.get_text(separator='\n', strip=True)

            return {'title': title, 'content': content, 'author': author, 'url': url}
        except:
            return self._extract_zhihu_simple(url)

    def _extract_zhihu_simple(self, url: str) -> Dict[str, Any]:
        """简单方式提取知乎"""
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
        """提取Medium文章"""
        self._init_driver()

        if self.driver is None:
            return {'title': 'Medium文章', 'content': f'Selenium不可用，请访问: {url}', 'url': url}

        try:
            self.driver.get(url)
            time.sleep(3)

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )

            title = ""
            try:
                title_elem = self.driver.find_element(By.TAG_NAME, "h1")
                title = title_elem.text.strip()
            except:
                pass

            content_elem = self.driver.find_element(By.TAG_NAME, "article")
            soup = BeautifulSoup(content_elem.get_attribute('innerHTML'), 'lxml')

            for tag in soup(['script', 'style', 'iframe']):
                tag.decompose()

            content = soup.get_text(separator='\n', strip=True)

            return {'title': title, 'content': content, 'url': url}
        except:
            return {'title': 'Medium文章', 'content': f'提取失败，请访问: {url}', 'url': url}

    def _extract_weibo(self, url: str) -> Dict[str, Any]:
        """提取微博内容"""
        self._init_driver()

        if self.driver is None:
            return {'title': '微博', 'content': f'Selenium不可用，请访问: {url}', 'url': url}

        try:
            self.driver.get(url)
            time.sleep(3)

            content = ""
            try:
                content_elem = self.driver.find_element(By.CLASS_NAME, "weibo-text")
                content = content_elem.text.strip()
            except:
                try:
                    content_elem = self.driver.find_element(By.CLASS_NAME, "WB_text")
                    content = content_elem.text.strip()
                except:
                    pass

            title = "微博内容"
            try:
                user_elem = self.driver.find_element(By.CLASS_NAME, "WB_name")
                title = user_elem.text.strip()
            except:
                pass

            return {'title': title, 'content': content, 'url': url}
        except:
            return {'title': '微博', 'content': f'提取失败: {url}', 'url': url}

    def _extract_juejin(self, url: str) -> Dict[str, Any]:
        """提取掘金文章"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            title = ""
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.text.strip()

            content_elem = soup.find('article') or soup.find(class_=re.compile(r'content|article'))
            if content_elem:
                for tag in content_elem(['script', 'style']):
                    tag.decompose()
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = "无法提取内容"

            return {'title': title, 'content': content, 'url': url}
        except Exception as e:
            return {'title': '掘金文章', 'content': f'提取失败: {str(e)}', 'url': url}

    def _extract_csdn(self, url: str) -> Dict[str, Any]:
        """提取CSDN文章"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            title = ""
            title_elem = soup.find('h1', class_='title-article')
            if not title_elem:
                title_elem = soup.find('title')
            if title_elem:
                title = title_elem.text.strip()

            content_elem = soup.find('div', id='article_content') or \
                          soup.find('div', class_='blog_content') or \
                          soup.find('article')

            if content_elem:
                for tag in content_elem(['script', 'style', 'iframe', 'ad']):
                    tag.decompose()
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = "无法提取内容"

            return {'title': title, 'content': content, 'url': url}
        except Exception as e:
            return {'title': 'CSDN文章', 'content': f'提取失败: {str(e)}', 'url': url}

    def _extract_stackoverflow(self, url: str) -> Dict[str, Any]:
        """提取StackOverflow内容"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            title = ""
            title_elem = soup.find('a', class_='question-hyperlink')
            if title_elem:
                title = title_elem.text.strip()

            question_elem = soup.find('div', class_='s-prose')
            if question_elem:
                for tag in question_elem(['script', 'style']):
                    tag.decompose()
                content = question_elem.get_text(separator='\n', strip=True)
            else:
                content = "无法提取内容"

            return {'title': title, 'content': content, 'url': url}
        except Exception as e:
            return {'title': 'StackOverflow', 'content': f'提取失败: {str(e)}', 'url': url}

    def _extract_github_readme(self, url: str) -> Dict[str, Any]:
        """提取GitHub README"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]

        if len(path_parts) >= 2:
            user, repo = path_parts[0], path_parts[1]
            for readme_name in ['README.md', 'README.rst', 'README', 'readme.md']:
                raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/main/{readme_name}"
                try:
                    response = requests.get(raw_url, timeout=10)
                    if response.status_code == 200:
                        return {
                            'title': f"{user}/{repo} README",
                            'content': response.text,
                            'url': url
                        }
                except:
                    pass

            for readme_name in ['README.md', 'README.rst', 'README']:
                raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/master/{readme_name}"
                try:
                    response = requests.get(raw_url, timeout=10)
                    if response.status_code == 200:
                        return {
                            'title': f"{user}/{repo} README",
                            'content': response.text,
                            'url': url
                        }
                except:
                    pass

        return {'title': 'GitHub仓库', 'content': f'无法自动提取README，请访问: {url}', 'url': url}

    def _extract_devto(self, url: str) -> Dict[str, Any]:
        """提取Dev.to文章"""
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            title = ""
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.text.strip()

            content_elem = soup.find('div', class_='crayons-article__body')
            if not content_elem:
                content_elem = soup.find('article')

            if content_elem:
                for tag in content_elem(['script', 'style']):
                    tag.decompose()
                content = content_elem.get_text(separator='\n', strip=True)
            else:
                content = "无法提取内容"

            return {'title': title, 'content': content, 'url': url}
        except Exception as e:
            return {'title': 'Dev.to文章', 'content': f'提取失败: {str(e)}', 'url': url}

    def close(self):
        """关闭浏览器驱动"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None


def detect_and_extract(url: str) -> Dict[str, Any]:
    """自动识别网站并提取内容"""
    handler = SpecialSiteHandler()
    try:
        site_name, config = handler.identify_site(url)

        if config:
            return handler.extract(url, config)
        else:
            return {'title': '', 'content': '', 'error': '未知网站类型'}
    finally:
        handler.close()
