---
name: skill-template
description: 新技能创建模板 — 创建新技能时复制此文件
version: 2.0.0
platforms: [windows, linux, darwin]
author: auto-learned
created: 2026-04-13
updated: 2026-04-13
tags: [template]
---

# 技能名称

简短描述：做这件事的标准流程

## 何时使用

触发条件：什么情况下应该调用这个技能

## 标准流程

1. 步骤一
2. 步骤二
3. 步骤三

## 注意事项

- 已知的坑和修复方法
- 依赖条件

## 验证方法

如何确认执行成功了

## 使用反馈（每次调用后更新）
```json
"effectiveness": "good",  // good / mixed / poor
"lastResult": "本次执行结果",
"notes": ["备注1", "备注2"]
```

---

## Cron 定时任务声明（可选）

如需定时自动执行，在 frontmatter 或下方声明：

```yaml
cron:
  schedule: "0 9 * * *"        # cron 表达式（每天9点）
  tz: "Asia/Bangkok"           # 时区（可选）
  description: "每天9点自动执行"  # 任务描述
  payload: |
    # 发送给 agent 的指令（多行）
    执行以下任务：
    1. 检查 DCS 数据采集状态
    2. 如有异常，发送告警
  skills: ["other-skill-name"]  # 挂载的技能（可选）
  enabled: true                  # 是否启用（可选，默认 true）
```

**Cron Expression 格式：**
```
┌───────────── 分钟 (0-59)
│ ┌─────────── 小时 (0-23)
│ │ ┌───────── 日 (1-31)
│ │ │ ┌─────── 月 (1-12)
│ │ │ │ ┌────── 星期 (0-6, 0=周日)
│ │ │ │ │
* * * * *
```

**常用示例：**
- `0 9 * * *` — 每天 9:00
- `*/30 * * * *` — 每 30 分钟
- `0 9,18 * * *` — 每天 9:00 和 18:00
- `0 */4 * * *` — 每 4 小时

## 技能自注册流程

当 Agent 加载技能时：
1. 检测 `cron:` 声明
2. 如 cron job 不存在 → 自动创建
3. 如 cron job 已存在 → 更新描述
4. 如 `enabled: false` → 删除已有 cron job

## 挂载技能到 Cron Job

cron job 运行时，会把 `payload` 作为消息发送给 agent，
并在消息中附带技能内容，让 agent 上下文包含技能执行能力。

当前限制：
- OpenClaw cron `agentTurn` 不直接挂载 skills 文件
- 需要在 `payload` 消息中内联技能内容
- 长期方案：等待 OpenClaw 支持 `skills:` 字段
