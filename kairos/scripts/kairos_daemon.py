#!/usr/bin/env python3
"""
KAIROS Daemon — 自主运行后台服务
结合 P1（Cron 调度）和 P2（GitHub Webhook）

功能：
  • Cron 调度：定时心跳检测、定时播报、早报推送
  • Webhook 监听：GitHub PR/Issue 事件自动触发 Agent 审查
  • Dream 集成：闲置时触发记忆整合
  • 健康检测：定时检查各 Agent 状态

启动：
  python3 kairos_daemon.py start [--daemon]
  python3 kairos_daemon.py stop
  python3 kairos_daemon.py status

Webhook 端点：
  POST /api/webhook/github — 接收 GitHub Webhook
  GET  /api/webhook/github/test — 测试端点
"""
import json
import pathlib
import sys
import time
import datetime
import argparse
import threading
import subprocess
import os
import hashlib
import hmac
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Optional, List, Any
import socketserver
import signal

# 路径设置
_BASE = pathlib.Path(__file__).resolve().parent.parent
WORKSPACE = _BASE / "workspace"
DATA = _BASE / "data"
CONFIG_FILE = DATA / "kairos_config.json"
PID_FILE = DATA / "kairos_daemon.pid"
GATEWAY_PORT = 18789
WEBHOOK_PORT = 7893

# 确保目录存在
DATA.mkdir(parents=True, exist_ok=True)

# ── 配置 ──

DEFAULT_CONFIG = {
    "version": 1,
    "enabled": True,
    "daemon": {
        "heartbeatMinutes": 5,  # 心跳检测间隔
        "dreamIdleMinutes": 30,  # 闲置多久后触发 Dream Mode
    },
    "cron": {
        "enabled": True,
        "tasks": [
            {
                "id": "morning-brief",
                "name": "早报推送",
                "schedule": "0 8 * * *",  # 每天 8:00
                "action": "morning-brief",
                "enabled": True,
            },
            {
                "id": "dream-consolidation",
                "name": "记忆整合",
                "schedule": "0 */4 * * *",  # 每 4 小时检查一次
                "action": "dream-check",
                "enabled": True,
            },
            {
                "id": "health-check",
                "name": "健康检测",
                "schedule": "*/10 * * * *",  # 每 10 分钟
                "action": "health-check",
                "enabled": True,
            },
        ],
    },
    "webhook": {
        "enabled": True,
        "port": WEBHOOK_PORT,
        "secret": "",  # GitHub Webhook Secret，留空则不验证
        "github": {
            "enabled": True,
            "events": ["pull_request", "issues", "push"],
            "repos": {},  # repo -> {enabled, agent, action}
        },
    },
    "notifications": {
        "channel": "feishu",
        "webhook": "",
    },
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
    tmp = str(path) + ".tmp"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        pathlib.Path(tmp).unlink(missing_ok=True)
    except Exception:
        pass


def get_config() -> Dict:
    return _read_json(CONFIG_FILE, DEFAULT_CONFIG)


def save_config(config: Dict):
    _write_json(CONFIG_FILE, config)


# ── GitHub Webhook 验证 ──

def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    """验证 GitHub Webhook 签名"""
    if not secret:
        return True  # 未配置 secret 时跳过验证
    if not signature:
        return False
    mac = hmac.new(secret.encode(), payload, hashlib.sha256)
    expected = "sha256=" + mac.hexdigest()
    return hmac.compare_digest(expected, signature)


def parse_github_event(payload: Dict) -> Dict:
    """解析 GitHub Webhook payload"""
    event_type = "unknown"
    action = payload.get("action", "")
    repo = payload.get("repository", {}).get("full_name", "")
    sender = payload.get("sender", {}).get("login", "")

    # PR 事件
    if "pull_request" in payload:
        pr = payload["pull_request"]
        event_type = "pull_request"
        return {
            "event": "pull_request",
            "action": action,
            "repo": repo,
            "sender": sender,
            "title": pr.get("title", ""),
            "number": pr.get("number", 0),
            "url": pr.get("html_url", ""),
            "head": pr.get("head", {}).get("ref", ""),
            "base": pr.get("base", {}).get("ref", ""),
            "state": pr.get("state", ""),
            "merged": pr.get("merged", False),
            "user": pr.get("user", {}).get("login", ""),
        }

    # Issue 事件
    if "issue" in payload:
        issue = payload["issue"]
        event_type = "issues"
        return {
            "event": "issues",
            "action": action,
            "repo": repo,
            "sender": sender,
            "title": issue.get("title", ""),
            "number": issue.get("number", 0),
            "url": issue.get("html_url", ""),
            "state": issue.get("state", ""),
            "labels": [l.get("name", "") for l in issue.get("labels", [])],
            "user": issue.get("user", {}).get("login", ""),
        }

    # Push 事件
    if "ref" in payload and "commits" in payload:
        return {
            "event": "push",
            "action": "push",
            "repo": repo,
            "sender": sender,
            "ref": payload.get("ref", ""),
            "commits_count": len(payload.get("commits", [])),
            "head": payload.get("after", ""),
        }

    return {"event": event_type, "action": action, "repo": repo, "sender": sender}


# ── Agent 调度 ──

def dispatch_agent(agent_id: str, message: str, timeout: int = 120) -> Dict:
    """向指定 Agent 发送消息并获取结果"""
    try:
        result = subprocess.run(
            ["openclaw", "agent", "--agent", agent_id, "-m", message, "--timeout", str(timeout)],
            capture_output=True, text=True, timeout=timeout + 10,
        )
        return {"ok": result.returncode == 0, "stdout": result.stdout[:500], "stderr": result.stderr[:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def trigger_morning_brief() -> Dict:
    """触发早报生成"""
    script = _BASE / "scripts" / "fetch_morning_news.py"
    if script.exists():
        try:
            subprocess.Popen(
                ["python3", str(script), "--force"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            return {"ok": True, "message": "早报生成已触发"}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": False, "error": "脚本不存在"}


def trigger_dream_check() -> Dict:
    """检查 Dream Mode 是否可以触发"""
    sys.path.insert(0, str(_BASE / "scripts"))
    try:
        from dream_mode import check_gates, run_dream_consolidation

        gates = check_gates()
        if gates.get("allGatesPass"):
            result = run_dream_consolidation()
            return {"ok": True, "triggered": True, "result": result}
        else:
            return {"ok": True, "triggered": False, "gates": gates}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def trigger_health_check() -> Dict:
    """健康检测"""
    try:
        # 检查 Gateway 是否在运行
        result = subprocess.run(
            ["openclaw", "gateway", "status"],
            capture_output=True, text=True, timeout=10,
        )
        gateway_ok = result.returncode == 0

        # 检查最近的任务
        tasks_file = DATA / "tasks_source.json"
        tasks = _read_json(tasks_file, [])
        active = [t for t in tasks if t.get("state") not in ("Done", "Cancelled")]

        return {
            "ok": True,
            "gateway": gateway_ok,
            "activeTasks": len(active),
            "checkedAt": now_iso(),
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


# ── Cron 调度器 ──

class CronScheduler:
    def __init__(self, config: Dict):
        self.config = config
        self.running = False
        self._thread = None
        self._last_run: Dict[str, datetime.datetime] = {}

    def _parse_cron_expr(self, expr: str) -> Optional[datetime.time]:
        """简单 Cron 解析（只支持标准格式：分 时 日 月 周）"""
        try:
            parts = expr.strip().split()
            if len(parts) != 5:
                return None
            minute, hour, day, month, weekday = parts

            now = datetime.datetime.now()

            # 解析小时和分钟
            if hour == "*":
                h = None
            else:
                h = int(hour)

            if minute == "*":
                m = None
            else:
                m = int(minute)

            return datetime.time(h or now.hour, m if m is not None else now.minute)
        except Exception:
            return None

    def _should_run(self, task: Dict) -> bool:
        """检查任务是否应该现在运行"""
        if not task.get("enabled", True):
            return False

        schedule = task.get("schedule", "")
        last_run_str = self._last_run.get(task["id"])
        last_run = None
        if last_run_str:
            try:
                last_run = datetime.datetime.fromisoformat(last_run_str)
            except Exception:
                pass

        now = datetime.datetime.now()

        # 简单实现：每分钟检查一次
        # 实际上应该用 cron 表达式精确匹配
        cron_time = self._parse_cron_expr(schedule)
        if not cron_time:
            return False

        if last_run:
            # 检查是否已经运行过
            if (now - last_run).total_seconds() < 60:
                return False

        # 检查时间是否匹配
        if cron_time.hour == now.hour and cron_time.minute == now.minute:
            return True

        return False

    def _run_task(self, task: Dict) -> Dict:
        """执行任务"""
        action = task.get("action", "")
        task_id = task.get("id", "")

        if action == "morning-brief":
            return trigger_morning_brief()
        elif action == "dream-check":
            return trigger_dream_check()
        elif action == "health-check":
            return trigger_health_check()
        else:
            return {"ok": False, "error": f"unknown action: {action}"}

    def _loop(self):
        """调度循环"""
        while self.running:
            try:
                for task in self.config.get("cron", {}).get("tasks", []):
                    if self._should_run(task):
                        result = self._run_task(task)
                        self._last_run[task["id"]] = now_iso()
                        log(f"[Cron] {task.get('name')} -> {result.get('ok', False)}")
            except Exception as e:
                log(f"[Cron] Error: {e}")

            time.sleep(60)  # 每分钟检查一次

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        log("[Cron] 调度器已启动")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)


# ── Webhook 服务器 ──

class WebhookHandler(BaseHTTPRequestHandler):
    config: Dict = {}

    def log_message(self, fmt, *args):
        log(f"[Webhook] {fmt % args}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/healthz":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "kairos-webhook"}).encode())
        elif parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>KAIROS Webhook Server</h1></body></html>")
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path != "/api/webhook/github":
            self.send_error(404)
            return

        # 读取请求体
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        # 验证签名
        signature = self.headers.get("X-Hub-Signature-256", "")
        secret = self.config.get("webhook", {}).get("secret", "")
        if secret and not verify_github_signature(body, signature, secret):
            log("[Webhook] 签名验证失败")
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"signature verification failed")
            return

        # 解析事件类型
        event = self.headers.get("X-GitHub-Event", "unknown")
        delivery_id = self.headers.get("X-GitHub-Delivery", "")

        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        event_data = parse_github_event(payload)
        event_data["gh_event"] = event
        event_data["delivery_id"] = delivery_id

        # 处理事件
        result = self._handle_event(event_data)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "result": result}).encode())

    def _handle_event(self, event_data: Dict) -> Dict:
        """根据事件类型处理"""
        event = event_data.get("event", "")
        action = event_data.get("action", "")
        repo = event_data.get("repo", "")

        # 检查是否配置了该仓库
        repos_config = self.config.get("webhook", {}).get("github", {}).get("repos", {})
        repo_config = repos_config.get(repo, {})

        if not repo_config.get("enabled", False):
            return {"skipped": True, "reason": "repo not configured"}

        # 检查事件类型
        enabled_events = self.config.get("webhook", {}).get("github", {}).get("events", [])
        if event not in enabled_events:
            return {"skipped": True, "reason": f"event {event} not enabled"}

        # 派发 Agent
        agent_id = repo_config.get("agent", "shangshu")
        action_type = repo_config.get("action", "review")

        messages = {
            "pull_request": f"📋 GitHub PR 事件\n仓库: {repo}\n动作: {action}\n标题: {event_data.get('title', '')}\n链接: {event_data.get('url', '')}\n状态: {event_data.get('state', '')}",
            "issues": f"🐛 GitHub Issue 事件\n仓库: {repo}\n动作: {action}\n标题: {event_data.get('title', '')}\n链接: {event_data.get('url', '')}\n标签: {', '.join(event_data.get('labels', []))}",
            "push": f"📤 Push 事件\n仓库: {repo}\n分支: {event_data.get('ref', '')}\n提交数: {event_data.get('commits_count', 0)}",
        }

        message = messages.get(event, f"GitHub {event} 事件: {json.dumps(event_data, ensure_ascii=False)}")
        result = dispatch_agent(agent_id, message)

        return {
            "event": event,
            "repo": repo,
            "agent": agent_id,
            "dispatch": result,
        }


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    allow_reuse_address = True


def start_webhook_server(config: Dict):
    port = config.get("webhook", {}).get("port", WEBHOOK_PORT)
    WebhookHandler.config = config
    server = ThreadedHTTPServer(("0.0.0.0", port), WebhookHandler)
    log(f"[Webhook] 服务器启动于端口 {port}")
    server.serve_forever()


# ── 主进程管理 ──

def get_pid() -> Optional[int]:
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except Exception:
            return None
    return None


def is_running() -> bool:
    pid = get_pid()
    if not pid:
        return False
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True, timeout=5,
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, subprocess.TimeoutExpired):
        return False
    except PermissionError:
        return True  # 有权限但进程不存在


def daemon_start(daemonize: bool = True):
    """启动守护进程"""
    if is_running():
        print("KAIROS 已在运行中 (PID: {})".format(get_pid()))
        return

    config = get_config()

    if daemonize and os.name != "nt":
        # Unix 后台守护
        pid = os.fork()
        if pid > 0:
            print(f"KAIROS 已启动 (PID: {pid})")
            sys.exit(0)
        os.setsid()
    else:
        pid = os.getpid()

    # 写 PID 文件
    PID_FILE.write_text(str(pid))

    # 启动 cron 调度器
    scheduler = CronScheduler(config)
    config["_scheduler"] = scheduler

    # 启动 webhook 服务器（独立线程）
    webhook_thread = threading.Thread(
        target=start_webhook_server, args=(config,), daemon=True
    )
    webhook_thread.start()

    # 启动 cron 调度器
    if config.get("cron", {}).get("enabled", True):
        scheduler.start()

    # 主循环
    try:
        while True:
            time.sleep(10)
            # 保活检查
            if not is_alive(pid):
                break
    except KeyboardInterrupt:
        pass
    finally:
        scheduler.stop()
        PID_FILE.unlink(missing_ok=True)
        log("[KAIROS] 已停止")


def daemon_stop():
    """停止守护进程"""
    pid = get_pid()
    if not pid:
        print("KAIROS 未运行")
        return

    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], timeout=10)
        else:
            os.kill(pid, signal.SIGTERM)
        print(f"KAIROS 已停止 (PID: {pid})")
    except Exception as e:
        print(f"停止失败: {e}")
    finally:
        PID_FILE.unlink(missing_ok=True)


def daemon_status():
    """查看状态"""
    pid = get_pid()
    running = is_running()
    config = get_config()

    print(f"""
╔══════════════════════════════════════════════════════╗
║  🤖 KAIROS 自主运行服务                          ║
╚══════════════════════════════════════════════════════╝

状态: {'🟢 运行中' if running else '🔴 已停止'}
PID:  {pid or '无'}

Cron 任务 ({len(config.get('cron', {}).get('tasks', []))} 个):
""")

    for task in config.get("cron", {}).get("tasks", []):
        status = "✅" if task.get("enabled") else "❌"
        print(f"  {status} [{task.get('id')}] {task.get('name')} — {task.get('schedule')}")

    print(f"""
Webhook 监听:
  端口: {config.get('webhook', {}).get('port', WEBHOOK_PORT)}
  状态: {'✅ 启用' if config.get('webhook', {}).get('enabled') else '❌ 禁用'}

配置的仓库:
""")

    repos = config.get("webhook", {}).get("github", {}).get("repos", {})
    if repos:
        for repo, cfg in repos.items():
            status = "✅" if cfg.get("enabled") else "❌"
            print(f"  {status} {repo} -> {cfg.get('agent', 'shangshu')}")
    else:
        print("  (暂无配置)")


def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def is_alive(pid: int) -> bool:
    try:
        if os.name == "nt":
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True, text=True, timeout=5,
            )
            return str(pid) in result.stdout
        else:
            os.kill(pid, 0)
            return True
    except (ProcessLookupError, PermissionError):
        return False
    except Exception:
        return False


# ── CLI ──

def cmd_start(args):
    if is_running():
        print("KAIROS 已在运行")
        return
    daemon_start(daemonize=not args.foreground)


def cmd_stop(args):
    daemon_stop()


def cmd_status(args):
    daemon_status()


def cmd_config(args):
    """查看/修改配置"""
    config = get_config()

    if args.list:
        print(json.dumps(config, indent=2, ensure_ascii=False))
    elif args.set:
        # 设置配置项，e.g. --set webhook.enabled=true
        parts = args.set.split("=", 1)
        if len(parts) != 2:
            print("用法: --set key=value")
            return
        key, value = parts
        # 简单实现：直接修改顶层
        if value.lower() in ("true", "false"):
            value = value.lower() == "true"
        elif value.isdigit():
            value = int(value)
        config[key] = value
        save_config(config)
        print(f"已设置 {key} = {value}")
    else:
        print(f"""
KAIROS 配置:

启动: python3 kairos_daemon.py start
停止: python3 kairos_daemon.py stop
状态: python3 kairos_daemon.py status
查看配置: python3 kairos_daemon.py config --list
修改配置: python3 kairos_daemon.py config --set key=value

Webhook 端点:
  POST http://localhost:{config.get('webhook', {}).get('port', WEBHOOK_PORT)}/api/webhook/github
  (配置 GitHub Webhook 时填这个 URL)
""")


def cmd_add_repo(args):
    """添加要监听的 GitHub 仓库"""
    config = get_config()
    repos = config.setdefault("webhook", {}).setdefault("github", {}).setdefault("repos", {})
    repos[args.repo] = {
        "enabled": True,
        "agent": args.agent or "shangshu",
        "action": args.action or "review",
    }
    save_config(config)
    print(f"✅ 已添加仓库: {args.repo} -> {args.agent or 'shangshu'}")


def main():
    parser = argparse.ArgumentParser(description="KAIROS 自主运行服务")
    sub = parser.add_subparsers(dest="cmd", help="子命令")

    p_start = sub.add_parser("start", help="启动服务")
    p_start.add_argument("--foreground", "-f", action="store_true", help="前台运行")
    p_start.set_defaults(func=cmd_start)

    p_stop = sub.add_parser("stop", help="停止服务")
    p_stop.set_defaults(func=cmd_stop)

    p_status = sub.add_parser("status", help="查看状态")
    p_status.set_defaults(func=cmd_status)

    p_config = sub.add_parser("config", help="配置管理")
    p_config.add_argument("--list", action="store_true", help="列出配置")
    p_config.add_argument("--set", metavar="key=value", help="设置配置项")
    p_config.set_defaults(func=cmd_config)

    p_add = sub.add_parser("add-repo", help="添加监听仓库")
    p_add.add_argument("repo", help="仓库名 (e.g. myname/myrepo)")
    p_add.add_argument("--agent", default=None, help="派发的 Agent (默认: shangshu)")
    p_add.add_argument("--action", default=None, help="动作类型 (默认: review)")
    p_add.set_defaults(func=cmd_add_repo)

    args = parser.parse_args()

    if args.cmd is None:
        parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
