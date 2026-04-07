#!/usr/bin/env python3
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
"""
Feature Flags 系统
控制功能开关，支持灰度发布和实验性功能

用法：
  python3 scripts/feature_flags.py list
  python3 scripts/feature_flags.py enable dream_mode
  python3 scripts/feature_flags.py disable experimental_feature
  python3 scripts/feature_flags.py check dream_mode
  python3 scripts/feature_flags.py add MY_FEATURE --status testing --description "新功能"
"""
import json
import pathlib
import sys
from typing import Dict, Optional, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

BASE = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = BASE / "workspace"
CONFIG_DIR = WORKSPACE / "data"
FLAG_FILE = CONFIG_DIR / "feature_flags.json"


# ── 功能状态枚举 ──

class FlagStatus(Enum):
    ENABLED = "enabled"       # 正式启用
    DISABLED = "disabled"     # 已禁用
    TESTING = "testing"       # 测试中
    COMING_SOON = "coming_soon"  # 即将发布
    EXPERIMENTAL = "experimental"  # 实验性
    DEPRECATED = "deprecated" # 已废弃


STATUS_LABELS = {
    FlagStatus.ENABLED: "✅ 启用",
    FlagStatus.DISABLED: "❌ 禁用",
    FlagStatus.TESTING: "🧪 测试中",
    FlagStatus.COMING_SOON: "🚧 即将发布",
    FlagStatus.EXPERIMENTAL: "🔬 实验性",
    FlagStatus.DEPRECATED: "📦 已废弃",
}


@dataclass
class FeatureFlag:
    """功能标记定义"""
    name: str
    status: str  # enabled/disabled/testing/coming_soon/experimental/deprecated
    description: str
    tags: List[str] = field(default_factory=list)
    enabled_by: str = ""
    disabled_by: str = ""
    enabled_at: str = ""
    disabled_at: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict = field(default_factory=dict)

    def is_active(self) -> bool:
        return self.status == "enabled"

    def is_visible(self) -> bool:
        """是否对用户可见"""
        return self.status not in ("deprecated",)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "status": self.status,
            "status_label": STATUS_LABELS.get(FlagStatus(self.status), self.status),
            "description": self.description,
            "tags": self.tags,
            "enabled_by": self.enabled_by,
            "disabled_by": self.disabled_by,
            "enabled_at": self.enabled_at,
            "disabled_at": self.disabled_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ── 默认功能标记 ──

DEFAULT_FLAGS: Dict[str, FeatureFlag] = {
    # 已启用
    "dream_mode": FeatureFlag(
        name="dream_mode",
        status="enabled",
        description="记忆整合引擎 — 当 Agent 闲置时自动整理分散的记忆碎片",
        tags=["memory", "automation", "core"],
        created_at=datetime.now().isoformat(),
    ),
    "kairos": FeatureFlag(
        name="kairos",
        status="enabled",
        description="KAIROS 自主运行 — Cron 调度 + GitHub Webhook 监听",
        tags=["automation", "cron", "webhook", "core"],
        created_at=datetime.now().isoformat(),
    ),
    "buddy_system": FeatureFlag(
        name="buddy_system",
        status="enabled",
        description="Buddy 宠物陪伴 — ASCII 宠物互动和评论系统",
        tags=["fun", "companion", "core"],
        created_at=datetime.now().isoformat(),
    ),
    "toolset": FeatureFlag(
        name="toolset",
        status="enabled",
        description="扩展工具集 — Grep/Glob/Todo/Rank",
        tags=["tools", "core"],
        created_at=datetime.now().isoformat(),
    ),
    "mood_detection": FeatureFlag(
        name="mood_detection",
        status="enabled",
        description="心情检测 — Regex 匹配用户情绪，调整响应策略",
        tags=["ux", "core"],
        created_at=datetime.now().isoformat(),
    ),

    # 测试中
    "contextual_buddy_comments": FeatureFlag(
        name="contextual_buddy_comments",
        status="testing",
        description="上下文感知宠物评论 — 基于对话上下文生成更相关的宠物评论",
        tags=["buddy", "ai", "experimental"],
        created_at=datetime.now().isoformat(),
    ),
    "feature_flags_system": FeatureFlag(
        name="feature_flags_system",
        status="enabled",
        description="Feature Flags 系统本身",
        tags=["system", "core"],
        created_at=datetime.now().isoformat(),
    ),

    # 即将发布
    "repl_mode": FeatureFlag(
        name="repl_mode",
        status="coming_soon",
        description="REPL 交互模式 — 交互式命令行界面",
        tags=["ui", "experimental"],
        created_at=datetime.now().isoformat(),
    ),
    "screenshot_analysis": FeatureFlag(
        name="screenshot_analysis",
        status="coming_soon",
        description="截图分析 — 分析屏幕截图提取信息",
        tags=["vision", "experimental"],
        created_at=datetime.now().isoformat(),
    ),

    # 实验性
    "voice_mode": FeatureFlag(
        name="voice_mode",
        status="experimental",
        description="语音模式 — 语音输入输出",
        tags=["voice", "experimental"],
        created_at=datetime.now().isoformat(),
    ),
    "undercover_mode": FeatureFlag(
        name="undercover_mode",
        status="experimental",
        description="隐身模式 — 在公开场合自动隐藏内部实现细节",
        tags=["privacy", "experimental"],
        created_at=datetime.now().isoformat(),
    ),

    # 已废弃
    "old_gacha": FeatureFlag(
        name="old_gacha",
        status="deprecated",
        description="旧版宠物抽卡系统（已由 buddy_system 替代）",
        tags=["legacy", "deprecated"],
        created_at=datetime.now().isoformat(),
    ),
}


# ── 功能管理器 ──

class FeatureManager:
    def __init__(self):
        self._flags: Dict[str, FeatureFlag] = {}
        self._hooks: Dict[str, List[Callable]] = {}  # 状态变更钩子
        self._load()

    def _load(self):
        """从文件加载"""
        if FLAG_FILE.exists():
            try:
                data = json.loads(FLAG_FILE.read_text(encoding="utf-8"))
                flags_data = data.get("flags", {})
                for name, fd in flags_data.items():
                    self._flags[name] = FeatureFlag(**fd)
            except Exception:
                self._flags = {}
        else:
            self._flags = {}

        # 合并默认标记
        for name, default_flag in DEFAULT_FLAGS.items():
            if name not in self._flags:
                self._flags[name] = default_flag
            else:
                # 更新元数据
                self._flags[name].description = default_flag.description
                self._flags[name].tags = default_flag.tags
                self._flags[name].updated_at = datetime.now().isoformat()

    def _save(self):
        """保存到文件"""
        FLAG_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "updated_at": datetime.now().isoformat(),
            "flags": {name: flag.__dict__ for name, flag in self._flags.items()},
        }
        FLAG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def is_enabled(self, name: str) -> bool:
        """检查功能是否启用"""
        flag = self._flags.get(name)
        if not flag:
            return False
        return flag.is_active()

    def get_status(self, name: str) -> Optional[str]:
        """获取功能状态"""
        flag = self._flags.get(name)
        return flag.status if flag else None

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """获取功能标记"""
        return self._flags.get(name)

    def list_flags(self, filter_tag: str = None,
                   filter_status: str = None) -> List[FeatureFlag]:
        """列出所有功能"""
        flags = list(self._flags.values())

        if filter_tag:
            flags = [f for f in flags if filter_tag in f.tags]

        if filter_status:
            flags = [f for f in flags if f.status == filter_status]

        return sorted(flags, key=lambda f: f.name)

    def enable(self, name: str, operator: str = "system") -> bool:
        """启用功能"""
        flag = self._flags.get(name)
        if not flag:
            return False

        old_status = flag.status
        flag.status = "enabled"
        flag.enabled_by = operator
        flag.enabled_at = datetime.now().isoformat()
        flag.updated_at = datetime.now().isoformat()

        self._save()
        self._trigger_hook(name, old_status, "enabled")
        return True

    def disable(self, name: str, operator: str = "system") -> bool:
        """禁用功能"""
        flag = self._flags.get(name)
        if not flag:
            return False

        old_status = flag.status
        flag.status = "disabled"
        flag.disabled_by = operator
        flag.disabled_at = datetime.now().isoformat()
        flag.updated_at = datetime.now().isoformat()

        self._save()
        self._trigger_hook(name, old_status, "disabled")
        return True

    def set_status(self, name: str, status: str, operator: str = "system") -> bool:
        """设置功能状态"""
        if status not in [s.value for s in FlagStatus]:
            return False

        flag = self._flags.get(name)
        if not flag:
            return False

        old_status = flag.status
        flag.status = status
        flag.updated_at = datetime.now().isoformat()

        if status == "enabled":
            flag.enabled_by = operator
            flag.enabled_at = datetime.now().isoformat()
        elif old_status == "enabled":
            flag.disabled_by = operator
            flag.disabled_at = datetime.now().isoformat()

        self._save()
        self._trigger_hook(name, old_status, status)
        return True

    def add_flag(self, name: str, description: str = "",
                 status: str = "disabled",
                 tags: List[str] = None,
                 operator: str = "system") -> bool:
        """添加新功能标记"""
        if name in self._flags:
            return False

        self._flags[name] = FeatureFlag(
            name=name,
            status=status,
            description=description,
            tags=tags or [],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        self._save()
        return True

    def remove_flag(self, name: str) -> bool:
        """删除功能标记"""
        if name not in self._flags:
            return False
        del self._flags[name]
        self._save()
        return True

    def register_hook(self, name: str, callback: Callable):
        """注册状态变更钩子"""
        if name not in self._hooks:
            self._hooks[name] = []
        self._hooks[name].append(callback)

    def _trigger_hook(self, name: str, old_status: str, new_status: str):
        """触发状态变更钩子"""
        callbacks = self._hooks.get(name, [])
        callbacks += self._hooks.get("*", [])  # 全局钩子
        for cb in callbacks:
            try:
                cb(name, old_status, new_status)
            except Exception as e:
                pass  # 钩子执行失败不影响主流程


# 全局实例
_manager: Optional[FeatureManager] = None


def get_manager() -> FeatureManager:
    global _manager
    if _manager is None:
        _manager = FeatureManager()
    return _manager


# 便捷函数

def is_enabled(name: str) -> bool:
    """检查功能是否启用"""
    return get_manager().is_enabled(name)


def check(name: str) -> Dict:
    """检查功能状态"""
    manager = get_manager()
    flag = manager.get_flag(name)
    if not flag:
        return {"exists": False, "enabled": False}
    return {
        "exists": True,
        "enabled": flag.is_active(),
        "status": flag.status,
        "status_label": STATUS_LABELS.get(FlagStatus(flag.status), flag.status),
        "description": flag.description,
    }


# ── CLI ──

def cmd_list(args):
    manager = get_manager()
    flags = manager.list_flags(filter_tag=args.tag, filter_status=args.status)

    print(f"\n📋 功能标记列表（共 {len(flags)} 个）：\n")

    # 按状态分组
    by_status = {}
    for flag in flags:
        if flag.status not in by_status:
            by_status[flag.status] = []
        by_status[flag.status].append(flag)

    for status in ["enabled", "testing", "experimental", "coming_soon", "disabled", "deprecated"]:
        flags_in_status = by_status.get(status, [])
        if not flags_in_status:
            continue
        label = STATUS_LABELS.get(FlagStatus(status), status)
        print(f"{label}（{len(flags_in_status)}）：")
        for flag in flags_in_status:
            tags_str = f" [{', '.join(flag.tags)}]" if flag.tags else ""
            print(f"  • {flag.name}{tags_str}")
            print(f"    {flag.description}")
        print()


def cmd_check(args):
    result = check(args.flag)
    if not result["exists"]:
        print(f"❌ 功能不存在：{args.flag}")
        return

    flag = get_manager().get_flag(args.flag)
    print(f"\n🔍 检查：{args.flag}")
    print(f"   状态：{result['status_label']}")
    print(f"   启用：{'是' if result['enabled'] else '否'}")
    print(f"   描述：{result['description']}")
    if flag.enabled_at:
        print(f"   启用于：{flag.enabled_at}")
    if flag.disabled_at:
        print(f"   禁用于：{flag.disabled_at}")


def cmd_enable(args):
    ok = get_manager().enable(args.flag, operator=args.operator or "cli")
    print(f"{'✅ 已启用' if ok else '❌ 启用失败'}：{args.flag}")


def cmd_disable(args):
    ok = get_manager().disable(args.flag, operator=args.operator or "cli")
    print(f"{'✅ 已禁用' if ok else '❌ 禁用失败'}：{args.flag}")


def cmd_set(args):
    ok = get_manager().set_status(args.flag, args.status, operator=args.operator or "cli")
    print(f"{'✅ 状态已更新' if ok else '❌ 更新失败'}：{args.flag} → {args.status}")


def cmd_add(args):
    ok = get_manager().add_flag(
        name=args.name,
        description=args.description or "",
        status=args.status or "disabled",
        tags=args.tag or [],
        operator=args.operator or "cli",
    )
    print(f"{'✅ 已添加' if ok else '❌ 添加失败'}：{args.name}")


def cmd_remove(args):
    ok = get_manager().remove_flag(args.name)
    print(f"{'✅ 已删除' if ok else '❌ 删除失败'}：{args.name}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Feature Flags 管理")
    sub = parser.add_subparsers(dest="cmd", help="子命令")

    p_list = sub.add_parser("list", help="列出所有功能")
    p_list.add_argument("--tag", help="按标签过滤")
    p_list.add_argument("--status", help="按状态过滤")
    p_check = sub.add_parser("check", help="检查功能")
    p_check.add_argument("flag", help="功能名称")
    p_enable = sub.add_parser("enable", help="启用功能")
    p_enable.add_argument("flag", help="功能名称")
    p_enable.add_argument("--operator")
    p_disable = sub.add_parser("disable", help="禁用功能")
    p_disable.add_argument("flag", help="功能名称")
    p_disable.add_argument("--operator")

    p_set = sub.add_parser("set", help="设置状态")
    p_set.add_argument("flag", help="功能名称")
    p_set.add_argument("status", help="状态")
    p_set.add_argument("--operator")

    p_add = sub.add_parser("add", help="添加功能")
    p_add.add_argument("name", help="功能名称")
    p_add.add_argument("--description", help="描述")
    p_add.add_argument("--status", default="disabled", help="初始状态")
    p_add.add_argument("--tag", action="append", help="标签")
    p_add.add_argument("--operator")
    p_remove = sub.add_parser("remove", help="删除功能")
    p_remove.add_argument("name", help="功能名称")

    args = parser.parse_args()

    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "check":
        cmd_check(args)
    elif args.cmd == "enable":
        cmd_enable(args)
    elif args.cmd == "disable":
        cmd_disable(args)
    elif args.cmd == "set":
        cmd_set(args)
    elif args.cmd == "add":
        cmd_add(args)
    elif args.cmd == "remove":
        cmd_remove(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
