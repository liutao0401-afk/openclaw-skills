# OpenClaw Skills by @liutao0401-afk

参考 Claude Code 泄漏源码，为 OpenClaw 设计的增强技能包。

## 技能包

### 🌙 Dream Mode
记忆整合引擎 — 当 Agent 闲置时自动整理分散的记忆碎片。
**标签:** memory, automation, idle, consolidation

### 🤖 KAIROS
自主运行守护进程 — 集 Cron 调度 + GitHub Webhook 于一体。
**标签:** automation, cron, webhook, github, daemon

### 🐾 Buddy System
ASCII 宠物陪伴 — 12 种宠物、5 级稀有度、心情互动。
**标签:** fun, companion, pets, ascii, mood

### 🛠 Toolset Expansion
扩展工具集 — Grep/Glob/TodoWrite-TodoRead/Rank。
**标签:** tools, grep, glob, todo, rank, search

### 😊 Mood Detection
心情检测 — Regex 匹配用户情绪，自动调整响应策略。
**标签:** mood, emotion, ux, sentiment

### 🚩 Feature Flags
功能开关系统 — 控制功能灰度发布，支持多状态管理。
**标签:** feature-flags, system, configuration

---

## 发布方式

使用 [ClawHub CLI](https://clawhub.ai) 安装：

```bash
# 安装单个技能
openclaw skills add https://github.com/liutao0401-afk/openclaw-skills/tree/main/dream-mode
openclaw skills add https://github.com/liutao0401-afk/openclaw-skills/tree/main/kairos
openclaw skills add https://github.com/liutao0401-afk/openclaw-skills/tree/main/buddy-system
openclaw skills add https://github.com/liutao0401-afk/openclaw-skills/tree/main/toolset-expansion
openclaw skills add https://github.com/liutao0401-afk/openclaw-skills/tree/main/mood-detection
openclaw skills add https://github.com/liutao0401-afk/openclaw-skills/tree/main/feature-flags
```

## 设计参考

- Claude Code v2.1.50 System Prompt
- Claude Code 泄漏源码分析（512,000+ 行 TypeScript）
- Dream Mode / KAIROS / Buddy System / ULTRAPLAN / Mood Detection

## 作者

GitHub: [@liutao0401-afk](https://github.com/liutao0401-afk)
