"""
网页爬虫模块
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 添加项目根目录到路径
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from web2md.extractor import WebExtractor
from web2md.obsidian_sync import ObsidianSync


def crawl_url(url: str, obsidian_path: str = None) -> Dict[str, Any]:
    """爬取单个URL"""
    print(f"正在爬取: {url}")

    try:
        # 创建提取器
        extractor = WebExtractor()
        result = extractor.extract(url)
        extractor.close()

        if 'error' in result and result.get('error'):
            print(f"爬取失败: {result.get('error')}")
            return result

        # 转换为Markdown
        markdown = _to_markdown(result)
        result['markdown'] = markdown

        # 保存到Obsidian
        if obsidian_path:
            try:
                obsidian = ObsidianSync(obsidian_path)
                filename = _generate_filename(result.get('title', 'untitled'))
                success, path = obsidian.save_markdown(filename, markdown)
                if success:
                    result['saved_path'] = path
                    print(f"已保存到: {path}")
                else:
                    print(f"保存失败: {path}")
            except Exception as e:
                print(f"保存到Obsidian失败: {e}")

        return result

    except Exception as e:
        print(f"爬取出错: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e), 'title': '', 'content': '', 'url': url}


def _to_markdown(result: Dict[str, Any]) -> str:
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


def _generate_filename(title: str) -> str:
    """生成文件名"""
    clean_title = ''.join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
    clean_title = clean_title.strip()[:50]
    clean_title = clean_title.replace(' ', '_')
    date = datetime.now().strftime('%Y%m%d')
    return f"{date}_{clean_title}.md"
