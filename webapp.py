#!/usr/bin/env python3
"""
Web2MD 网页应用
"""

from flask import Flask, render_template, request, jsonify
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from web2md.extractor import WebExtractor
from web2md.markdown_formatter import MarkdownFormatter

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/convert', methods=['POST'])
def convert():
    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({'error': '请输入URL'}), 400

    # 提取内容
    extractor = WebExtractor()
    try:
        content = extractor.extract(url)
    finally:
        extractor.close()

    if 'error' in content and content.get('content'):
        return jsonify({'error': content.get('error', '提取失败')}), 500

    # 转换为Markdown
    formatter = MarkdownFormatter()
    markdown = formatter.format(content)

    return jsonify({
        'title': content.get('title', ''),
        'markdown': markdown,
        'url': url
    })


if __name__ == '__main__':
    print("=" * 50)
    print("🌐 Web2MD 网页应用已启动")
    print("=" * 50)
    print("访问地址: http://localhost:5000")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
