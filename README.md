# OpenClaw Skills — 技能库

> 基于 Hermes Agent 理念构建的自主学习闭环系统
> 自动从任务中学习，持续积累可复用技能

## 核心机制

```
任务完成 → 反思 → 判断是否技能化 → 写成 SKILL.md → 下次自动调用 → 持续改进
```

## 技能目录

| 技能 | 描述 | 状态 |
|------|------|------|
| `self-reflection.md` | 自主学习闭环（核心机制） | ✅ |
| `dcs-opc-collector.md` | 通用 DCS OPC UA 数据采集 | ✅ |
| `github-deploy.md` | GitHub 仓库创建 + 推送 | ✅ |
| `windows-cleanup.md` | Windows 自启动项彻底清理 | ✅ |
| `SKILL.md` | 技能创建模板 | ✅ |

## 技能格式

遵循 Hermes SKILL.md 标准格式：
```yaml
---
name: skill-name
description: 简短描述
version: 1.0.0
platforms: [windows, linux, darwin]
author: auto-learned
created: 2026-MM-DD
tags: [tag1, tag2]
---

# 技能名称

## 何时使用

## 标准流程

## 注意事项

## 验证方法
```

## 触发条件

以下情况自动触发学习流程：
1. 复杂任务（超过5步骤）完成
2. 用户说"记住这个"
3. 同类任务第三次出现
4. 调研新框架/新技术后

## 推送机制

学到新技能后，自动推送到：
- `workspace-taizi` — 钉钉 agent
- 其他配置好的 agent workspace

## 与 Hermes 的差异

| 功能 | Hermes | OpenClaw |
|------|--------|----------|
| 技能格式 | SKILL.md + YAML meta | 完全兼容 |
| 学习触发 | 自动 | 当前手动，未来自动 |
| 技能数量 | 40+ | 4（起步） |
| 跨Agent推送 | 支持 | 已实现 |
| 容量限制 | MEMORY 2200c | 当前无限制 |

## 扩展方向

- [ ] 增加更多技能（目标：20+）
- [ ] 实现自动反思触发（不需要用户说）
- [ ] 增加技能使用追踪
- [ ] 实现容量管理
- [ ] 对接 agentskills.io 标准
