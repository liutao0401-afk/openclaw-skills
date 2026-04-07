#!/usr/bin/env python3
"""
Dream Mode — 记忆整合引擎
当 Agent 闲置时，自动整理分散的记忆碎片，形成结构化知识。

触发条件（三重门）:
  ① 时间门：距上次整合 >= minHours (默认 24h)
  ② 会话门：新 session 数 >= minSessions (默认 3)
  ③ 锁门：获取文件 advisory lock

整理流程（4阶段）:
  Phase 1: 收集 - 汇总所有新 session 的摘要
  Phase 2: 提炼 - 提取关键决策、教训
  Phase 3: 写入 - 更新长期记忆文件
  Phase 4: 归档 - session 移入 archive/，释放空间

用法:
  python3 dream_mode.py status          # 查看整理状态
  python3 dream_mode.py trigger        # 手动触发整合
  python3 dream_mode.py archive        # 归档旧 session
  python3 dream_mode.py consolidate      # 运行完整整合流程
"""
import json
import pathlib
import sys
import datetime
import os
import shutil
import argparse
from typing import List, Dict, Optional, Any
from collections import defaultdict

# 路径设置
_BASE = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = _BASE / "workspace"
MEMORY_DIR = WORKSPACE / "agent_memory"
MEMORIES_DIR = MEMORY_DIR / "memories"
ARCHIVE_DIR = MEMORY_DIR / "archive"
LOCKS_DIR = MEMORY_DIR / "locks"
DREAM_STATE_FILE = MEMORY_DIR / "dream_state.json"
SESSIONS_DIR = _BASE / "agents" / "main" / "sessions"

# 确保目录存在
for d in [MEMORIES_DIR, ARCHIVE_DIR, LOCKS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── 配置 ──
MIN_HOURS = 24  # 距上次整合最少小时
MIN_SESSIONS = 3  # 最少新 session 数
STALE_HOURS = 1  # 锁过期小时数
MAX_ARCHIVE_AGE_DAYS = 30  # 超过这个天数的 session 才归档
DREAM_MODEL = None  # None = 使用当前 agent 的默认模型


def now_iso():
    return datetime.datetime.now().isoformat()


def _read_json(path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path, data):
    tmp = str(path) + ".tmp"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        pathlib.Path(tmp).unlink(missing_ok=True)
    except Exception:
        pass


# ── 锁管理 ──

class AdvisoryLock:
    """简单的文件 advisory lock（基于 PID + mtime）"""

    def __init__(self, name: str):
        self.lock_file = LOCKS_DIR / f"{name}.lock"
        self.acquired = False

    def acquire(self, timeout_sec: int = 30) -> bool:
        """尝试获取锁，返回是否成功"""
        start = datetime.datetime.now()
        while True:
            if self._try_acquire():
                self.acquired = True
                return True
            if (datetime.datetime.now() - start).total_seconds() > timeout_sec:
                return False
            import time
            time.sleep(1)

    def _try_acquire(self) -> bool:
        """单次获取尝试"""
        if self.lock_file.exists():
            lock_data = _read_json(self.lock_file)
            if not lock_data:
                return False

            # 检查是否过期
            acquired_at = lock_data.get("acquiredAt", "")
            try:
                acquired_time = datetime.datetime.fromisoformat(acquired_at)
                age_hours = (datetime.datetime.now() - acquired_time).total_seconds() / 3600
                if age_hours < STALE_HOURS:
                    # 锁有效，检查 PID 是否还活着
                    pid = lock_data.get("pid")
                    if pid and _is_pid_alive(pid):
                        return False  # 锁被占用
            except Exception:
                pass

        # 获取锁
        lock_data = {
            "pid": os.getpid(),
            "acquiredAt": now_iso(),
            "holder": "dream_mode",
        }
        _write_json(self.lock_file, lock_data)
        return True

    def release(self):
        """释放锁"""
        if self.acquired and self.lock_file.exists():
            try:
                self.lock_file.unlink()
            except Exception:
                pass
            self.acquired = False


def _is_pid_alive(pid: int) -> bool:
    """检查进程是否存活"""
    try:
        if os.name == "nt":
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True, timeout=5
            )
            return str(pid) in result.stdout
        else:
            import subprocess
            result = subprocess.run(
                ["ps", "-p", str(pid)],
                capture_output=True, timeout=5
            )
            return result.returncode == 0
    except Exception:
        return False


# ── Dream State ──

def get_dream_state() -> Dict:
    """获取当前整合状态"""
    return _read_json(DREAM_STATE_FILE, {
        "lastConsolidatedAt": None,
        "lastConsolidatedSessions": 0,
        "totalConsolidations": 0,
        "totalLessonsLearned": 0,
        "lockedBy": None,
        "lastError": None,
    })


def update_dream_state(**kwargs):
    """更新整合状态"""
    state = get_dream_state()
    state.update(kwargs)
    _write_json(DREAM_STATE_FILE, state)


# ── Session 收集 ──

def get_recent_sessions(limit: int = 20) -> List[Dict]:
    """从 session 目录收集最近的 session"""
    if not SESSIONS_DIR.exists():
        return []

    jsonl_files = sorted(
        SESSIONS_DIR.glob("*.jsonl"),
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )

    sessions = []
    for sf in jsonl_files[:limit]:
        try:
            content = sf.read_text(errors="ignore")
            lines = content.splitlines()
            if not lines:
                continue

            # 找第一条和最后一条消息的时间
            first_ts = None
            last_ts = None
            message_count = 0
            preview = ""

            for ln in lines[-20:]:  # 只看最后 20 条
                try:
                    item = json.loads(ln)
                    msg = item.get("message", {})
                    role = msg.get("role", "")
                    ts = item.get("timestamp", "")

                    if role == "user":
                        message_count += 1
                        if not first_ts:
                            first_ts = ts
                        last_ts = ts
                        # 取第一条 user 消息作为 preview
                        if not preview:
                            for c in msg.get("content", []):
                                if c.get("type") == "text" and c.get("text"):
                                    preview = c["text"][:100]
                                    break
                except Exception:
                    continue

            sessions.append({
                "file": sf.name,
                "path": str(sf),
                "firstTs": first_ts,
                "lastTs": last_ts,
                "messageCount": message_count,
                "preview": preview,
                "size": sf.stat().st_size,
            })
        except Exception:
            continue

    return sessions


def get_new_sessions_since(last_consolidated: Optional[str]) -> List[Dict]:
    """获取自上次整合后新增的 session"""
    all_sessions = get_recent_sessions(limit=50)
    if not last_consolidated:
        return all_sessions[:MIN_SESSIONS]

    new_sessions = []
    for s in all_sessions:
        if s["firstTs"] and s["firstTs"] > last_consolidated:
            new_sessions.append(s)

    return new_sessions


# ── 记忆文件操作 ──

def get_memory_file(agent_id: str = "main", memory_type: str = "longterm") -> pathlib.Path:
    """获取指定类型的记忆文件路径"""
    agent_dir = MEMORIES_DIR / agent_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    return agent_dir / f"{memory_type}.json"


def read_longterm_memory(agent_id: str = "main") -> Dict:
    """读取长期记忆"""
    return _read_json(get_memory_file(agent_id, "longterm"), {
        "version": 1,
        "updatedAt": None,
        "entries": [],  # [{id, content, source, tags, createdAt, lastUsedAt, useCount}]
        "stats": {
            "totalEntries": 0,
            "byTag": {},
        }
    })


def read_lessons(agent_id: str = "main") -> List[Dict]:
    """读取教训列表"""
    return _read_json(get_memory_file(agent_id, "lessons"), [])


def read_decisions(agent_id: str = "main") -> List[Dict]:
    """读取关键决策列表"""
    return _read_json(get_memory_file(agent_id, "decisions"), [])


def write_longterm_memory(agent_id: str, memory: Dict):
    """写入长期记忆"""
    memory["updatedAt"] = now_iso()
    memory["stats"]["totalEntries"] = len(memory.get("entries", []))
    _write_json(get_memory_file(agent_id, "longterm"), memory)


# ── 记忆提炼 ──

def _extract_key_decisions(session_previews: List[str]) -> List[Dict]:
    """从 session 摘要中提取关键决策"""
    # 简单的启发式提取（真正生产环境应该用 LLM）
    decisions = []
    keywords = [
        "决定", "选择了", "采用", "确定",
        "decided", "chose", "adopted", "选择",
        "规划", "计划", "计划采用",
    ]

    for preview in session_previews:
        if not preview:
            continue
        text = preview.lower()
        for kw in keywords:
            if kw.lower() in text:
                decisions.append({
                    "id": f"dec_{now_iso().replace(':', '').replace('-', '')[:15]}",
                    "content": preview[:200],
                    "source": "session",
                    "extractedAt": now_iso(),
                })
                break

    return decisions[:10]  # 最多 10 条


def _extract_lessons(session_previews: List[str]) -> List[str]:
    """从 session 中提炼教训（简单的关键词匹配）"""
    lessons = []
    patterns = [
        ("错误", "学到的教训："),
        ("失败", "教训："),
        ("修复", "避免同类问题："),
        ("bug", "下次注意："),
        ("问题", "解决方案："),
    ]

    for preview in session_previews:
        if not preview:
            continue
        for keyword, lesson_type in patterns:
            if keyword in preview.lower():
                lessons.append(f"{lesson_type} {preview[:150]}")
                break

    return lessons[:10]


# ── 核心整合流程 ──

def run_dream_consolidation(agent_id: str = "main") -> Dict:
    """运行完整的记忆整合流程"""
    lock = AdvisoryLock("consolidation")

    if not lock.acquire(timeout_sec=5):
        return {
            "ok": False,
            "error": "无法获取锁，另一进程正在进行整合",
            "lockedBy": _read_json(LOCKS_DIR / "consolidation.lock", {}).get("pid"),
        }

    try:
        state = get_dream_state()
        last_consolidated = state.get("lastConsolidatedAt")

        # Phase 1: 收集
        new_sessions = get_new_sessions_since(last_consolidated)
        if len(new_sessions) < MIN_SESSIONS:
            return {
                "ok": True,
                "skipped": True,
                "reason": f"新 session 不足（{len(new_sessions)}/{MIN_SESSIONS}）",
                "nextCheck": "下次心跳时再检查",
            }

        session_previews = [s.get("preview", "") for s in new_sessions]
        session_ids = [s.get("file", "") for s in new_sessions]

        # Phase 2: 提炼
        decisions = _extract_key_decisions(session_previews)
        lessons = _extract_lessons(session_previews)

        # Phase 3: 写入
        # 更新长期记忆
        longterm = read_longterm_memory(agent_id)
        for decision in decisions:
            # 避免重复
            existing = [e.get("content", "") for e in longterm.get("entries", [])]
            if decision.get("content") not in existing:
                decision["useCount"] = 0
                decision["lastUsedAt"] = None
                longterm["entries"].append(decision)

        # 限制记忆条目数量
        MAX_ENTRIES = 200
        if len(longterm["entries"]) > MAX_ENTRIES:
            # 按使用频率和创建时间排序，保留最重要的
            longterm["entries"].sort(
                key=lambda e: (e.get("useCount", 0), e.get("extractedAt", "")),
                reverse=True
            )
            longterm["entries"] = longterm["entries"][:MAX_ENTRIES]

        write_longterm_memory(agent_id, longterm)

        # 写入教训
        existing_lessons = read_lessons(agent_id)
        for lesson in lessons:
            if lesson not in existing_lessons:
                existing_lessons.append(lesson)
        # 限制教训数量
        if len(existing_lessons) > 100:
            existing_lessons = existing_lessons[-100:]
        _write_json(get_memory_file(agent_id, "lessons"), existing_lessons)

        # 写入决策
        existing_decisions = read_decisions(agent_id)
        for decision in decisions:
            if decision not in existing_decisions:
                existing_decisions.append(decision)
        if len(existing_decisions) > 100:
            existing_decisions = existing_decisions[-100:]
        _write_json(get_memory_file(agent_id, "decisions"), existing_decisions)

        # Phase 4: 归档 session（标记为已处理）
        archive_index = _read_json(ARCHIVE_DIR / "index.json", {"archived": [], "sessions": {}})
        for sid in session_ids:
            if sid not in archive_index.get("archived", []):
                archive_index["archived"].append(sid)
                archive_index["sessions"][sid] = {
                    "archivedAt": now_iso(),
                    "preview": session_previews[session_ids.index(sid)][:100] if session_ids.index(sid) < len(session_previews) else "",
                }
        _write_json(ARCHIVE_DIR / "index.json", archive_index)

        # 更新状态
        new_count = len(new_sessions)
        update_dream_state(
            lastConsolidatedAt=now_iso(),
            lastConsolidatedSessions=state.get("lastConsolidatedSessions", 0) + new_count,
            totalConsolidations=state.get("totalConsolidations", 0) + 1,
            totalLessonsLearned=state.get("totalLessonsLearned", 0) + len(lessons),
            lastError=None,
        )

        return {
            "ok": True,
            "phases": {
                "collected": f"{new_count} 个新 session",
                "decisions": f"{len(decisions)} 条关键决策",
                "lessons": f"{len(lessons)} 条教训",
            },
            "memory": {
                "totalEntries": len(longterm["entries"]),
                "totalLessons": len(existing_lessons),
                "totalDecisions": len(existing_decisions),
            },
            "consolidatedAt": now_iso(),
        }

    except Exception as e:
        update_dream_state(lastError=str(e))
        return {"ok": False, "error": str(e)}

    finally:
        lock.release()


def check_gates() -> Dict:
    """检查三重重置是否满足"""
    state = get_dream_state()
    last = state.get("lastConsolidatedAt")

    # 时间门
    time_gate = True
    if last:
        try:
            last_time = datetime.datetime.fromisoformat(last)
            hours_since = (datetime.datetime.now() - last_time).total_seconds() / 3600
            time_gate = hours_since >= MIN_HOURS
        except Exception:
            time_gate = True

    # 会话门
    new_sessions = get_new_sessions_since(last)
    session_gate = len(new_sessions) >= MIN_SESSIONS

    # 锁门
    lock = AdvisoryLock("consolidation")
    can_acquire = lock.acquire(timeout_sec=1)
    if can_acquire:
        lock.release()

    return {
        "timeGate": time_gate,
        "timeGateHours": MIN_HOURS,
        "sessionGate": session_gate,
        "sessionGateMin": MIN_SESSIONS,
        "newSessions": len(new_sessions) if new_sessions else 0,
        "lockGate": can_acquire,
        "allGatesPass": time_gate and session_gate and can_acquire,
    }


# ── CLI ──

def cmd_status(args):
    """查看整合状态"""
    state = get_dream_state()
    gates = check_gates()

    print(f"""
╔══════════════════════════════════════════════════════╗
║  🌙 Dream Mode 记忆整合状态                         ║
╚══════════════════════════════════════════════════════╝

整合统计:
  • 上次整合: {state.get('lastConsolidatedAt') or '从未整合'}
  • 累计整合次数: {state.get('totalConsolidations', 0)}
  • 累计处理 session: {state.get('lastConsolidatedSessions', 0)}
  • 学到的教训: {state.get('totalLessonsLearned', 0)}

触发条件检查:
  {'✅' if gates['timeGate'] else '⏳'} 时间门: {gates['timeGateHours']}h 冷却 ({gates['timeGateHours'] if gates['timeGate'] else '未满足'})
  {'✅' if gates['sessionGate'] else '⏳'} 会话门: >= {gates['sessionGateMin']} 个新 session ({gates['newSessions'] if gates['sessionGate'] else f'{gates["newSessions"]} 个'})
  {'✅' if gates['lockGate'] else '🔒'} 锁门: {'可获取' if gates['lockGate'] else '被占用'}
  {'✅' if gates['allGatesPass'] else '⏳'} 三重门: {'全部满足，可触发整合' if gates['allGatesPass'] else '未全部满足'}

最近 session ({min(5, len(get_recent_sessions(5))) } 个):
""")

    for s in get_recent_sessions(5):
        print(f"  • {s.get('file', 'unknown')} | {s.get('messageCount', 0)} 条消息 | {s.get('preview', '')[:50]}")

    if state.get("lastError"):
        print(f"\n⚠️ 最近错误: {state['lastError']}")


def cmd_trigger(args):
    """手动触发整合"""
    gates = check_gates()
    if not gates["allGatesPass"]:
        print("⚠️ 触发条件未全部满足，强制运行...")
        if not args.force:
            print("  (use --force to override)")
            return

    result = run_dream_consolidation(args.agent)
    if result.get("ok"):
        if result.get("skipped"):
            print(f"⏭️ 跳过: {result['reason']}")
        else:
            print(f"✅ 整合完成:")
            for phase, info in result.get("phases", {}).items():
                print(f"   • {phase}: {info}")
            m = result.get("memory", {})
            print(f"   → 长期记忆: {m.get('totalEntries', 0)} 条")
            print(f"   → 教训: {m.get('totalLessons', 0)} 条")
    else:
        print(f"❌ 整合失败: {result.get('error')}")


def cmd_archive(args):
    """归档旧 session"""
    state = get_dream_state()
    last = state.get("lastConsolidatedAt")

    sessions = get_recent_sessions(limit=50)
    archive_index = _read_json(ARCHIVE_DIR / "index.json", {"archived": [], "sessions": {}})
    already_archived = set(archive_index.get("archived", []))

    old_sessions = []
    for s in sessions:
        if s.get("file") in already_archived:
            continue
        if last and s.get("firstTs") and s["firstTs"] <= last:
            old_sessions.append(s)
        elif not last:
            old_sessions.append(s)

    print(f"发现 {len(old_sessions)} 个待归档 session")

    for s in old_sessions[: args.limit]:
        archive_index["archived"].append(s["file"])
        archive_index["sessions"][s["file"]] = {
            "archivedAt": now_iso(),
            "preview": s.get("preview", "")[:100],
            "firstTs": s.get("firstTs"),
            "lastTs": s.get("lastTs"),
        }
        print(f"  ✓ {s['file']}")

    _write_json(ARCHIVE_DIR / "index.json", archive_index)
    print(f"已归档 {min(len(old_sessions), args.limit)} 个 session")


def cmd_consolidate(args):
    """运行完整整合流程"""
    result = run_dream_consolidation(args.agent)
    if result.get("ok"):
        if result.get("skipped"):
            print(f"⏭️ {result['reason']}")
            gates = check_gates()
            print(f"   新 session: {gates['newSessions']}/{gates['sessionGateMin']}")
        else:
            print("✅ 整合完成!")
            for k, v in result.get("phases", {}).items():
                print(f"   {k}: {v}")
    else:
        print(f"❌ 失败: {result.get('error')}")


def cmd_view(args):
    """查看记忆内容"""
    if args.type == "lessons":
        lessons = read_lessons(args.agent)
        print(f"📝 教训 ({len(lessons)} 条):\n")
        for i, l in enumerate(lessons[-args.limit:], 1):
            print(f"  {i}. {l}")
    elif args.type == "decisions":
        decisions = read_decisions(args.agent)
        print(f"🎯 关键决策 ({len(decisions)} 条):\n")
        for d in decisions[-args.limit:]:
            print(f"  • {d.get('content', '')[:100]}")
    elif args.type == "memory":
        memory = read_longterm_memory(args.agent)
        entries = memory.get("entries", [])
        print(f"🧠 长期记忆 ({len(entries)} 条):\n")
        for e in entries[-args.limit:]:
            print(f"  • [{e.get('source', '')}] {e.get('content', '')[:100]}")
    else:
        print(f"未知类型: {args.type}")


def main():
    parser = argparse.ArgumentParser(description="Dream Mode 记忆整合引擎")
    sub = parser.add_subparsers(dest="cmd", help="子命令")

    sub.add_parser("status", help="查看整合状态")
    p_trigger = sub.add_parser("trigger", help="手动触发整合")
    p_trigger.add_argument("--agent", default="main")
    p_trigger.add_argument("--force", action="store_true")
    sub.add_parser("archive", help="归档旧 session").add_argument("--limit", type=int, default=10)
    p_consolidate = sub.add_parser("consolidate", help="运行整合")
    p_consolidate.add_argument("--agent", default="main")

    p_view = sub.add_parser("view", help="查看记忆内容")
    p_view.add_argument("--type", choices=["memory", "lessons", "decisions"], default="memory")
    p_view.add_argument("--agent", default="main")
    p_view.add_argument("--limit", type=int, default=20)

    sub.add_parser("gates", help="检查触发条件")

    args = parser.parse_args()

    if args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "trigger":
        cmd_trigger(args)
    elif args.cmd == "archive":
        cmd_archive(args)
    elif args.cmd == "consolidate":
        cmd_consolidate(args)
    elif args.cmd == "view":
        cmd_view(args)
    elif args.cmd == "gates":
        gates = check_gates()
        print(json.dumps(gates, indent=2, ensure_ascii=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
