---
name: dream-mode
description: 三重门触发记忆整合 — 当 Agent 闲置时自动整理分散的记忆碎片，形成结构化知识。包含时间门、会话门、锁门三重检查，4阶段整合流程（收集→提炼→写入→归档），防止多进程冲突的 Advisory Lock，记忆按使用频率自动淘汰。
tags: [memory, automation, idle, consolidation]
version: 1.0.0
author: liutao0401@gmail.com
license: MIT
homepage: https://github.com/liutao0401
---

# Dream Mode — 记忆整合引擎

让 Agent 在闲置时自动整理记忆，模拟人类睡眠中的记忆巩固过程。

## 核心功能

- **三重门触发**：时间（24h）+ 会话（≥3）+ 锁门
- **4阶段整合**：收集 → 提炼 → 写入 → 归档
- **Advisory Lock**：防止多进程并发整合冲突
- **记忆分类**：longterm / lessons / decisions
- **自动淘汰**：低价值记忆按使用频率排序，超量自动裁剪

## 触发条件

```
⏰ 时间门：距上次整合 ≥ 24 小时
💬 会话门：新 session 数 ≥ 3
🔒 锁门：无其他进程占用
```

## 记忆文件位置

```
agent_memory/
├── memories/main/
│   ├── longterm.json   # 长期记忆条目
│   ├── lessons.json     # 学到的教训
│   └── decisions.json   # 关键决策
├── archive/             # 已归档 session
├── locks/             # advisory locks
└── dream_state.json   # 整合状态
```

## 使用命令

```bash
# 查看整合状态
python3 scripts/dream_mode.py status

# 检查触发条件
python3 scripts/dream_mode.py gates

# 手动触发整合
python3 scripts/dream_mode.py trigger --force

# 查看记忆内容
python3 scripts/dream_mode.py view --type lessons
python3 scripts/dream_mode.py view --type decisions

# 归档旧 session
python3 scripts/dream_mode.py archive --limit 10
```

## 整合流程说明

**Phase 1 收集**：扫描 session 目录，收集新 session 的摘要

**Phase 2 提炼**：从 session 中提取关键决策和教训（排除敏感内容）

**Phase 3 写入**：更新 longterm.json / lessons.json / decisions.json

**Phase 4 归档**：session 标记为已处理，释放空间

## 设计原则

- 记忆提炼时排除敏感内容（密码、密钥、个人隐私）
- 锁文件基于 mtime + PID，防止进程崩溃后锁残留
- 记忆条目按使用频率 + 时间排序，自动淘汰低价值条目
- 最多保留 200 条长期记忆、100 条教训、100 条决策

## 集成到心跳

在 HEARTBEAT.md 中加入检查：

```markdown
## 🌙 Dream Mode 检查（每次心跳都查）
python3 scripts/dream_mode.py gates
# 如果所有门都通过 → 触发整合：
python3 scripts/dream_mode.py trigger
```

## 依赖

- Python 3.9+
- OpenClaw Agent 工作目录

## 注意事项

- 仅在主 session 中加载长期记忆
- 不要在共享上下文（群聊）中暴露敏感记忆
- 建议配合 cron 定期检查 gates 状态
