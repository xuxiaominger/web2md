# Web2MD - 网页转Markdown工具

将网页内容转换为格式良好的Markdown文件。

## 🌐 在线网页版

**点击部署到 Render：**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://dashboard.render.com/select-repo?filter=my-repos&repoUrl=https://github.com/xuxiaominger/web2md)

部署步骤：
1. 点击上方按钮或访问 https://dashboard.render.com
2. 用 GitHub 登录
3. 选择 `web2md` 仓库
4. 设置：
   - Name: `web2md`
   - Region: `Oregon`
   - Branch: `main`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python webapp.py`
5. 点击 Deploy

## 本地运行

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

如需桌面应用：
```bash
python app.py
```

## GitHub

🔗 https://github.com/xuxiaominger/web2md

## 许可证

MIT
