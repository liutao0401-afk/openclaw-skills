---
name: capacity-manager
description: MEMORY.md 容量管理系统 — 严格限制记忆文件大小，避免上下文膨胀
version: 1.0.0
platforms: [windows, linux, darwin]
author: hermes-inspired
created: 2026-04-13
tags: [memory, capacity, management]
---

# MEMORY.md 容量管理系统

Hermes 风格：严格容量限制，逼迫 Agent 只保留最有价值的信息。

## 容量限制

| 文件 | 硬限制 | 软限制（警告） | 保留优先级 |
|------|---------|---------------|-----------|
| `MEMORY.md` | 3000 chars | 2500 chars | 精选记忆 > 例行条目 |
| `USER.md` | 1500 chars | 1200 chars | 用户偏好 > 身份信息 |

## 何时触发检查

- 每次 heartbeat 时
- 写入新内容前
- 每日第一次写入记忆时

## 容量检查流程

### 第一步：检查当前大小
```bash
# 检查字符数
# PowerShell:
$content = Get-Content MEMORY.md -Raw -Encoding UTF8
$length = $content.Length
Write-Output "MEMORY.md: $length / 3000 chars"

$userContent = Get-Content USER.md -Raw -Encoding UTF8
$userLength = $userContent.Length
Write-Output "USER.md: $userLength / 1500 chars"
```

### 第二步：判断状态
```
OK (绿色):     < 软限制，不操作
警告 (黄色):  >= 软限制，开始合并
危险 (红色):   >= 硬限制，立即压缩
```

### 第三步：压缩策略（按优先级保留）

**MEMORY.md 保留优先级：**
1. ⭐⭐⭐ 用户核心信息（姓名、时区、偏好）
2. ⭐⭐⭐ GitHub 项目地址（不可找回）
3. ⭐⭐ 重要决策和教训
4. ⭐ 系统配置（可能需要重建）
5. ~~例行事件记录~~（删除或极简化）
6. ~~重复内容~~（合并）

**删除顺序：**
- 时间戳过期的待处理事项
- 重复的描述
- 过于详细的步骤（只保留结论）
- 一次性事件（除非有重要教训）

### 第四步：执行压缩
```
压缩动作：
1. 合并相似条目
2. 删除过期/不重要内容
3. 保留最精华的 3000 chars
4. 在文件顶部标记：[容量已压缩 YYYY-MM-DD]
```

## 容量检查自动化

在 HEARTBEAT.md 中加入检查：

```markdown
### 容量检查（每次 heartbeat）
检查 MEMORY.md 和 USER.md 字符数：
- 超过软限制 → 立即合并
- 超过硬限制 → 强制压缩
```

## 压缩模板

```markdown
# MEMORY.md — 长期记忆

> ⚠️ 容量已压缩 2026-04-13（硬限制: 3000 chars）

## 核心信息（优先保留）
- 用户：hh / liutao0401-afk / GMT+7
- 系统：Windows x64, Node.js v22.17.0, Python 3.12+

## GitHub 项目
| 项目 | 地址 |
|------|------|
| openclaw-skills | github.com/liutao0401-afk/openclaw-skills |
| dcs-jx300xp-collector | github.com/liutao0401-afk/dcs-jx300xp-collector |

## 重要教训（只保留精华）
1. ClawPanel 每次启动重置 gateway token → 已从注册表移除
2. GBK 编码问题 → Python 加 sys.stdout.reconfigure(encoding='utf-8')
3. GitHub push 需要 HTTPS + Token，不能用 SSH（无 SSH key）

## 当前技能库
skills/: self-reflection, dcs-opc-collector, github-deploy, windows-cleanup

## 系统状态
- Gateway: ws://127.0.0.1:18789, auth=none
- ClawPanel: 已卸载自启动
```

## 验证方法

```bash
# 验证容量
$content = Get-Content MEMORY.md -Raw -Encoding UTF8
$content.Length  # 应 < 3000
```

## 与 Hermes 的差异

| 功能 | Hermes | OpenClaw |
|------|--------|----------|
| MEMORY.md 限制 | 2200 chars | 3000 chars |
| USER.md 限制 | 1375 chars | 1500 chars |
| 自动压缩 | 是 | 半自动（每次 heartbeat 检查） |
| 容量提醒 | 百分比显示 | 软/硬限制两级 |

## 触发时机

1. **HEARTBEAT.md** — 每次心跳检查
2. **写入前检查** — 写入新内容前先检查
3. **每日检查** — 每日首次写入记忆时
