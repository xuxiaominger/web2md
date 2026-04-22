# Web2MD - 网页转Markdown工具

将网页内容转换为格式良好的Markdown文件。

## 🌐 在线网页版

**访问地址：https://web2md.onrender.com**

（首次打开可能需要几秒钟启动）

## 💻 本地运行

```bash
# 克隆仓库
git clone https://github.com/xuxiaominger/web2md.git
cd web2md

# 安装依赖
pip install -r requirements.txt

# 启动网页应用
python webapp.py

# 浏览器打开 http://localhost:5000
```

## 📱 网页版功能

- 🔍 输入框粘贴网页链接
- 🔴 点击红色按钮转换
- 📋 一键复制Markdown结果
- 📋 自动读取剪贴板

## 支持的网站

- 通用网页
- 微信公众号
- 知乎
- CSDN
- 掘金
- GitHub README
- StackOverflow
- Dev.to

## 本地GUI版本

如需桌面应用，请运行：
```bash
python app.py
```

## 技术栈

- Flask: 网页后端
- BeautifulSoup: HTML解析
- HTML2Text: Markdown转换
- tkinter: 桌面GUI

## GitHub

🔗 https://github.com/xuxiaominger/web2md

## 许可证

MIT
