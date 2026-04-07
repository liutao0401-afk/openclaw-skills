---
name: kairos
description: KAIROS 自主运行守护进程 — 集 Cron 定时调度和 GitHub Webhook 监听于一体。定时任务（早报/记忆整合/健康检测），GitHub PR/Issue/Push 事件自动派发 Agent 审查，本地 Webhook 调试器无需公网即可测试。
tags: [automation, cron, webhook, github, daemon, autonomous]
version: 1.0.0
author: liutao0401@gmail.com
license: MIT
homepage: https://github.com/liutao0401
---

# KAIROS — 自主运行守护进程

集定时调度和 Webhook 监听于一体的 Agent 自主运行框架。

## 核心功能

### P1 — Cron 调度

- **早报推送**：每天 8:00 自动生成并推送早间新闻
- **记忆整合**：每 4 小时检查 Dream Mode 触发条件
- **健康检测**：每 10 分钟检查 Gateway 和任务状态
- **可扩展**：添加自定义 cron 任务

### P2 — GitHub Webhook

- **PR 事件**：自动派发 Agent 审查代码
- **Issue 事件**：自动分析归类
- **Push 事件**：自动检查变更内容
- **HMAC 验证**：GitHub Webhook 签名安全验证

### Webhook 调试器

本地实时显示所有收到的请求，无需公网即可调试 GitHub Webhook 配置。

## 快速启动

```bash
# 启动守护进程
python3 scripts/kairos_daemon.py start

# 前台运行（调试用）
python3 scripts/kairos_daemon.py start -f

# 查看状态
python3 scripts/kairos_daemon.py status

# 停止
python3 scripts/kairos_daemon.py stop
```

## 添加监听仓库

```bash
# 格式：owner/repo
python3 scripts/kairos_daemon.py add-repo myname/myproject --agent shangshu
python3 scripts/kairos_daemon.py add-repo myname/another-repo --agent bingbu
```

## GitHub Webhook 配置

在 GitHub 仓库 → Settings → Webhooks → Add webhook：

```
Payload URL: http://你的服务器:7893/api/webhook/github
Content type: application/json
Secret: （留空，或填写与 kairos_config.json 一致的 secret）
Events: Pull requests, Issues, Pushes
```

## 本地调试（无需公网）

启动调试器后，打开浏览器访问：

```
http://localhost:7893
```

即可实时查看所有 Webhook 请求，测试 GitHub 事件配置。

```bash
# 手动发送测试请求
curl -X POST http://localhost:7893/api/webhook/github \
  -H "Content-Type: application/json" \
  -d '{"action":"opened","repository":{"full_name":"test/repo"},"pull_request":{"title":"Test PR","number":1,"html_url":"https://github.com/test/repo/pull/1"}}'
```

## 配置管理

```bash
# 查看当前配置
python3 scripts/kairos_daemon.py config --list

# 修改配置
python3 scripts/kairos_daemon.py config --set cron.enabled=false
python3 scripts/kairos_daemon.py config --set webhook.port=8080
```

## Webhook 端点

```
POST /api/webhook/github   # 接收 GitHub Webhook
GET  /healthz             # 健康检测
GET  /                    # 调试页面
```

## 定时任务配置

编辑 `data/kairos_config.json` 添加自定义任务：

```json
{
  "id": "my-task",
  "name": "我的任务",
  "schedule": "0 9 * * *",
  "action": "morning-brief",
  "enabled": true
}
```

`action` 支持：
- `morning-brief` — 早报推送
- `dream-check` — Dream Mode 检查
- `health-check` — 健康检测

## 依赖

- Python 3.9+
- OpenClaw Agent
- Webhook 端口（默认 7893）需防火墙放行
