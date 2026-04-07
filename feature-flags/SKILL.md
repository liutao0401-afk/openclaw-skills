---
name: feature-flags
description: Feature Flags 功能开关系统 — 控制功能灰度发布，支持 enabled/testing/experimental/coming_soon/deprecated 等状态。内置 12 个默认标记（dream_mode/kairos/buddy_system 等），支持状态变更钩子，可扩展任意新功能。
tags: [feature-flags, system, configuration, flags, toggles]
version: 1.0.0
author: liutao0401@gmail.com
license: MIT
homepage: https://github.com/liutao0401-afk/openclaw-skills
---

# Feature Flags — 功能开关系统

控制功能的灰度发布，支持多状态管理。

## 内置功能标记

| 功能 | 状态 | 说明 |
|------|------|------|
| dream_mode | ✅ enabled | 记忆整合引擎 |
| kairos | ✅ enabled | 自主运行守护进程 |
| buddy_system | ✅ enabled | ASCII 宠物陪伴 |
| toolset | ✅ enabled | 扩展工具集 |
| mood_detection | ✅ enabled | 心情检测 |
| feature_flags_system | ✅ enabled | 本系统 |
| repl_mode | 🚧 coming_soon | REPL 交互模式 |
| voice_mode | 🔬 experimental | 语音模式 |
| undercover_mode | 🔬 experimental | 隐身模式 |

## 使用命令

```bash
# 列出所有功能
python3 scripts/feature_flags.py list

# 按标签过滤
python3 scripts/feature_flags.py list --tag core

# 检查功能状态
python3 scripts/feature_flags.py check dream_mode

# 启用功能
python3 scripts/feature_flags.py enable my_feature

# 禁用功能
python3 scripts/feature_flags.py disable experimental_feature

# 设置状态
python3 scripts/feature_flags.py set my_feature testing

# 添加新功能
python3 scripts/feature_flags.py add MY_FEATURE --description "新功能" --tag experimental

# 删除功能
python3 scripts/feature_flags.py remove old_feature
```

## 功能状态

| 状态 | 标识 | 说明 |
|------|------|------|
| enabled | ✅ 启用 | 正式可用 |
| disabled | ❌ 禁用 | 已关闭 |
| testing | 🧪 测试中 | 内部测试 |
| coming_soon | 🚧 即将发布 | 即将公开 |
| experimental | 🔬 实验性 | 可试用 |
| deprecated | 📦 已废弃 | 不再维护 |

## Agent 集成

```python
from feature_flags import is_enabled, check, get_manager

# 检查功能是否启用
if is_enabled("dream_mode"):
    run_dream_consolidation()

# 获取功能详情
info = check("kairos")
print(f"状态: {info['status_label']}")

# 注册状态变更钩子
def on_dream_enabled(name, old, new):
    print(f"Dream Mode 被 {new} 了！")

manager = get_manager()
manager.register_hook("dream_mode", on_dream_enabled)
```

## 设计参考

Claude Code 有 45 个 feature flags 控制功能发布。
这套系统让不同功能可以独立开关，是持续交付的基础设施。
