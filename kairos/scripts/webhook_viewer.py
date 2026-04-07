#!/usr/bin/env python3
"""
本地 Webhook 调试器
监听端口，实时在浏览器显示所有收到的请求
不用 ngrok、不用公网，纯粹本地调试 GitHub Webhook

用法：
  python3 scripts/webhook_viewer.py
  然后打开 http://localhost:7893 查看实时请求
"""
import json
import datetime
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import threading
import os

PORT = 7893
requests_log = []
log_lock = threading.Lock()
running = True


def log_request(method, path, headers, body, client_ip):
    with log_lock:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        req = {
            "ts": ts,
            "method": method,
            "path": path,
            "ip": client_ip,
            "event": headers.get("X-GitHub-Event", ""),
            "delivery": headers.get("X-GitHub-Delivery", ""),
            "headers": dict(headers),
            "body": body[:2000] if body else "",
        }
        requests_log.insert(0, req)
        if len(requests_log) > 50:
            requests_log.pop()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # 静默

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = self._build_html()
            self.wfile.write(html.encode("utf-8"))
        elif self.path == "/api/requests":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            with log_lock:
                self.wfile.write(json.dumps({"requests": requests_log}, ensure_ascii=False).encode())
        elif self.path == "/clear":
            with log_lock:
                requests_log.clear()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"cleared")
        else:
            self.send_error(404)

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="replace")

        client_ip = self.client_address[0]
        log_request("POST", self.path, self.headers, body, client_ip)

        # GitHub 签名验证（简单日志）
        sig = self.headers.get("X-Hub-Signature-256", "")
        event = self.headers.get("X-GitHub-Event", "")
        delivery = self.headers.get("X-GitHub-Delivery", "")

        # 发回 GitHub 的响应
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        resp = {
            "ok": True,
            "received": True,
            "event": event,
            "delivery": delivery,
            "logged": True,
        }
        self.wfile.write(json.dumps(resp, ensure_ascii=False).encode())

    def _build_html(self):
        return """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<title>Webhook 调试器</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #0d1117; color: #e6edf3; font-family: 'Segoe UI', monospace; min-height: 100vh; }
  .hdr { background: #161b22; border-bottom: 1px solid #30363d; padding: 14px 20px; display: flex; align-items: center; gap: 16px; }
  .hdr h1 { font-size: 16px; color: #58a6ff; }
  .hdr .info { font-size: 12px; color: #8b949e; }
  .hdr .url { font-size: 11px; color: #3fb950; background: #0d1117; padding: 4px 10px; border-radius: 4px; border: 1px solid #30363d; }
  .btn { background: #21262d; color: #e6edf3; border: 1px solid #30363d; padding: 5px 14px; border-radius: 6px; cursor: pointer; font-size: 12px; }
  .btn:hover { background: #30363d; }
  .grid { display: grid; grid-template-columns: 380px 1fr; gap: 0; height: calc(100vh - 56px); }
  .req-list { border-right: 1px solid #30363d; overflow-y: auto; }
  .req-item { padding: 10px 16px; border-bottom: 1px solid #21262d; cursor: pointer; transition: background 0.1s; }
  .req-item:hover { background: #161b22; }
  .req-item.active { background: #1f2937; border-left: 3px solid #58a6ff; }
  .req-ts { font-size: 10px; color: #8b949e; margin-bottom: 3px; }
  .req-method { font-size: 11px; font-weight: bold; color: #58a6ff; }
  .req-event { font-size: 10px; color: #f78166; margin-left: 6px; }
  .req-path { font-size: 11px; color: #e6edf3; margin-top: 2px; word-break: break-all; }
  .req-ip { font-size: 10px; color: #484f58; margin-top: 2px; }
  .detail { padding: 16px 20px; overflow-y: auto; }
  .empty { color: #484f58; font-size: 13px; padding: 40px; text-align: center; }
  .section { margin-bottom: 20px; }
  .section h3 { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 1px solid #21262d; }
  .kv { display: flex; gap: 8px; margin-bottom: 4px; font-size: 12px; }
  .kv .k { color: #8b949e; min-width: 140px; }
  .kv .v { color: #e6edf3; word-break: break-all; }
  .kv .v.ok { color: #3fb950; }
  .kv .v.warn { color: #d29922; }
  .kv .v.err { color: #f85149; }
  pre { background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 12px; font-size: 11px; color: #e6edf3; white-space: pre-wrap; word-break: break-all; max-height: 400px; overflow-y: auto; line-height: 1.6; }
  .ping { position: fixed; bottom: 16px; right: 16px; font-size: 11px; color: #3fb950; }
  @keyframes dot { 0%, 80%, 100% { opacity: 0; } 40% { opacity: 1; } }
  .live::after { content: ''; display: inline-block; width: 8px; height: 8px; background: #3fb950; border-radius: 50%; margin-left: 6px; animation: dot 1.4s infinite; }
</style>
</head>
<body>
<div class="hdr">
  <h1>🪝 Webhook 调试器</h1>
  <span class="info">本地监听 <span class="url">http://localhost:""" + str(PORT) + """/api/webhook/github</span></span>
  <button class="btn" onclick="clearReqs()">🗑 清空</button>
  <span id="count" class="info"></span>
  <span id="status" class="info live">监听中</span>
</div>
<div class="grid">
  <div class="req-list" id="reqList">
    <div class="empty">暂无请求<br><br>在 GitHub Webhook 设置：<br><code style="font-size:11px">http://localhost:""" + str(PORT) + """/api/webhook/github</code></div>
  </div>
  <div class="detail" id="detail">
    <div class="empty">👈 选择一个请求查看详情</div>
  </div>
</div>
<div class="ping" id="ping">● 实时</div>

<script>
let activeId = null;
let lastTs = 0;

function load() {
  fetch('/api/requests')
    .then(r => r.json())
    .then(d => {
      const list = document.getElementById('reqList');
      const count = document.getElementById('count');
      count.textContent = d.requests.length + ' 个请求';

      if (d.requests.length === 0) {
        list.innerHTML = '<div class="empty">暂无请求</div>';
        return;
      }

      // 只更新有变化的
      const latest = d.requests[0];
      if (!latest || latest.ts === lastTs) return;
      lastTs = latest.ts;

      let html = '';
      for (const r of d.requests) {
        const isActive = activeId === r.delivery;
        html += '<div class="req-item' + (isActive ? ' active' : '') + '" onclick="show(\'' + r.delivery + '\')">\
          <div class="req-ts">' + r.ts + '</div>\
          <div><span class="req-method">' + r.method + '</span><span class="req-event">' + (r.event || '—') + '</span></div>\
          <div class="req-path">' + r.path + '</div>\
          <div class="req-ip">来自 ' + r.ip + '</div>\
        </div>';
      }
      list.innerHTML = html;

      if (activeId) show(activeId);
    });
}

function show(delivery) {
  activeId = delivery;
  const r = document.querySelector('.req-item.active');
  if (r) r.classList.remove('active');
  event && event.currentTarget && event.currentTarget.classList.add('active');

  fetch('/api/requests')
    .then(r => r.json())
    .then(d => {
      const req = d.requests.find(x => x.delivery === delivery);
      if (!req) return;
      const detail = document.getElementById('detail');
      let html = '<div class="section"><h3>基本信息</h3>';
      html += '<div class="kv"><span class="k">时间</span><span class="v">' + req.ts + '</span></div>';
      html += '<div class="kv"><span class="k">方法</span><span class="v ok">' + req.method + '</span></div>';
      html += '<div class="kv"><span class="k">路径</span><span class="v">' + req.path + '</span></div>';
      html += '<div class="kv"><span class="k">来源 IP</span><span class="v">' + req.ip + '</span></div>';
      html += '</div>';

      html += '<div class="section"><h3>GitHub 事件</h3>';
      html += '<div class="kv"><span class="k">X-GitHub-Event</span><span class="v warn">' + (req.event || '无') + '</span></div>';
      html += '<div class="kv"><span class="k">X-GitHub-Delivery</span><span class="v">' + (req.delivery || '无') + '</span></div>';
      html += '<div class="kv"><span class="k">Content-Type</span><span class="v">' + (req.headers['content-type'] || '无') + '</span></div>';
      html += '</div>';

      html += '<div class="section"><h3>Payload (前 2000 字符)</h3>';
      let payload = req.body || '(空)';
      try { payload = JSON.stringify(JSON.parse(payload), null, 2); } catch(e) {}
      html += '<pre>' + escapeHtml(payload) + '</pre></div>';

      detail.innerHTML = html;
    });
}

function clearReqs() {
  fetch('/clear').then(() => { activeId = null; lastTs = 0; load(); });
}

function escapeHtml(s) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

setInterval(load, 1000);
load();
</script>
</body>
</html>"""


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"🪝 Webhook 调试器已启动")
    print(f"   监听端口: {PORT}")
    print(f"   Webhook 端点: http://localhost:{PORT}/api/webhook/github")
    print(f"   调试页面: http://localhost:{PORT}/")
    print(f"\n在 GitHub Webhook 设置 Payload URL 为:")
    print(f"   http://localhost:{PORT}/api/webhook/github")
    print(f"\n按 Ctrl+C 停止\n")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    run_server()
