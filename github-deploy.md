---
name: github-deploy
description: GitHub 仓库创建 + 代码推送完整流程
version: 1.0.0
platforms: [windows, linux, darwin]
author: auto-learned
created: 2026-04-11
tags: [github, git, deploy]
---

# GitHub 仓库部署

## 何时使用

- 用户要求把项目推送到 GitHub
- 本地已有代码，需要创建新仓库

## 标准流程

### 前提条件
```
需要 GitHub Personal Access Token（需要 repo 权限）
Token 格式：ghp_xxxxxxxxxxxx
```

### 第一步：初始化仓库
```bash
cd 项目目录
git init
git config user.email "liutao0401@gmail.com"
git config user.name "liutao0401-afk"
```

### 第二步：关联远程仓库
```bash
# 方式A：已有仓库
git remote add origin https://TOKEN@github.com/liutao0401-afk/REPO_NAME.git

# 方式B：通过 API 创建仓库
curl -X POST https://api.github.com/user/repos \
  -H "Authorization: token TOKEN" \
  -d '{"name":"REPO_NAME","description":"描述","private":false}'
```

### 第三步：提交代码
```bash
git add .
git commit -F commit_message.txt   # 用文件避免引号转义问题
git branch -M main
git push -u origin main
```

### 第四步：验证
```bash
curl https://api.github.com/repos/liutao0401-afk/REPO_NAME/contents
```

## 常见问题

### Repository not found
→ Token 无效 或 仓库未创建

### 推送失败 but no error
→ 检查 `git remote -v` 确认 URL 包含 token

### 没有 SSH key
→ 用 HTTPS + Token 方式，Git 全局配置不要设置 SSH rewrites

## 验证方法

仓库页面能正常访问，文件列表完整

## 使用反馈
```json
"effectiveness": "",  // good / mixed / poor
"lastResult": "",
"notes": []
