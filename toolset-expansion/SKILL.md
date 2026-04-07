---
name: toolset-expansion
description: OpenClaw 扩展工具集 — Grep 全文搜索、Glob 文件匹配、TodoWrite/TodoRead 清单管理、Rank 文件优先级排序。参考 Claude Code 的 43 工具体系设计，填补 OpenClaw 基础工具的空白。
tags: [tools, grep, glob, todo, rank, search]
version: 1.0.0
author: liutao0401@gmail.com
license: MIT
homepage: https://github.com/liutao0401-afk/openclaw-skills
---

# Toolset Expansion — 扩展工具集

参考 Claude Code 工具体系，为 OpenClaw 添加缺失的核心工具。

## 包含工具

| 工具 | 命令 | 说明 |
|------|------|------|
| Grep | `python3 scripts/toolset.py grep "pattern"` | 全文搜索 |
| Glob | `python3 scripts/toolset.py glob "*.py"` | 文件模式匹配 |
| TodoWrite | `python3 scripts/toolset.py todo add "任务"` | 添加 Todo |
| TodoRead | `python3 scripts/toolset.py todo list` | 列出 Todo |
| Rank | `python3 scripts/toolset.py rank --sort modified` | 文件优先级排序 |

## Grep 使用

```bash
# 基本搜索
python3 scripts/toolset.py grep "function_name" --path ./workspace

# 忽略大小写
python3 scripts/toolset.py grep "error" -i

# 只搜索 Python 文件
python3 scripts/toolset.py grep "TODO" --include "*.py"

# 排除特定文件
python3 scripts/toolset.py grep "password" --exclude "*.test.py"
```

## Glob 使用

```bash
# 搜索所有 Python 文件
python3 scripts/toolset.py glob "*.py"

# 搜索配置 YAML
python3 scripts/toolset.py glob "*.yaml" --path ./config

# 非递归（当前目录）
python3 scripts/toolset.py glob "*.md" --no-recursive
```

## Todo 使用

```bash
# 添加 Todo
python3 scripts/toolset.py todo add "完成登录功能" -p 2 --tag auth

# 列出 Todo
python3 scripts/toolset.py todo list

# 按状态过滤
python3 scripts/toolset.py todo list --filter pending

# 标记完成
python3 scripts/toolset.py todo done T0001

# 统计
python3 scripts/toolset.py todo stats
```

## Rank 使用

```bash
# 按修改时间排序（最近优先）
python3 scripts/toolset.py rank

# 按文件大小排序
python3 scripts/toolset.py rank --sort size

# 按名称排序
python3 scripts/toolset.py rank --sort name

# 指定路径和数量
python3 scripts/toolset.py rank --path ./src --limit 10
```

## 依赖

- Python 3.9+
- OpenClaw 工作目录

## 设计参考

Claude Code 的 Grep/Glob 工具是工作流的第一步：
"先探索再动手"（Explore before editing）是其核心方法论。
