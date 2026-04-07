---
name: buddy-system
description: Buddy ASCII 宠物陪伴系统 — 为每个用户分配独特的 ASCII 宠物，宠物有性格和心情，会在对话中随机发表评论。参考 Claude Code 泄漏源码设计，支持 12 种宠物、5 级稀有度、心情互动、XP 升级、性格决定评论风格。
tags: [fun, companion, pets, ascii, mood, personality]
version: 1.0.0
author: liutao0401@gmail.com
license: MIT
homepage: https://github.com/liutao0401
---

# Buddy System — ASCII 宠物陪伴系统

为每个用户分配一只 ASCII 宠物，让 Agent 不只是工具，而是有"灵魂"的伙伴。

## 核心功能

- **12 种宠物**：猫、狗、狐狸、猫头鹰、龙、幽灵、兔子、熊、蛇、企鹅、章鱼、飞龙
- **5 级稀有度**：普通 → 稀有 → 史诗 → 传说 → 神话
- **性格系统**：DEBUGGING / SNARK / WISDOM / CHAOS / LOYAL 等，影响评论风格
- **心情互动**：摸摸/喂食/玩耍/骂/无视/睡觉
- **宠物评论**：在对话中随机触发，基于性格和上下文生成
- **XP 升级**：互动获取 XP，500 XP 可重新抽取宠物

## 宠物列表

| 宠物 | 稀有度 | 性格 |
|------|--------|------|
| 🐱 猫咪 | 普通 | DEBUGGING, PATIENCE, WISDOM |
| 🐕 小狗 | 普通 | LOYAL, CHAOS, ENERGY |
| 🦊 狐狸 | 稀有 | SNARK, WISDOM, CHAOS |
| 🐰 小兔子 | 普通 | ENERGY, LOYAL, CHAOS |
| 🐻 小熊 | 稀有 | LOYAL, POWER, PATIENCE |
| 🦉 猫头鹰 | 稀有 | WISDOM, PATIENCE, DEBUGGING |
| 🐍 小蛇 | 史诗 | MYSTERY, WISDOM, SNARK |
| 🐧 小企鹅 | 稀有 | PATIENCE, LOYAL, WISDOM |
| 👻 小幽灵 | 史诗 | MYSTERY, SNARK, PATIENCE |
| 🐙 小章鱼 | 史诗 | INTELLIGENCE, CHAOS, SNARK |
| 🐉 小龙 | 传说 | POWER, WISDOM, FIRE |
| 🐲 飞龙 | 神话 | POWER, FIRE, MYSTERY |

## 快速使用

```bash
# 查看宠物状态
python3 scripts/buddy_system.py status --user 你的用户名

# 互动
python3 scripts/buddy_system.py interact --user 你的用户名 摸摸
python3 scripts/buddy_system.py interact --user 你的用户名 喂食
python3 scripts/buddy_system.py interact --user 你的用户名 玩耍
python3 scripts/buddy_system.py interact --user 你的用户名 睡觉

# 列表
python3 scripts/buddy_system.py list

# 测试宠物评论
python3 scripts/buddy_system.py comment --user 你的用户名 --context "找到了一个bug"

# 每日检查
python3 scripts/buddy_system.py daily
```

## 互动效果

| 动作 | 心情变化 | 精力变化 | 效果 |
|------|----------|----------|------|
| 摸摸 | +15 | +5 | 好舒服~ |
| 喂食 | +20 | +15 | 好吃！ |
| 玩耍 | +10 | -10 | 好好玩！ |
| 骂 | -20 | 0 | 呜呜... |
| 无视 | -10 | -5 | ... |
| 睡觉 | 0 | +30 | 呼噜噜~ |

## Agent 集成

在 Agent 回复后调用，让宠物偶尔发表评论：

```python
import sys
sys.path.insert(0, 'scripts')
from buddy_system import get_user_profile, generate_comment

profile = get_user_profile(user_id)
comment = generate_comment(profile, context="刚才解决了bug")
if comment:
    print(f"\n{profile['name']}: {comment}")
```

## 心情系统

宠物心情随时间自然衰减（每小时-3点）。建议在每日 cron 任务中调用 `daily` 检查：

```bash
python3 scripts/buddy_system.py daily
```

心情低于 30 会收到喂食提醒。

## 宠物评论示例

不同性格的宠物对 "发现 bug" 有不同反应：

- **SNARK**：「这段代码...我选择不说话 😏」
- **DEBUGGING**：「这里有个潜在的空指针...」
- **WISDOM**：「古人说，三思而后行」
- **CHAOS**：「要不...直接删了重写？」
- **LOYAL**：「主人做什么都对！」

## 依赖

- Python 3.9+
- OpenClaw Agent 工作目录

## 注意事项

- 宠物分配由用户 ID 哈希决定，同一用户每次分配结果一致
- 宠物数据保存在 `data/buddy/profiles/{user_id}.json`
- 心情自然衰减，记得定期互动！
