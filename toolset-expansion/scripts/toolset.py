#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
OpenClaw 扩展工具集
Grep / Glob / TodoWrite / TodoRead / FileSearch / Rank

用法：
  python3 scripts/toolset.py grep "pattern" --path ./workspace
  python3 scripts/toolset.py glob "*.py" --path ./workspace
  python3 scripts/toolset.py todo list
  python3 scripts/toolset.py todo add "完成任务"
  python3 scripts/toolset.py todo done "任务ID"
  python3 scripts/toolset.py rank --path ./workspace
"""
import os
import sys
import json
import pathlib
import argparse
import re
import fnmatch
import hashlib
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

BASE = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = BASE / "workspace"
TODO_FILE = WORKSPACE / "data" / "todo.json"

# ── Todo 系统 ──

def ensure_todo_file():
    TODO_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not TODO_FILE.exists():
        TODO_FILE.write_text(json.dumps({
            "version": 1,
            "todos": [],
            "lastId": 0
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def todo_list(filter_status: str = None) -> List[Dict]:
    """列出所有 Todo"""
    ensure_todo_file()
    data = json.loads(TODO_FILE.read_text(encoding="utf-8"))
    todos = data.get("todos", [])
    if filter_status:
        todos = [t for t in todos if t.get("status") == filter_status]
    return sorted(todos, key=lambda t: t.get("priority", 5) - t.get("createdAt", ""))


def todo_add(title: str, priority: int = 3, tags: List[str] = None) -> Dict:
    """添加新 Todo"""
    ensure_todo_file()
    data = json.loads(TODO_FILE.read_text(encoding="utf-8"))
    last_id = data.get("lastId", 0) + 1
    todo = {
        "id": f"T{last_id:04d}",
        "title": title,
        "status": "pending",
        "priority": priority,  # 1=最高, 5=最低
        "tags": tags or [],
        "createdAt": datetime.now().isoformat(),
        "completedAt": None,
        "updatedAt": datetime.now().isoformat(),
    }
    data["todos"].append(todo)
    data["lastId"] = last_id
    TODO_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return todo


def todo_done(todo_id: str) -> Optional[Dict]:
    """标记 Todo 完成"""
    ensure_todo_file()
    data = json.loads(TODO_FILE.read_text(encoding="utf-8"))
    for todo in data["todos"]:
        if todo.get("id") == todo_id:
            todo["status"] = "completed"
            todo["completedAt"] = datetime.now().isoformat()
            todo["updatedAt"] = datetime.now().isoformat()
            TODO_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return todo
    return None


def todo_remove(todo_id: str) -> bool:
    """删除 Todo"""
    ensure_todo_file()
    data = json.loads(TODO_FILE.read_text(encoding="utf-8"))
    original_len = len(data["todos"])
    data["todos"] = [t for t in data["todos"] if t.get("id") != todo_id]
    if len(data["todos"]) < original_len:
        TODO_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return True
    return False


def todo_stats() -> Dict:
    """Todo 统计"""
    ensure_todo_file()
    data = json.loads(TODO_FILE.read_text(encoding="utf-8"))
    todos = data.get("todos", [])
    return {
        "total": len(todos),
        "pending": sum(1 for t in todos if t.get("status") == "pending"),
        "completed": sum(1 for t in todos if t.get("status") == "completed"),
        "byPriority": {
            str(i): sum(1 for t in todos if t.get("priority") == i and t.get("status") == "pending")
            for i in range(1, 6)
        }
    }


# ── Grep ──

def grep(pattern: str, path: str = None, case_insensitive: bool = False,
          include: str = None, exclude: str = None, max_results: int = 100) -> List[Dict]:
    """
    在文件中搜索文本
    """
    root = pathlib.Path(path) if path else WORKSPACE
    if not root.exists():
        return []

    pattern_re = re.compile(pattern, re.IGNORECASE if case_insensitive else 0)
    results = []

    include_patterns = include.split(",") if include else ["*"]
    exclude_patterns = exclude.split(",") if exclude else []

    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue

        # 跳过二进制文件和大文件
        if file_path.stat().st_size > 5 * 1024 * 1024:
            continue

        # 匹配包含模式
        if include_patterns and not any(fnmatch.fnmatch(str(file_path), p.strip()) for p in include_patterns):
            continue

        # 匹配排除模式
        if exclude_patterns and any(fnmatch.fnmatch(str(file_path), p.strip()) for p in exclude_patterns):
            continue

        # 跳过二进制扩展名
        skip_exts = {".pyc", ".png", ".jpg", ".gif", ".zip", ".pdf", ".exe", ".dll", ".node"}
        if file_path.suffix.lower() in skip_exts:
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for line_no, line in enumerate(content.splitlines(), 1):
            if pattern_re.search(line):
                results.append({
                    "file": str(file_path.relative_to(root)),
                    "line": line_no,
                    "content": line.strip()[:200],
                    "match": pattern_re.findall(line),
                })
                if len(results) >= max_results:
                    break

    return results


# ── Glob ──

def glob(pattern: str, path: str = None, recursive: bool = True, include_dirs: bool = False) -> List[str]:
    """
    按模式匹配文件
    """
    root = pathlib.Path(path) if path else WORKSPACE
    if not root.exists():
        return []

    results = []
    if recursive:
        iterator = root.rglob(pattern)
    else:
        iterator = root.glob(pattern)

    for p in iterator:
        if not p.is_file() and not (include_dirs and p.is_dir()):
            continue
        if p.is_file() and p.stat().st_size > 100 * 1024 * 1024:  # 跳过 >100MB 文件
            continue
        results.append(str(p.relative_to(root)))

    return sorted(results, key=lambda x: x.lower())


# ── File Rank ──

def rank_files(path: str = None, by: str = "modified", limit: int = 20) -> List[Dict]:
    """
    按优先级排序文件（用于决定优先处理哪些）
    by: modified | size | name | recently_changed
    """
    root = pathlib.Path(path) if path else WORKSPACE
    if not root.exists():
        return []

    files = []
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix in {".pyc", ".git"}:
            continue

        stat = f.stat()
        files.append({
            "path": str(f.relative_to(root)),
            "modified": stat.st_mtime,
            "size": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 1),
        })

    if by == "modified":
        files.sort(key=lambda f: f["modified"], reverse=True)
    elif by == "size":
        files.sort(key=lambda f: f["size"], reverse=True)
    elif by == "name":
        files.sort(key=lambda f: f["path"].lower())

    return files[:limit]


# ── File Hash ──

def file_hash(file_path: str, algo: str = "md5") -> Optional[str]:
    """计算文件哈希"""
    try:
        p = pathlib.Path(file_path)
        if not p.exists() or not p.is_file():
            return None
        h = hashlib.new(algo)
        h.update(p.read_bytes())
        return h.hexdigest()
    except Exception:
        return None


# ── CLI ──

def cmd_grep(args):
    results = grep(args.pattern, path=args.path,
                  case_insensitive=args.ignore_case,
                  include=args.include, exclude=args.exclude,
                  max_results=args.max_results)
    if not results:
        print(f"未找到匹配 '{args.pattern}' 的内容")
        return
    print(f"找到 {len(results)} 个匹配：\n")
    for r in results:
        print(f"{r['file']}:{r['line']}: {r['content']}")
    return results


def cmd_glob(args):
    results = glob(args.pattern, path=args.path,
                   recursive=not args.no_recursive,
                   include_dirs=args.dirs)
    if not results:
        print(f"未找到匹配 '{args.pattern}' 的文件")
        return
    print(f"找到 {len(results)} 个文件：\n")
    for f in results:
        print(f)


def cmd_todo(args):
    if args.action == "list":
        todos = todo_list(filter_status=args.filter)
        stats = todo_stats()
        print(f"\n📋 Todo 统计：待办 {stats['pending']} / 已完成 {stats['completed']} / 总计 {stats['total']}")
        if args.filter:
            print(f"过滤：{args.filter}")
        print()
        if not todos:
            print("  (空)")
        for t in todos:
            status_icon = "✅" if t.get("status") == "completed" else "⬜"
            priority_bar = "🔴" * t.get("priority", 3) + "⚪" * (5 - t.get("priority", 3))
            tags = f" [{', '.join(t.get('tags', []))}]" if t.get("tags") else ""
            print(f"  {status_icon} [{t['id']}] {priority_bar} {t.get('title', '')}{tags}")
        print()
    elif args.action == "add":
        todo = todo_add(args.title, priority=args.priority or 3, tags=args.tag)
        print(f"✅ 已添加：[{todo['id']}] {todo['title']} (优先级: {todo['priority']})")
    elif args.action == "done":
        todo = todo_done(args.id)
        if todo:
            print(f"✅ 已完成：[{todo['id']}] {todo['title']}")
        else:
            print(f"❌ 找不到 Todo: {args.id}")
    elif args.action == "remove":
        ok = todo_remove(args.id)
        print(f"{'✅ 已删除' if ok else '❌ 找不到'}: {args.id}")
    elif args.action == "stats":
        stats = todo_stats()
        print(f"\n📊 Todo 统计：")
        print(f"  总计: {stats['total']}")
        print(f"  待办: {stats['pending']}")
        print(f"  已完成: {stats['completed']}")
        print(f"  按优先级（待办）:")
        for p, count in stats["byPriority"].items():
            bar = "🔴" * int(p) + "⚪" * (5 - int(p))
            print(f"    {bar} P{p}: {count}")


def cmd_rank(args):
    files = rank_files(path=args.path, by=args.sort, limit=args.limit)
    if not files:
        print("未找到文件")
        return
    print(f"\n📁 文件优先级排序（{args.sort}）：\n")
    for i, f in enumerate(files, 1):
        size_str = f"{f['size_kb']} KB" if f['size_kb'] < 1024 else f"{f['size_kb']/1024:.1f} MB"
        modified = datetime.fromtimestamp(f['modified']).strftime("%m-%d %H:%M")
        print(f"  {i:2d}. {size_str:>10s} {modified}  {f['path']}")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw 扩展工具集")
    sub = parser.add_subparsers(dest="cmd", help="子命令")

    # grep
    p_grep = sub.add_parser("grep", help="在文件中搜索文本")
    p_grep.add_argument("pattern", help="搜索模式（正则）")
    p_grep.add_argument("--path", help="搜索路径")
    p_grep.add_argument("-i", "--ignore-case", action="store_true")
    p_grep.add_argument("--include", help="包含的文件模式（如 *.py,*.md）")
    p_grep.add_argument("--exclude", help="排除的文件模式")
    p_grep.add_argument("-m", "--max-results", type=int, default=100)

    # glob
    p_glob = sub.add_parser("glob", help="按模式匹配文件")
    p_glob.add_argument("pattern", help="文件模式（如 *.py）")
    p_glob.add_argument("--path", help="搜索路径")
    p_glob.add_argument("--no-recursive", action="store_true")
    p_glob.add_argument("--dirs", action="store_true", help="包含目录")

    # todo
    p_todo = sub.add_parser("todo", help="Todo 列表管理")
    p_todo.add_argument("action", choices=["list", "add", "done", "remove", "stats"])
    p_todo.add_argument("id", nargs="?", help="Todo ID（如 T0001）")
    p_todo.add_argument("--title", help="Todo 标题（add 时用）")
    p_todo.add_argument("-p", "--priority", type=int, help="优先级 1-5")
    p_todo.add_argument("--tag", action="append", help="标签")
    p_todo.add_argument("--filter", choices=["pending", "completed"], help="过滤状态")

    # rank
    p_rank = sub.add_parser("rank", help="文件优先级排序")
    p_rank.add_argument("--path", help="搜索路径")
    p_rank.add_argument("--sort", choices=["modified", "size", "name"], default="modified")
    p_rank.add_argument("-n", "--limit", type=int, default=20)

    args = parser.parse_args()

    if args.cmd == "grep":
        cmd_grep(args)
    elif args.cmd == "glob":
        cmd_glob(args)
    elif args.cmd == "todo":
        cmd_todo(args)
    elif args.cmd == "rank":
        cmd_rank(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
