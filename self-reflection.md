---
name: self-reflection
description: 自主学习闭环 — 任务完成后主动反思、生成技能、追踪效果、持续改进（核心机制）
version: 2.0.0
platforms: [windows, linux, darwin]
author: hermes-inspired
created: 2026-04-13
updated: 2026-04-13
tags: [learning, reflection, skill-creation, self-improvement]
---

# 自主学习闭环

Hermes Agent 核心机制：任务完成后自动触发反思，生成可执行技能，追踪使用效果，持续改进。

## 何时使用

每次完成以下类型的任务后自动触发：
- 复杂技术调研（新框架、新工具）
- 完整项目构建（DCS系统、前端应用）
- 反复出现的同类问题（第三次遇到同类型任务时）
- 用户明确要求"记住这个"
- **技能被调用后** → 记录使用效果

---

## 标准流程

### 第一步：反思触发（任务完成时）
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
写入 `skills/反思-TASK-NAME.md`，格式见 SKILL.md 模板。

### 第四步：记录到使用追踪
```json
skills/usage-log.json
{
  "skills": {
    "skill-name": {
      "created": "2026-04-13",
      "lastUsed": "2026-04-13",
      "useCount": 1,
      "effectiveness": "good",  // good / mixed / poor
      "lastResult": "成功，Docker Compose 启动正常",
      "notes": []
    }
  }
}
```

### 第五步：技能调用后反馈
```
技能使用完毕后，自动记录：
- useCount++
- lastUsed 更新
- lastResult 本次结果
- effectiveness 根据结果更新
```

---

## 效果评判标准

| 效果 | 评判 | 操作 |
|------|------|------|
| **good** | 全部步骤正常，成功完成 | effectiveness = good，notes 加"强化" |
| **mixed** | 部分步骤有问题，需要调整 | effectiveness = mixed，附上修正说明 |
| **poor** | 完全失败，方法不对 | effectiveness = poor，考虑删除或重写 |

---

## 持续改进机制

### 技能使用后评估（每次调用后执行）
```
效果好 → 在技能文件末尾加一条"强化笔记"
效果差 → 在技能文件中修正问题步骤
完全失败 → 删除技能，标记"不适用"
```

### 定期检查（每次 heartbeat）
```
检查 skills/usage-log.json：
- 超过30天未使用的技能 → 标记为"可能过时"
- effectiveness = poor 超过2次 → 删除技能
- 发现相似技能超过3个 → 合并
```

---

## 推送机制

技能学到后，自动推送到：
- `workspace-taizi`
- 其他 agent workspace

---

## 验证方法

技能库使用率持续提升，mixed/poor 技能及时被修正或删除
