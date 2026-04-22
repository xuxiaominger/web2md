#!/bin/bash
# Web2MD GitHub 部署脚本

echo "======================================"
echo "Web2MD - GitHub 部署"
echo "======================================"

# 检查是否已安装gh
if ! command -v gh &> /dev/null; then
    echo "错误: 未安装GitHub CLI (gh)"
    echo "请先安装: https://cli.github.com/"
    exit 1
fi

# 检查GitHub认证状态
echo ""
echo "检查GitHub认证状态..."
if ! gh auth status &> /dev/null; then
    echo "需要先登录GitHub!"
    echo ""
    echo "请运行以下命令进行认证:"
    echo "  gh auth login"
    echo ""
    echo "认证选项:"
    echo "  - GitHub.com: Yes"
    echo "  - HTTPS: Yes"
    echo "  - 登录GitHub: Login with a web browser"
    echo "  - Token: 输入你的Personal Access Token"
    echo ""
    echo "或直接运行: gh auth login"
    exit 1
fi

echo "✓ 已登录GitHub"

# 获取仓库名称
REPO_NAME=${1:-web2md}

echo ""
echo "创建GitHub仓库: $REPO_NAME"

# 创建仓库
gh repo create $REPO_NAME --public --source=. --description "Web2MD - 网页转Markdown工具" --clone=false

if [ $? -ne 0 ]; then
    echo "仓库可能已存在，尝试推送..."
fi

# 添加远程并推送
echo ""
echo "推送代码到GitHub..."

# 尝试main分支
git remote add origin https://github.com/$(gh api user --jq '.login')/$REPO_NAME.git 2>/dev/null || true

git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✓ 部署成功!"
    echo "仓库地址: https://github.com/$(gh api user --jq '.login')/$REPO_NAME"
    echo "======================================"
else
    echo ""
    echo "推送失败，请检查错误信息"
fi
