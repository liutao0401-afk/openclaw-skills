# OpenClaw Skills by @liutao

三个 OpenClaw 技能包，参考 Claude Code 泄漏源码设计。

## 技能包

### 🌙 Dream Mode — 记忆整合引擎
自动化记忆整理，让 Agent 真正"认识"用户。

**标签：** memory, automation, idle, consolidation

### 🤖 KAIROS — 自主运行守护进程
集 Cron 调度 + GitHub Webhook 于一体。

**标签：** automation, cron, webhook, github, daemon, autonomous

### 🐾 Buddy System — ASCII 宠物陪伴
给 OpenClaw 一只灵魂宠物，陪你写代码。

**标签：** fun, companion, pets, ascii, mood, personality

---

## 发布方式

使用 [ClawHub CLI](https://clawhub.ai) 发布：

```bash
# 1. 安装 clawhub（需要 Node.js）
npm install -g clawhub

# 2. 登录
clawhub login

# 3. 发布 Dream Mode
cd dream-mode
clawhub skill publish . --slug dream-mode --name "Dream Mode" --tags memory,automation --changelog "v1.0.0 initial release"

# 4. 发布 KAIROS
cd ../kairos
clawhub skill publish . --slug kairos --name "KAIROS" --tags automation,cron,webhook --changelog "v1.0.0 initial release"

# 5. 发布 Buddy System
cd ../buddy-system
clawhub skill publish . --slug buddy-system --name "Buddy System" --tags fun,companion --changelog "v1.0.0 initial release"
```

## 作者

GitHub: [@liutao](https://github.com/liutao0401)
