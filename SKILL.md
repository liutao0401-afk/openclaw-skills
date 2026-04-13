---
name: skill-template
description: 新技能创建模板 — 创建新技能时复制此文件
version: 1.0.0
platforms: [windows, linux, darwin]
author: auto-learned
created: 2026-04-13
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
每次技能使用后，在上方填写实际效果。effectiveness 变化时（如 mixed → good），在 notes 中说明原因。
