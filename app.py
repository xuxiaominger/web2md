"""
Web2MD Remote Controller - Flask Web App
部署到 Render
"""

from flask import Flask, render_template_string, request, jsonify
import os
import sys

app = Flask(__name__)

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Obsidian路径 - Render环境变量
OBSIDIAN_PATH = os.environ.get('OBSIDIAN_PATH', '/Users/xuxiaoming/Documents/我的笔记本/2025年10月2日至')

# HTML界面
HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Web2MD 远程控制</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 16px;
        }
        .container { max-width: 600px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 20px; font-size: 24px; }
        .card {
            background: white; border-radius: 16px; padding: 20px;
            margin-bottom: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .search-box { display: flex; gap: 8px; }
        input { flex: 1; padding: 14px; border: 2px solid #ddd; border-radius: 12px; font-size: 16px; outline: none; }
        input:focus { border-color: #667eea; }
        .btn {
            padding: 14px 24px; background: #e74c3c; color: white;
            border: none; border-radius: 12px; font-size: 16px; font-weight: bold;
            cursor: pointer; white-space: nowrap;
        }
        .btn:active { transform: scale(0.98); }
        .btn:disabled { background: #95a5a6; }
        .results { max-height: 60vh; overflow-y: auto; }
        .result-item { padding: 12px; border-bottom: 1px solid #eee; cursor: pointer; }
        .result-item:active { background: #f5f5f5; }
        .result-item .title { font-weight: bold; color: #333; margin-bottom: 4px; }
        .result-item .url { color: #666; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .result-item .status { font-size: 12px; margin-top: 4px; }
        .result-item .status.saved { color: #27ae60; }
        .result-item .status.saving { color: #f39c12; }
        .status-bar { text-align: center; color: white; padding: 12px; font-size: 14px; }
        .info { background: rgba(255,255,255,0.2); border-radius: 8px; padding: 12px; margin-bottom: 16px; color: white; font-size: 14px; text-align: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Web2MD 远程控制</h1>

        <div class="info">
            💾 保存位置: Obsidian<br>
            📍 {{obsidian_path}}
        </div>

        <div class="card">
            <div class="search-box">
                <input type="text" id="kw" placeholder="输入搜索关键词..." onkeypress="if(event.key==='Enter')search()">
                <button class="btn" id="searchBtn" onclick="search()">🔍 搜索</button>
            </div>
        </div>

        <div class="card results" id="results">
            <p style="color:#666;text-align:center;">输入关键词搜索，最多显示50个结果</p>
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
        document.getElementById('results').innerHTML = '<p style="text-align:center;color:#666;">搜索中...</p>';

        try {
            const r = await fetch('/api/search?q=' + encodeURIComponent(kw));
            const data = await r.json();
            results = data.results || [];
            showResults();
            document.getElementById('status').textContent = '找到 ' + results.length + ' 个结果，点击提取';
        } catch(e) {
            document.getElementById('status').textContent = '搜索失败: ' + e.message;
        }

        document.getElementById('searchBtn').disabled = false;
    }

    function showResults() {
        const container = document.getElementById('results');
        if(results.length === 0) {
            container.innerHTML = '<p style="color:#666;text-align:center;">未找到结果</p>';
            return;
        }
        container.innerHTML = results.map((r,i) =>
            '<div class="result-item" onclick="extract('+i+')"><div class="title">'+r.title+'</div><div class="url">'+r.url+'</div><div class="status" id="s'+i+'">点击提取保存到Obsidian</div></div>'
        ).join('');
    }

    async function extract(i) {
        const r = results[i];
        const statusEl = document.getElementById('s'+i);

        statusEl.textContent = '正在提取...';
        statusEl.className = 'status saving';
        document.getElementById('status').textContent = '正在提取: ' + r.title;

        try {
            const resp = await fetch('/api/extract', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: r.url})
            });
            const data = await resp.json();

            if(data.success) {
                statusEl.textContent = '✅ 已保存到Obsidian';
                statusEl.className = 'status saved';
                document.getElementById('status').textContent = '保存成功: ' + r.title;
            } else {
                statusEl.textContent = '❌ ' + (data.error || '提取失败');
                statusEl.className = 'status';
            }
        } catch(e) {
            statusEl.textContent = '❌ ' + e.message;
        }
    }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML, obsidian_path=OBSIDIAN_PATH)

@app.route('/api/search')
def api_search():
    """搜索API"""
    from webclipper.searcher import search as do_search
    q = request.args.get('q', '')
    if not q:
        return jsonify({'results': [], 'error': '请输入关键词'})

    try:
        results = do_search(q, limit=50)
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'results': [], 'error': str(e)})

@app.route('/api/extract', methods=['POST'])
def api_extract():
    """提取API"""
    data = request.get_json()
    url = data.get('url', '')

    if not url:
        return jsonify({'success': False, 'error': '需要URL'})

    try:
        from webclipper.crawler import crawl_url
        result = crawl_url(url, OBSIDIAN_PATH)

        if 'error' in result:
            return jsonify({'success': False, 'error': result.get('error')})

        return jsonify({
            'success': True,
            'title': result.get('title'),
            'saved': result.get('saved_path')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
