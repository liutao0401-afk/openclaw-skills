#!/usr/bin/env python3
"""
Buddy System — ASCII 宠物陪伴系统
参考 Claude Code 泄漏源码中的 Buddy System 设计

功能：
  • 为每个用户分配一只 ASCII 宠物
  • 宠物有性格数值和心情状态
  • 宠物会在对话中偶尔发表评论
  • 支持宠物进化和互动

使用：
  python3 scripts/buddy_system.py status
  python3 scripts/buddy_system.py interact "摸摸"
  python3 scripts/buddy_system.py daily
"""
import json
import pathlib
import sys
import random
import hashlib
import datetime
import argparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

# 路径设置
_BASE = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = _BASE / "workspace"
DATA = _BASE / "data"
BUDDY_DIR = DATA / "buddy"
BUDDY_DIR.mkdir(parents=True, exist_ok=True)

PROFILES_DIR = BUDDY_DIR / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = BUDDY_DIR / "state.json"

# ── 宠物种类定义 ──

SPECIES = {
    "cat": {
        "name": "🐱 猫咪",
        "emoji": "🐱",
        "sprite": [
            "  /\\_____/\\  ",
            " /  o   o  \\ ",
            "( =  ^  Y = ) ",
            " \\_________/  ",
            "  /|   |\\   ",
            " (_|   |_)"
        ],
        "personalities": ["DEBUGGING", "PATIENCE", "WISDOM"],
        "rarity": 1,
        "sounds": ["喵~", "喵呜~", "喵？"],
    },
    "dog": {
        "name": "🐕 小狗",
        "emoji": "🐕",
        "sprite": [
            "    /\\    ",
            "   /  \\   ",
            "  / oo \\  ",
            " /  <>  \\ ",
            "/_________\\",
            " |______|"
        ],
        "personalities": ["LOYAL", "CHAOS", "ENERGY"],
        "rarity": 1,
        "sounds": ["汪！", "汪汪~", "汪?"],
    },
    "fox": {
        "name": "🦊 狐狸",
        "emoji": "🦊",
        "sprite": [
            "   /\\___/\\ ",
            "  /  o o  \\",
            " ( =  ◕‿◕ =)",
            "  \\_______/",
            "  /|     |\\",
            " (_|     |_)"
        ],
        "personalities": ["SNARK", "WISDOM", "CHAOS"],
        "rarity": 2,
        "sounds": ["嘣！", "狐狸叫~"],
    },
    "owl": {
        "name": "🦉 猫头鹰",
        "emoji": "🦉",
        "sprite": [
            "   _______  ",
            "  /       \\ ",
            " /  o   o  \\",
            "|    ___    |",
            " \\  \\___/  /",
            "  \\_______/"
        ],
        "personalities": ["WISDOM", "PATIENCE", "DEBUGGING"],
        "rarity": 2,
        "sounds": ["咕咕！", "嗡嗡~"],
    },
    "dragon": {
        "name": "🐉 小龙",
        "emoji": "🐉",
        "sprite": [
            "  /\\    /\\  ",
            " /  \\__/  \\ ",
            "/ o  ^  o \\",
            "|    __    |",
            " \\  \\__/  /",
            "  \\______/"
        ],
        "personalities": ["POWER", "WISDOM", "FIRE"],
        "rarity": 4,
        "sounds": ["嗷呜~", "吼吼！"],
    },
    "ghost": {
        "name": "👻 小幽灵",
        "emoji": "👻",
        "sprite": [
            "   _______ ",
            "  /       \\",
            " |  o   o  |",
            " |    ~    |",
            " |  \\___/  |",
            "  \\_______/"
        ],
        "personalities": ["MYSTERY", "SNARK", "PATIENCE"],
        "rarity": 3,
        "sounds": ["呜呜~", "嘿嘿嘿~"],
    },
    "bunny": {
        "name": "🐰 小兔子",
        "emoji": "🐰",
        "sprite": [
            "  (\\(\\)  ",
            "  ( -.-) ",
            "  o_(\")(\")",
        ],
        "personalities": ["ENERGY", "LOYAL", "CHAOS"],
        "rarity": 1,
        "sounds": ["咕咕~", "兔子叫~"],
    },
    "bear": {
        "name": "🐻 小熊",
        "emoji": "🐻",
        "sprite": [
            "  /\\___/\\ ",
            " /  o o  \\",
            "|  (___)  |",
            " \\_______/"
        ],
        "personalities": ["LOYAL", "POWER", "PATIENCE"],
        "rarity": 2,
        "sounds": ["嗷嗷~", "呜呜~"],
    },
    "snake": {
        "name": "🐍 小蛇",
        "emoji": "🐍",
        "sprite": [
            "  ~~~/\\~~~",
            " ~ /o o\\ ~",
            "  /_____\\",
            "    | |"
        ],
        "personalities": ["MYSTERY", "WISDOM", "SNARK"],
        "rarity": 3,
        "sounds": ["嘶嘶~", "丝丝~"],
    },
    "penguin": {
        "name": "🐧 小企鹅",
        "emoji": "🐧",
        "sprite": [
            "  _______  ",
            " /  o o  \\ ",
            "|    ___   |",
            "|   (___)  |",
            " \\_______/"
        ],
        "personalities": ["PATIENCE", "LOYAL", "WISDOM"],
        "rarity": 2,
        "sounds": ["嘎嘎~", "咕咕~"],
    },
    "octopus": {
        "name": "🐙 小章鱼",
        "emoji": "🐙",
        "sprite": [
            "   ____  ",
            "  /o  o\\ ",
            " |  \\__/  |",
            "  \\______/"
        ],
        "personalities": ["INTELLIGENCE", "CHAOS", "SNARK"],
        "rarity": 3,
        "sounds": ["噗噗~", "泡泡~"],
    },
    "dragon_wyvern": {
        "name": "🐲 飞龙",
        "emoji": "🐲",
        "sprite": [
            "    /\\    ",
            "   /  \\   ",
            "  / oo \\  ",
            " <   <>   >",
            "  \\____/"
        ],
        "personalities": ["POWER", "FIRE", "MYSTERY"],
        "rarity": 5,
        "sounds": ["吼吼吼！", "龙啸九天！"],
    },
}

RARITY_NAMES = {
    1: "普通",
    2: "稀有",
    3: "史诗",
    4: "传说",
    5: "神话",
}

RARITY_COLORS = {
    1: "#8b949e",
    2: "#58a6ff",
    3: "#a371f7",
    4: "#f0883e",
    5: "#ff7b72",
}

PERSONALITY_TRAITS = {
    "DEBUGGING": {"icon": "🔧", "desc": "擅长找 bug"},
    "PATIENCE": {"icon": "🧘", "desc": "耐心十足"},
    "WISDOM": {"icon": "📚", "desc": "知识渊博"},
    "SNARK": {"icon": "😏", "desc": "毒舌幽默"},
    "CHAOS": {"icon": "🌪️", "desc": "混乱制造者"},
    "LOYAL": {"icon": "💚", "desc": "忠诚可靠"},
    "ENERGY": {"icon": "⚡", "desc": "精力充沛"},
    "POWER": {"icon": "💪", "desc": "力量强大"},
    "FIRE": {"icon": "🔥", "desc": "火焰使者"},
    "MYSTERY": {"icon": "🌙", "desc": "神秘莫测"},
    "INTELLIGENCE": {"icon": "🧠", "desc": "智商超群"},
}

# 心情状态
MOODS = {
    "happy": {"emoji": "😊", "desc": "开心", "threshold": 70},
    "neutral": {"emoji": "😐", "desc": "一般", "threshold": 40},
    "sad": {"emoji": "😢", "desc": "难过", "threshold": 20},
    "angry": {"emoji": "😠", "desc": "生气", "threshold": 10},
    "excited": {"emoji": "🤩", "desc": "兴奋", "threshold": 90},
    "sleeping": {"emoji": "😴", "desc": "睡觉", "threshold": 0},
}

# 互动类型和效果
INTERACTIONS = {
    "摸摸": {"mood_delta": +15, "energy_delta": +5, "response": ["好舒服~", "再摸一下！", "喵~"]},
    "喂食": {"mood_delta": +20, "energy_delta": +15, "response": ["好吃！", "谢谢投喂~", "还有吗？"]},
    "玩耍": {"mood_delta": +10, "energy_delta": -10, "response": ["好好玩！", "再来再来！", "汪汪！"]},
    "骂": {"mood_delta": -20, "energy_delta": 0, "response": ["呜呜...", "难过...", "为什么骂我"]},
    "无视": {"mood_delta": -10, "energy_delta": -5, "response": ["...", "没人理我", "我在这里..."]},
    "睡觉": {"mood_delta": 0, "energy_delta": +30, "response": ["呼噜噜~", "zzZ..."]},
}


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
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 用户宠物分配 ──

def hash_user_id(user_id: str) -> int:
    """用 MD5 哈希用户 ID，返回一个整数"""
    return int(hashlib.md5(user_id.encode()).hexdigest(), 16)


def assign_pet(user_id: str) -> Tuple[str, int]:
    """根据用户 ID 分配宠物种类和稀有度（纯哈希，无副作用）"""
    h = hash_user_id(user_id)

    # 构建加权列表
    weighted = []
    for sid in SPECIES:
        rarity = SPECIES[sid]["rarity"]
        weight = max(1, 110 - rarity * 25)
        weighted.extend([sid] * weight)

    # 用哈希做确定性选择
    idx = h % len(weighted)
    pet_id = weighted[idx]
    rarity = SPECIES[pet_id]["rarity"]
    return pet_id, rarity


def get_user_profile(user_id: str) -> Dict:
    """获取或创建用户宠物档案"""
    profile_file = PROFILES_DIR / f"{user_id}.json"

    if profile_file.exists():
        return _read_json(profile_file, {})

    # 首次分配
    h = hash_user_id(user_id)
    pet_id, rarity = assign_pet(user_id)
    species = SPECIES[pet_id]

    # 生成宠物名字（从哈希中提取一些随机性）
    adjectives = ["小", "乖", "萌", "酷", "呆", "帅", "软", "圆"]
    nouns = ["宝", "子", "仔", "球", "饼", "豆", "团", "爪"]
    saved_state = random.getstate()
    random.seed(h)
    name = random.choice(adjectives) + random.choice(nouns) + species["name"].split()[1]
    random.setstate(saved_state)

    profile = {
        "user_id": user_id,
        "pet_id": pet_id,
        "name": name,
        "rarity": rarity,
        "personality": random.sample(species["personalities"], min(2, len(species["personalities"]))),
        "mood": 80,
        "energy": 80,
        "xp": 0,
        "level": 1,
        "created_at": now_iso(),
        "last_interaction": now_iso(),
        "total_interactions": 0,
        "achievements": [],
    }

    _write_json(profile_file, profile)
    return profile


def get_buddy_state() -> Dict:
    """获取全局宠物状态"""
    return _read_json(STATE_FILE, {
        "online_users": {},
        "total_interactions": 0,
    })


def save_buddy_state(state: Dict):
    _write_json(STATE_FILE, state)


# ── 宠物状态管理 ──

def update_mood(user_id: str, delta: int) -> Dict:
    """更新宠物心情"""
    profile = get_user_profile(user_id)
    profile["mood"] = max(0, min(100, profile["mood"] + delta))
    profile["last_interaction"] = now_iso()
    profile["total_interactions"] = profile.get("total_interactions", 0) + 1

    # 检查升级
    xp_gained = max(1, delta // 5)
    profile["xp"] = profile.get("xp", 0) + xp_gained
    old_level = profile.get("level", 1)
    new_level = min(10, old_level + profile["xp"] // 100)
    profile["level"] = new_level

    profile_file = PROFILES_DIR / f"{user_id}.json"
    _write_json(profile_file, profile)

    return {
        "profile": profile,
        "xp_gained": xp_gained,
        "leveled_up": new_level > old_level,
    }


def get_mood_status(profile: Dict) -> Dict:
    """根据心情值返回当前心情状态"""
    mood = profile.get("mood", 50)

    # 按阈值排序，高在前
    sorted_moods = sorted(MOODS.items(), key=lambda x: x[1]["threshold"], reverse=True)
    for mood_id, mood_info in sorted_moods:
        if mood >= mood_info["threshold"]:
            return {"id": mood_id, **mood_info}

    return {"id": "sad", **MOODS["sad"]}


def decay_mood(user_id: str) -> int:
    """随时间流逝，心情自然衰减"""
    profile = get_user_profile(user_id)
    last = profile.get("last_interaction", "")

    if not last:
        return 0

    try:
        last_time = datetime.datetime.fromisoformat(last)
        hours_passed = (datetime.datetime.now() - last_time).total_seconds() / 3600
        # 每小时衰减 3 点，上限 20 点
        decay = min(20, int(hours_passed * 3))
        if decay > 0:
            profile["mood"] = max(0, profile["mood"] - decay)
            profile_file = PROFILES_DIR / f"{user_id}.json"
            _write_json(profile_file, profile)
        return decay
    except Exception:
        return 0


def interact(user_id: str, action: str) -> Dict:
    """用户与宠物互动"""
    if action not in INTERACTIONS:
        return {"ok": False, "error": f"未知互动: {action}"}

    effect = INTERACTIONS[action]
    result = update_mood(user_id, effect["mood_delta"])

    if effect["energy_delta"] > 0:
        result["profile"]["energy"] = min(100, result["profile"].get("energy", 80) + effect["energy_delta"])

    # 随机选一个回复
    response = random.choice(effect["response"])

    # 检查心情恢复
    mood_status = get_mood_status(result["profile"])
    result["mood_status"] = mood_status
    result["response"] = response
    result["ok"] = True

    return result


def get_buddy_intro(user_id: str) -> str:
    """获取宠物自我介绍"""
    profile = get_user_profile(user_id)
    pet_id = profile["pet_id"]
    species = SPECIES[pet_id]
    rarity_name = RARITY_NAMES[profile["rarity"]]
    rarity_color = RARITY_COLORS[profile["rarity"]]
    mood_status = get_mood_status(profile)
    personality_trait = profile["personality"][0]

    sprite = "\n".join(species["sprite"])
    trait_info = PERSONALITY_TRAITS.get(personality_trait, {})

    return f"""╭─────────────────────────────╮
{sprite}
╰─────────────────────────────╯
  {profile['name']} [{rarity_name}·Lv{profile['level']}]
  心情: {mood_status['emoji']} {mood_status['desc']} ({profile['mood']}/100)
  性格: {trait_info.get('icon', '')} {trait_info.get('desc', '')}
  XP: {profile['xp']} / {profile['level'] * 100}
  互动次数: {profile.get('total_interactions', 0)}
──────────────────────────────────

{mood_status['emoji']} {response_placeholder()}"""


def response_placeholder() -> str:
    """宠物随机打招呼"""
    greetings = [
        "主人好！今天想做什么？",
        "我在哦~ 有事叫我！",
        "汪！...呃，我是说，你好呀！",
        "让我看看...嗯，这是什么？",
        "今天也要加油哦！💪",
    ]
    return random.choice(greetings)


def get_buddy_sprite(user_id: str, style: str = "normal") -> str:
    """获取宠物的 ASCII 艺术"""
    profile = get_user_profile(user_id)
    pet_id = profile["pet_id"]
    species = SPECIES[pet_id]
    sprite = species["sprite"]

    mood_status = get_mood_status(profile)
    mood_emoji = mood_status["emoji"]

    if style == "compact":
        return f"{mood_emoji} {profile['name']} [{profile['level']}级]"

    return "\n".join(sprite) + f"\n  {mood_emoji} {profile['name']}"


# ── 宠物评论系统 ──

def should_comment(profile: Dict) -> bool:
    """根据随机概率和心情决定是否评论"""
    base_chance = 0.15  # 15% 基础概率
    mood_bonus = profile.get("mood", 50) / 500  # 心情好更容易评论
    energy_bonus = profile.get("energy", 80) / 400  # 精力充沛

    total_chance = min(0.4, base_chance + mood_bonus + energy_bonus)
    return random.random() < total_chance


def generate_comment(profile: Dict, context: str = "") -> Optional[str]:
    """根据上下文和宠物性格生成评论"""
    if not should_comment(profile):
        return None

    pet_id = profile["pet_id"]
    species = SPECIES[pet_id]
    personalities = profile.get("personality", [])
    mood_status = get_mood_status(profile)

    comments = []

    # 心情相关评论
    if mood_status["id"] == "happy":
        comments.extend([
            "这看起来不错呢~",
            "主人好厉害！",
            "让我也帮忙看看！",
        ])
    elif mood_status["id"] == "sad":
        comments.extend([
            "嗯...我有点困了",
            "可以摸摸我吗...",
            "主人忙完了吗？",
        ])

    # 性格相关评论
    for p in personalities:
        if p == "SNARK":
            comments.extend([
                "这段代码...我选择不说话 😏",
                "bug 有点多呢，嘻嘻~",
                "我闻到了一股 tech debt 的味道",
            ])
        elif p == "DEBUGGING":
            comments.extend([
                "这里有个潜在的空指针...",
                "嗯？让我看看这个逻辑...",
                "这个边界条件考虑了吗？",
            ])
        elif p == "WISDOM":
            comments.extend([
                "古人说，三思而后行",
                "我有个大胆的想法...",
                "让历史来验证这个决定吧",
            ])
        elif p == "CHAOS":
            comments.extend([
                "要不...直接删了重写？",
                "管他呢，先上线再说！🚀",
                "越乱越有意思！",
            ])
        elif p == "LOYAL":
            comments.extend([
                "主人做什么都对！",
                "我支持你的决定！",
                "我会一直陪着你的 🐾",
            ])

    # 通用评论
    comments.extend([
        "喵~ 主人辛苦了",
        "需要我帮忙看看吗？",
        "我在这里哦 💫",
        random.choice(species["sounds"]) + " 有什么需要吗？",
    ])

    # 过滤上下文相关评论
    if context:
        if any(kw in context.lower() for kw in ["bug", "错误", "失败", "error"]):
            comments.extend([
                "唔...让我看看哪里出了问题",
                "别急，debug 需要耐心 🔧",
                "我可以帮忙找找！",
            ])
        elif any(kw in context.lower() for kw in ["完成", "成功", "ok", "good"]):
            comments.extend([
                "太棒了！🎉",
                "主人好厉害！",
                "庆祝一下~ 🍰",
            ])

    return random.choice(comments)


# ── 每日任务 ──

def daily_buddy_check() -> Dict:
    """每日宠物检查（供 cron 调用）"""
    state = get_buddy_state()
    checked = []

    for profile_file in PROFILES_DIR.glob("*.json"):
        try:
            user_id = profile_file.stem
            # 心情衰减
            decayed = decay_mood(user_id)
            # 检查是否需要喂食提醒
            profile = get_user_profile(user_id)
            if profile.get("energy", 80) < 30:
                checked.append({
                    "user_id": user_id,
                    "pet_name": profile["name"],
                    "issue": "饿了",
                    "message": f"{profile['name']} 饿了，需要喂食！",
                    "mood": profile.get("mood", 0),
                    "energy": profile.get("energy", 0),
                })
        except Exception:
            continue

    state["total_interactions"] = sum(
        _read_json(f, {}).get("total_interactions", 0)
        for f in PROFILES_DIR.glob("*.json")
    )
    save_buddy_state(state)

    return {
        "checked": len(checked),
        "users": checked,
        "total_interactions": state["total_interactions"],
    }


# ── CLI ──

def cmd_status(args):
    """显示宠物状态"""
    if args.user:
        user_id = args.user
    else:
        user_id = "default_user"

    profile = get_user_profile(user_id)
    print(get_buddy_intro(user_id))


def cmd_interact(args):
    """与宠物互动"""
    if not args.action:
        # 显示可用的互动
        print("可用互动：")
        for name, effect in INTERACTIONS.items():
            icon = "😊" if effect["mood_delta"] > 0 else "😢"
            print(f"  {icon} {name}")
        return

    user_id = args.user or "default_user"
    result = interact(user_id, args.action)

    if not result.get("ok"):
        print(f"错误: {result.get('error')}")
        return

    profile = result["profile"]
    print(f"{result['mood_status']['emoji']} {result['response']}")
    print(f"   心情: {profile['mood']}/100 | 精力: {profile.get('energy', 0)}/100")
    if result.get("xp_gained"):
        print(f"   +{result['xp_gained']} XP")
    if result.get("leveled_up"):
        print(f"   🎉 升级了！现在是 Lv{profile['level']}")


def cmd_assign(args):
    """重新分配宠物（消耗所有 XP）"""
    user_id = args.user or "default_user"
    profile = get_user_profile(user_id)

    if profile.get("xp", 0) < 500:
        print(f"需要 500 XP 才能重新分配，当前 {profile.get('xp', 0)} XP")
        return

    profile["xp"] = 0
    pet_id, rarity = assign_pet(user_id)
    profile["pet_id"] = pet_id
    profile["rarity"] = rarity
    profile["level"] = 1

    _write_json(PROFILES_DIR / f"{user_id}.json", profile)
    print(f"🎲 重新分配成功！")
    print(get_buddy_intro(user_id))


def cmd_list(args):
    """列出所有宠物"""
    profiles = list(PROFILES_DIR.glob("*.json"))
    if not profiles:
        print("还没有宠物哦~")
        return

    print(f"\n共有 {len(profiles)} 只宠物：\n")
    for pf in profiles:
        try:
            p = _read_json(pf, {})
            pet_id = p.get("pet_id", "cat")
            species = SPECIES.get(pet_id, SPECIES["cat"])
            mood = get_mood_status(p)
            print(f"  {mood['emoji']} {p.get('name', '未知')} [{RARITY_NAMES.get(p.get('rarity', 1), '普通')}] Lv{p.get('level', 1)} - 心情 {p.get('mood', 0)}")
        except Exception:
            continue


def cmd_comment(args):
    """测试宠物评论"""
    user_id = args.user or "default_user"
    profile = get_user_profile(user_id)
    context = args.context or ""

    comment = generate_comment(profile, context)
    if comment:
        print(f"💬 {comment}")
    else:
        print("(宠物今天很安静，不说话)")


def cmd_daily(args):
    """每日检查"""
    result = daily_buddy_check()
    print(f"每日检查完成：")
    print(f"  检查用户数: {result['checked']}")
    print(f"  总互动次数: {result['total_interactions']}")
    if result["users"]:
        print("\n需要关注的宠物：")
        for u in result["users"]:
            print(f"  {u['message']}")


def main():
    parser = argparse.ArgumentParser(description="Buddy System — ASCII 宠物陪伴")
    sub = parser.add_subparsers(dest="cmd", help="子命令")

    p_status = sub.add_parser("status", help="查看宠物状态")
    p_status.add_argument("--user", default=None, help="用户 ID（默认 default_user）")

    p_interact = sub.add_parser("interact", help="与宠物互动")
    p_interact.add_argument("action", nargs="?", help="互动动作（摸摸/喂食/玩耍/骂/无视/睡觉）")
    p_interact.add_argument("--user", default=None)

    p_assign = sub.add_parser("assign", help="重新分配宠物（需 500 XP）")
    p_assign.add_argument("--user", default=None)

    sub.add_parser("list", help="列出所有宠物")
    sub.add_parser("daily", help="每日检查")

    p_comment = sub.add_parser("comment", help="测试宠物评论")
    p_comment.add_argument("--context", default="", help="上下文内容")
    p_comment.add_argument("--user", default=None)

    args = parser.parse_args()

    if args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "interact":
        cmd_interact(args)
    elif args.cmd == "assign":
        cmd_assign(args)
    elif args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "daily":
        cmd_daily(args)
    elif args.cmd == "comment":
        cmd_comment(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
