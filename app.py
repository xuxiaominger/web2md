"""
Web2MD Remote Controller - 简化版
"""

from flask import Flask, render_template_string, request, jsonify
import os
import sys
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

app = Flask(__name__)

# 添加路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Obsidian路径
OBSIDIAN_PATH = os.environ.get('OBSIDIAN_PATH', '/Users/xuxiaoming/Documents/我的笔记本/2025年10月2日至')

# HTML界面
HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web2MD</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); min-height: 100vh; padding: 16px; }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 16px; }
        .card { background: white; border-radius: 16px; padding: 16px; margin-bottom: 16px; }
        .search-box { display: flex; gap: 8px; }
        input { flex: 1; padding: 12px; border: 2px solid #ddd; border-radius: 8px; font-size: 16px; }
        .btn { padding: 12px 20px; background: #e74c3c; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; }
        .btn:disabled { background: #95a5a6; }
        .results { max-height: 50vh; overflow-y: auto; }
        .item { padding: 12px; border-bottom: 1px solid #eee; cursor: pointer; }
        .item .title { font-weight: bold; margin-bottom: 4px; }
        .item .url { color: #666; font-size: 12px; }
        .item .status { font-size: 12px; margin-top: 4px; color: #667eea; }
        .item .status.done { color: #27ae60; }
        .status-bar { text-align: center; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Web2MD</h1>
        <div class="card">
            <div class="search-box">
                <input type="text" id="kw" placeholder="输入搜索关键词..." onkeypress="if(event.key==='Enter')search()">
                <button class="btn" id="searchBtn" onclick="search()">搜索</button>
            </div>
        </div>
        <div class="card results" id="results">
            <p style="color:#666;text-align:center;">输入关键词搜索</p>
        </div>
        <div class="status-bar" id="status">等待操作...</div>
    </div>
    <script>
    let results = [];
    async function search() {
        const kw = document.getElementById('kw').value.trim();
        if(!kw) return;
        document.getElementById('searchBtn').disabled = true;
        document.getElementById('status').textContent = '搜索中...';
        document.getElementById('results').innerHTML = '<p style="text-align:center;">搜索中...</p>';
        try {
            const r = await fetch('/api/search?q=' + encodeURIComponent(kw));
            const data = await r.json();
            results = data.results || [];
            if(results.length === 0) {
                document.getElementById('results').innerHTML = '<p style="color:#666;text-align:center;">未找到结果</p>';
            } else {
                document.getElementById('results').innerHTML = results.map((r,i) =>
                    '<div class="item" onclick="extract('+i+')"><div class="title">'+r.title+'</div><div class="url">'+r.url+'</div><div class="status" id="s'+i+'">点击提取</div></div>'
                ).join('');
            }
            document.getElementById('status').textContent = '找到 ' + results.length + ' 个结果';
        } catch(e) {
            document.getElementById('status').textContent = '搜索失败: ' + e.message;
        }
        document.getElementById('searchBtn').disabled = false;
    }
    async function extract(i) {
        const r = results[i];
        const el = document.getElementById('s'+i);
        el.textContent = '提取中...';
        try {
            const resp = await fetch('/api/extract', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: r.url})
            });
            const data = await resp.json();
            el.textContent = data.success ? '✅ 已保存' : '❌ ' + (data.error || '失败');
            el.className = data.success ? 'status done' : 'status';
        } catch(e) {
            el.textContent = '❌ ' + e.message;
        }
    }
    </script>
</body>
</html>
'''

def do_search(keyword, limit=50):
    """执行搜索"""
    results = []

    # 使用 DuckDuckGo
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(keyword)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'lxml')

        for item in soup.select('.result')[:limit]:
            try:
                title_elem = item.select_one('.result__title')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                link_elem = title_elem.select_one('a')
                link = link_elem.get('href', '') if link_elem else ''

                if title and link:
                    results.append({
                        'title': title[:200],
                        'url': link
                    })
            except:
                continue
    except Exception as e:
        print(f"搜索失败: {e}")

    return results

def do_extract(url, obsidian_path):
    """执行提取"""
    try:
        # 导入提取器
        from web2md.extractor import WebExtractor
        from web2md.obsidian_sync import ObsidianSync
        from datetime import datetime

        # 提取内容
        extractor = WebExtractor()
        result = extractor.extract(url)
        extractor.close()

        if 'error' in result and result.get('error'):
            return {'success': False, 'error': result.get('error')}

        # 转换为Markdown
        title = result.get('title', '未命名')
        content = result.get('content', '')
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        markdown = f"""---
title: "{title}"
date: {date}
source: webclipper
url: {url}
---

# {title}

> 来源: {url}

{content}

---
*由 WebClipper 自动提取*
"""

        # 保存到Obsidian
        if obsidian_path:
            try:
                obsidian = ObsidianSync(obsidian_path)
                # 生成文件名
                clean_title = ''.join(c for c in title if c.isalnum() or c in ' -_')[:30]
                clean_title = clean_title.replace(' ', '_')
                filename = f"{datetime.now().strftime('%Y%m%d')}_{clean_title}.md"

                success, path = obsidian.save_markdown(filename, markdown)
                if success:
                    return {'success': True, 'title': title, 'saved': path}
            except Exception as e:
                print(f"保存失败: {e}")

        return {'success': True, 'title': title}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/search')
def api_search():
    q = request.args.get('q', '')
    if not q:
        return jsonify({'results': [], 'error': 'no keyword'})

    try:
        results = do_search(q, limit=50)
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'results': [], 'error': str(e)})

@app.route('/api/extract', methods=['POST'])
def api_extract():
    data = request.get_json() or {}
    url = data.get('url', '')

    if not url:
        return jsonify({'success': False, 'error': 'no url'})

    result = do_extract(url, OBSIDIAN_PATH)
    return jsonify(result)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
