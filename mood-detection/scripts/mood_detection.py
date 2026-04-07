#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
心情检测系统
Regex 匹配用户情绪，生成响应策略

用法：
  python3 scripts/mood_detection.py detect "这个bug怎么修都修不好！"
  python3 scripts/mood_detection.py respond --mood frustrated
  python3 scripts/mood_detection.py log "user123" "太好了！完美！"
"""
import json
import re
import sys
import pathlib
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime

BASE = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = BASE / "workspace"
MOOD_LOG_FILE = WORKSPACE / "data" / "mood_history.json"

# ── 心情模式定义 ──

@dataclass
class MoodConfig:
    id: str
    emoji: str
    label: str
    tone: str
    response_strategy: str
    priority_boost: int  # 优先级提升
    patterns: List[str]


MOOD_CONFIGS = {
    "frustrated": MoodConfig(
        id="frustrated",
        emoji="😤",
        label="挫败",
        tone="apologetic.supportive",
        response_strategy="请耐心描述问题，我会一步步帮你排查",
        priority_boost=3,
        patterns=[
            r"怎么不行", r"不行", r"不对", r"有问题", r"糟糕",
            r"不对", r"不行", r"不能", r"没用", r"失败",
            r"这不工作", r"不工作", r"我不懂", r"到底怎么回事",
            r"烦", r"累", r"崩溃",
            r"why.*not.*work", r"doesn't.*work", r"wtf", r"damn",
        ]
    ),
    "angry": MoodConfig(
        id="angry",
        emoji="😠",
        label="愤怒",
        tone="calm.reassuring",
        response_strategy="深呼吸，我来帮你解决这个问题",
        priority_boost=5,
        patterns=[
            r"生气", r"怒", r"气死了", r"气死我了",
            r"垃圾", r"烂", r"破", r"垃圾代码",
            r"什么垃圾", r"傻.*逼", r"智障",
            r"hate", r"angry", r"furious", r"terrible",
        ]
    ),
    "confused": MoodConfig(
        id="confused",
        emoji="😕",
        label="困惑",
        tone="patient.explanatory",
        response_strategy="没关系，我一步步解释给你听",
        priority_boost=2,
        patterns=[
            r"什么是", r"怎么用", r"不明白", r"不懂", r"不理解",
            r"啥意思", r"啥", r"啥是", r"怎么",
            r"help", r"how.*do", r"what.*is", r"confused", r"lost",
            r"教我", r"教教我", r"解释一下", r"说明",
        ]
    ),
    "excited": MoodConfig(
        id="excited",
        emoji="🤩",
        label="兴奋",
        tone="enthusiastic",
        response_strategy="太好了！让我们继续！",
        priority_boost=0,
        patterns=[
            r"太棒了", r"厉害", r"完美", r"喜欢", r"太酷了",
            r"好厉害", r"牛逼", r"牛", r"强", r" excellent",
            r"awesome", r"amazing", r"love.*it", r"great", r"perfect",
        ]
    ),
    "sad": MoodConfig(
        id="sad",
        emoji="😢",
        label="难过",
        tone="warm.supportive",
        response_strategy="别难过，我们一起想办法",
        priority_boost=2,
        patterns=[
            r"难过", r"伤心", r"郁闷", r"心塞",
            r"算了", r"不想做了", r"没意思",
            r"sad", r"unhappy", r"depressed",
        ]
    ),
    "neutral": MoodConfig(
        id="neutral",
        emoji="😐",
        label="平静",
        tone="professional",
        response_strategy="好的，我来处理",
        priority_boost=0,
        patterns=[]
    ),
    "impatient": MoodConfig(
        id="impatient",
        emoji="⏰",
        label="急躁",
        tone="efficient.direct",
        response_strategy="明白，我马上帮你搞定",
        priority_boost=4,
        patterns=[
            r"快点", r"快点", r"赶紧", r"快",
            r"慢", r"太慢了", r"等不及",
            r" hurry", r"quick", r"fast", r"slow",
            r"asap", r"right now",
        ]
    ),
    "curious": MoodConfig(
        id="curious",
        emoji="🤔",
        label="好奇",
        tone="informative.interested",
        response_strategy="好问题！让我来解答",
        priority_boost=1,
        patterns=[
            r"为什么", r"怎么回事", r"原理", r"为什么",
            r"好奇", r"想知道", r"问下",
            r"why", r"how come", r"curious", r"wonder",
        ]
    ),
    "grateful": MoodConfig(
        id="grateful",
        emoji="🙏",
        label="感谢",
        tone="warm.grateful",
        response_strategy="不客气！有问题随时找我",
        priority_boost=0,
        patterns=[
            r"谢谢", r"感谢", r"多谢", r"感恩",
            r"thx", r"thanks", r"thank you", r"appreciate",
        ]
    ),
}


# ── 检测引擎 ──

def detect_mood(text: str) -> Tuple[str, MoodConfig, List[str]]:
    """
    检测文本中的心情

    Returns:
        (mood_id, mood_config, matched_patterns)
    """
    if not text:
        return "neutral", MOOD_CONFIGS["neutral"], []

    text_lower = text.lower()
    matched = []

    # 按优先级排序检测
    priority_order = ["angry", "frustrated", "impatient", "sad",
                      "confused", "curious", "excited", "grateful"]

    for mood_id in priority_order:
        config = MOOD_CONFIGS.get(mood_id)
        if not config:
            continue
        for pattern in config.patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                matched.append(pattern)
                return mood_id, config, matched

    return "neutral", MOOD_CONFIGS["neutral"], []


def detect_mood_with_intensity(text: str) -> Dict:
    """
    带强度的检测（可用于复杂情绪判断）
    """
    if not text:
        return {"mood": "neutral", "intensity": 0, "signals": []}

    text_lower = text.lower()
    signals = []

    for mood_id, config in MOOD_CONFIGS.items():
        for pattern in config.patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                signals.append({
                    "mood": mood_id,
                    "pattern": pattern,
                    "matched_text": match.group(),
                })

    if not signals:
        return {"mood": "neutral", "intensity": 0, "signals": []}

    # 取最高优先级的
    priority_order = ["angry", "frustrated", "impatient", "sad",
                      "confused", "curious", "excited", "grateful", "neutral"]

    top_signal = signals[0]  # 默认第一个
    for sig in signals:
        if priority_order.index(sig["mood"]) < priority_order.index(top_signal["mood"]):
            top_signal = sig

    return {
        "mood": top_signal["mood"],
        "intensity": len(signals),
        "signals": signals,
        "config": MOOD_CONFIGS[top_signal["mood"]].__dict__,
    }


# ── 响应生成 ──

def generate_response(mood_id: str, context: str = "") -> str:
    """根据心情生成响应前缀"""
    config = MOOD_CONFIGS.get(mood_id, MOOD_CONFIGS["neutral"])

    # 上下文增强
    if context:
        context_lower = context.lower()
        if "bug" in context_lower or "错误" in context_lower or "报错" in context_lower:
            return f"{config.emoji} {config.response_strategy} 有 bug 我们就一个个排查。"
        if "代码" in context_lower or "code" in context_lower:
            return f"{config.emoji} {config.response_strategy} 代码的事交给我。"

    return f"{config.emoji} {config.response_strategy}"


def get_tone_for_mood(mood_id: str) -> str:
    """获取心情对应的语气风格"""
    config = MOOD_CONFIGS.get(mood_id, MOOD_CONFIGS["neutral"])
    return config.tone


# ── 日志记录 ──

def ensure_mood_file():
    MOOD_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not MOOD_LOG_FILE.exists():
        MOOD_LOG_FILE.write_text(json.dumps({
            "version": 1,
            "history": []
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def log_mood(user_id: str, text: str, mood_id: str = None):
    """记录用户心情到历史"""
    ensure_mood_file()

    # 如果没指定，自动检测
    if mood_id is None:
        mood_id, _, _ = detect_mood(text)

    data = json.loads(MOOD_LOG_FILE.read_text(encoding="utf-8"))

    entry = {
        "user_id": user_id,
        "text": text[:200],
        "mood": mood_id,
        "timestamp": datetime.now().isoformat(),
    }

    data["history"].append(entry)

    # 限制历史条数
    if len(data["history"]) > 1000:
        data["history"] = data["history"][-500:]

    MOOD_LOG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return entry


def get_mood_history(user_id: str, limit: int = 20) -> List[Dict]:
    """获取用户心情历史"""
    ensure_mood_file()
    data = json.loads(MOOD_LOG_FILE.read_text(encoding="utf-8"))

    history = [e for e in data.get("history", []) if e.get("user_id") == user_id]
    return history[-limit:]


def get_mood_stats(user_id: str = None) -> Dict:
    """获取心情统计"""
    ensure_mood_file()
    data = json.loads(MOOD_LOG_FILE.read_text(encoding="utf-8"))

    history = data.get("history", [])
    if user_id:
        history = [e for e in history if e.get("user_id") == user_id]

    mood_counts = {}
    for entry in history:
        mood = entry.get("mood", "neutral")
        mood_counts[mood] = mood_counts.get(mood, 0) + 1

    return {
        "total": len(history),
        "by_mood": mood_counts,
        "dominant_mood": max(mood_counts, key=mood_counts.get) if mood_counts else "neutral",
    }


# ── CLI ──

def cmd_detect(args):
    text = " ".join(args.text) if isinstance(args.text, list) else args.text
    result = detect_mood_with_intensity(text)

    config = result["config"]
    print(f"\n检测结果：{config['emoji']} {config['label']}")
    print(f"语气风格：{config['tone']}")
    print(f"响应策略：{config['response_strategy']}")
    if result["intensity"] > 1:
        print(f"信号强度：{result['intensity']}（检测到 {len(result['signals'])} 个情绪信号）")
    print()
    for sig in result["signals"]:
        print(f"  [{sig['mood']}] {sig['pattern']} → {sig['matched_text']}")


def cmd_respond(args):
    response = generate_response(args.mood, args.context or "")
    print(f"\n{response}")


def cmd_log(args):
    entry = log_mood(args.user, args.text, args.mood)
    print(f"✅ 已记录心情：{entry['mood']}")


def cmd_stats(args):
    stats = get_mood_stats(args.user)
    print(f"\n📊 心情统计（{'用户 ' + args.user if args.user else '全部用户'}）：")
    print(f"   总记录：{stats['total']}")
    print(f"   主要心情：{stats['dominant_mood']}")
    print(f"\n   分布：")
    for mood, count in sorted(stats["by_mood"].items(), key=lambda x: x[1], reverse=True):
        config = MOOD_CONFIGS.get(mood, MOOD_CONFIGS["neutral"])
        bar = "█" * count + "░" * max(0, 20 - count)
        print(f"   {config['emoji']} {config['label']:8s} {bar} {count}")


def main():
    parser = argparse.ArgumentParser(description="心情检测系统")
    sub = parser.add_subparsers(dest="cmd", help="子命令")

    p_detect = sub.add_parser("detect", help="检测心情")
    p_detect.add_argument("text", nargs="+", help="要检测的文本")
    p_detect.add_argument("--raw", action="store_true", help="原始模式")

    p_respond = sub.add_parser("respond", help="生成响应")
    p_respond.add_argument("--mood", required=True, choices=list(MOOD_CONFIGS.keys()))
    p_respond.add_argument("--context", help="上下文")

    p_log = sub.add_parser("log", help="记录心情")
    p_log.add_argument("user", help="用户 ID")
    p_log.add_argument("text", help="用户消息")
    p_log.add_argument("--mood", help="心情（不填则自动检测）")

    p_stats = sub.add_parser("stats", help="心情统计")
    p_stats.add_argument("--user", default=None, help="用户 ID")

    args = parser.parse_args()

    if args.cmd == "detect":
        cmd_detect(args)
    elif args.cmd == "respond":
        cmd_respond(args)
    elif args.cmd == "log":
        cmd_log(args)
    elif args.cmd == "stats":
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
