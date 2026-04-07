---
name: mood-detection
description: 心情检测系统 — Regex 匹配用户情绪，自动调整响应策略。支持 frustrated/angry/confused/excited/sad 等 10 种情绪，根据心情自动选择合适的语气和回复风格。参考 Claude Code 的 Mood 检测机制设计。
tags: [mood, emotion, ux, sentiment, detection]
version: 1.0.0
author: liutao0401@gmail.com
license: MIT
homepage: https://github.com/liutao0401-afk/openclaw-skills
---

# Mood Detection — 心情检测系统

自动检测用户情绪，调整 Agent 响应风格。

## 支持的情绪

| 情绪 | 标识 | 触发关键词示例 |
|------|------|----------------|
| 😤 挫败 | frustrated | 怎么不行、不对、有问题 |
| 😠 愤怒 | angry | 垃圾、气死了 |
| 😕 困惑 | confused | 什么是、不明白、怎么用 |
| 🤩 兴奋 | excited | 太棒了、完美、厉害 |
| 😢 难过 | sad | 难过、伤心 |
| ⏰ 急躁 | impatient | 快点、赶紧 |
| 🤔 好奇 | curious | 为什么、原理 |
| 🙏 感谢 | grateful | 谢谢、多谢 |
| 😐 平静 | neutral | （默认） |

## 使用命令

```bash
# 检测心情
python3 scripts/mood_detection.py detect "这个bug怎么修都修不好"

# 生成响应
python3 scripts/mood_detection.py respond --mood frustrated

# 记录心情
python3 scripts/mood_detection.py log user123 "太好了！"

# 心情统计
python3 scripts/mood_detection.py stats --user user123
```

## Agent 集成

```python
from mood_detection import detect_mood, generate_response, log_mood

# 1. 检测用户心情
mood, config, matched = detect_mood(user_message)

# 2. 根据心情生成响应前缀
response_prefix = generate_response(mood, context=current_task)

# 3. 记录心情历史
log_mood(user_id, user_message, mood)
```

## 响应策略

| 心情 | 语气 | 策略 |
|------|------|------|
| frustrated | apologetic.supportive | 耐心排查，一步步来 |
| angry | calm.reassuring | 深呼吸，我来帮你 |
| confused | patient.explanatory | 一步步解释 |
| excited | enthusiastic | 肯定并继续 |
| impatient | efficient.direct | 马上搞定 |

## 设计参考

Claude Code 的心情检测通过 regex 匹配用户输入中的情绪关键词，
然后选择不同的响应策略。这是提升用户体验的简单但有效的方式。
