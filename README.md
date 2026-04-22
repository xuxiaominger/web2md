# Web2MD - 网页转Markdown工具

将网页内容转换为格式良好的Markdown文件，自动同步到Obsidian笔记库。

## 功能特性

- 📄 支持任意网页内容提取
- 🔍 自动识别特殊网站（微信公众号、知乎、Medium、微博等）
- 📝 输出格式准确的Markdown
- 🖱️ 图形界面操作简便
- 🔄 自动同步到Obsidian
- 📁 文件名自动命名：网页标题 + 日期

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

1. 运行程序：
   ```bash
   python main.py
   ```

2. 复制任意网页链接到剪贴板
3. 程序自动读取链接并显示在输入框
4. 点击红色"转换"按钮
5. 自动生成Markdown并保存到Obsidian库

## 目录结构

```
web2md/
├── __init__.py
├── extractor.py         # 网页内容提取
├── special_sites.py     # 特殊网站处理
├── markdown_formatter.py # Markdown格式化
├── gui.py               # GUI界面
├── obsidian_sync.py     # Obsidian同步
└── github_sync.py       # GitHub同步
main.py                  # 入口文件
requirements.txt         # 依赖
```

## 依赖

- requests: HTTP请求
- beautifulsoup4: HTML解析
- lxml: XML/HTML解析器
- selenium: 动态网页渲染
- webdriver-manager: Chrome驱动管理
- tkinter: GUI界面（Python内置）
- PyGithub: GitHub API

## 许可证

MIT
