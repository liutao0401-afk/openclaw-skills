---
name: self-reflection
description: 自主学习闭环 — 任务完成后主动反思、生成技能、持续改进（核心机制）
version: 1.0.0
platforms: [windows, linux, darwin]
author: hermes-inspired
created: 2026-04-13
tags: [learning, reflection, skill-creation, self-improvement]
---

# 自主学习闭环

Hermes Agent 核心机制：任务完成后自动触发反思，生成可执行技能。

## 何时使用

每次完成以下类型的任务后自动触发：
- 复杂技术调研（新框架、新工具）
- 完整项目构建（DCS系统、前端应用）
- 反复出现的同类问题（第三次遇到同类型任务时）
- 用户明确要求"记住这个"

## 标准流程

### 第一步：反思触发（任务完成后自动执行）
```
问自己三个问题：
1. 这次有什么经验教训值得保留？
2. 这个任务未来可能重复吗？
3. 用户的偏好有什么新发现？
```

### 第二步：判断是否值得技能化
```
值得技能化的标准：
✓ 流程超过5个步骤
✓ 用户可能再次需要
✓ 有明确的可复用模板
✗ 纯一次性任务
✗ 用户明确说"不用记"
```

### 第三步：生成技能文件
```markdown
skills/反思-TASK-NAME.md

---
name: task-name
description: 简短描述
version: 1.0.0
platforms: [windows, linux, darwin]
author: auto-learned
created: 2026-MM-DD
tags: [xxx]
---

# 任务名称

## 何时使用
触发条件

## 标准流程
1. 步骤一
2. 步骤二

## 注意事项
已知的坑

## 验证方法
```

### 第四步：更新记忆
```
memory/YYYY-MM-DD.md

## 反思记录
- 任务：xxx
- 学到了：xxx
- 技能化：已写入 skills/xxx.md
```

### 第五步：推送至其他 Agent（可选）
```
当技能对其他 Agent 有价值时，推送到：
- taizi workspace: C:\Users\hh\.openclaw\workspace-taizi\skills\
- 其他 agent workspace
```

## 持续改进机制

### 技能使用后评估
```
效果好 → 在技能文件加一条"强化笔记"
效果差 → 修正技能文件中的步骤
完全失败 → 删除技能，标记为"不适用"
```

### 定期整合
```
每天heartbeat时：
- 检查 skills/ 目录
- 合并相似技能（超过3个相似 → 合并）
- 删除过时技能
```

## 技能优先级

| 等级 | 标准 | 示例 |
|------|------|------|
| P0 | 核心流程，每天用 | github-deploy |
| P1 | 重要技能，每周用 | dcs-opc-collector |
| P2 | 一般技能，偶尔用 | windows-cleanup |

## 验证方法

技能库持续增长，重复任务执行效率明显提升
