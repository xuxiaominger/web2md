"""
Web2MD Remote Controller - Simple Flask App
"""

from flask import Flask, render_template_string, request, jsonify
import os
import sys
import traceback

app = Flask(__name__)

# Add path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Obsidian path
OBSIDIAN_PATH = os.environ.get('OBSIDIAN_PATH', '/Users/xuxiaoming/Documents/我的笔记本/2025年10月2日至')

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
        .item .status.error { color: #e74c3c; }
        .status-bar { text-align: center; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Web2MD</h1>
        <div class="card">
            <div class="search-box">
                <input type="text" id="kw" placeholder="搜索关键词...">
                <button class="btn" onclick="doSearch()">搜索</button>
            </div>
        </div>
        <div class="card results" id="results"></div>
        <div class="status-bar" id="status"></div>
    </div>
    <script>
    let results = [];
    async function doSearch() {
        const kw = document.getElementById('kw').value.trim();
        if (!kw) return;
        document.getElementById('status').textContent = '搜索中...';
        try {
            const r = await fetch('/s?q=' + encodeURIComponent(kw));
            const d = await r.json();
            results = d.results || [];
            document.getElementById('results').innerHTML = results.map((r,i) =>
                '<div class="item" onclick="extract('+i+')"><div class="title">'+r.title+'</div><div class="url">'+r.url+'</div><div class="status" id="s'+i+'">点击保存</div></div>'
            ).join('');
            document.getElementById('status').textContent = '找到 ' + results.length + ' 个结果';
        } catch(e) {
            document.getElementById('status').textContent = '错误: ' + e.message;
        }
    }
    async function extract(i) {
        const r = results[i];
        const el = document.getElementById('s'+i);
        el.textContent = '保存中...';
        try {
            const resp = await fetch('/e', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({url:r.url})});
            const d = await resp.json();
            el.textContent = d.success ? '✅ 已保存' : '❌ ' + (d.error||'');
            el.className = d.success ? 'status done' : 'status error';
        } catch(e) {
            el.textContent = '❌ ' + e.message;
        }
    }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/s')
def search():
    """Search API"""
    q = request.args.get('q', '')
    if not q:
        return jsonify({'results': [], 'error': 'no keyword'})

    try:
        # Use requests directly
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse

        results = []
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(q)}"
        headers = {'User-Agent': 'Mozilla/5.0'}

        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, 'lxml')

        for item in soup.select('.result')[:50]:
            try:
                t = item.select_one('.result__title')
                if not t: continue
                title = t.get_text(strip=True)
                a = t.select_one('a')
                link = a.get('href', '') if a else ''
                if title and link:
                    results.append({'title': title[:200], 'url': link})
            except: continue

        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'results': [], 'error': str(e)})

@app.route('/e', methods=['POST'])
def extract():
    """Extract API"""
    try:
        data = request.get_json() or {}
        url = data.get('url', '')
        if not url:
            return jsonify({'success': False, 'error': 'no url'})

        # Import crawler
        from webclipper.crawler import crawl_url
        result = crawl_url(url, OBSIDIAN_PATH)

        if 'error' in result and result.get('error'):
            return jsonify({'success': False, 'error': result.get('error')})

        return jsonify({'success': True, 'title': result.get('title')})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
