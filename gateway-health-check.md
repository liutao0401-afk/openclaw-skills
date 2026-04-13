---
name: gateway-health-check
description: Gateway 健康检查 + 自愈 — 每15分钟检查一次，连不上则自动重启
version: 1.0.0
platforms: [windows]
author: auto-learned
created: 2026-04-13
tags: [gateway, health, cron, self-heal]
cron:
  schedule: "*/15 * * * *"
  tz: "Asia/Bangkok"
  description: "每15分钟检查 Gateway 连通性，挂了则自动重启"
  enabled: true
---

# Gateway Health Check — 自动健康检查与自愈

## 检查流程

### 1. 连通性检查
```bash
curl -s --connect-timeout 3 http://127.0.0.1:18789/health || \
curl -s --connect-timeout 3 http://127.0.0.1:18789/api/status
```
**期望**：返回 200 + JSON

### 2. 如失败，尝试重启 Gateway
```bash
openclaw gateway restart
```

### 3. 等待 10 秒后再检查
```bash
sleep 10 && curl -s --connect-timeout 5 http://127.0.0.1:18789/health
```

### 4. 第三次检查仍失败 → 记录错误 + 告警
- 写入 `memory/gateway-errors.md`
- 发送钉钉告警（如果配置了）

## 状态判断

| 状态 | 条件 | 操作 |
|------|------|------|
| ✅ 健康 | /health 返回 200 | 结束 |
| ⚠️ 轻微问题 | 返回非200但有响应 | 记录日志 |
| 🔴 挂了 | 连接超时/拒绝 | 重启 |
| 🔴 重启后仍挂 | 重启后仍连不上 | 告警 + 记录 |

## 验证

```bash
curl http://127.0.0.1:18789/health
# 期望：{"status":"ok","uptime":...}
```

## 注意事项

- 只检查 loopback (127.0.0.1)，不检查 0.0.0.0
- 重启间隔 > 5分钟，防止频繁重启
- 连续3次失败才告警，避免抖动误报

## 使用反馈
```json
"effectiveness": "good"
"lastResult": "2026-04-13 08:32 首次注册"
"notes": []
```
