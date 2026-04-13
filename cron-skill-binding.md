---
name: cron-skill-binding
description: Cron Skill 绑定系统 — 技能自注册定时任务 + cron job 挂载技能的完整机制
version: 1.0.0
platforms: [windows, linux, darwin]
author: hermes-inspired
created: 2026-04-13
tags: [cron, skill, automation, hermes]
---

# Cron Skill Binding — 定时任务与技能自动绑定

基于 Hermes Agent 理念：技能可以自己声明"我需要定时执行"，系统自动注册到 cron。

## 两种模式

### 模式 A：技能自注册（Skill declares its own cron）

技能在 frontmatter 或末尾 YAML 块声明 cron schedule，系统自动创建 cron job。

### 模式 B：Cron 挂载技能（Cron attaches skills）

创建 cron job 时声明要挂载的技能，job 运行时 agent 拥有该技能上下文。

---

## 模式 A：技能自注册流程

```
技能声明 cron.schedule
    ↓
Agent 启动时扫描 skills/ 目录
    ↓
检测到新 cron 声明
    ↓
调用 cron(action="add") 创建任务
    ↓
cron job 存在则更新，不存在则创建
```

### 自注册检测脚本（每次启动或 heartbeat 时执行）

```javascript
// pseudocode
const fs = require('fs');
const path = require('path');
const skillsDir = 'skills/';

const files = fs.readdirSync(skillsDir).filter(f => f.endsWith('.md'));

for (const file of files) {
  const content = fs.readFileSync(path.join(skillsDir, file), 'utf8');
  const cronMatch = content.match(/cron:\s*\n\s*schedule:\s*["']([^"']+)["']/);

  if (cronMatch) {
    const schedule = cronMatch[1];
    const skillName = file.replace('.md', '');
    // 检查 cron job 是否存在，不存在则创建
    ensureCronJob(skillName, schedule, skillName);
  }
}
```

### 技能 cron 声明格式

在技能文件末尾：

```yaml
cron:
  schedule: "0 9 * * *"
  tz: "Asia/Bangkok"
  description: "每天9点检查 DCS 采集状态"
  enabled: true
```

---

## 模式 B：Cron 挂载技能

创建 cron job 时，通过 payload 内联技能内容：

```javascript
cron(action="add", job={
  name: "DCS Health Check",
  schedule: { kind: "cron", expr: "0 */4 * * *", tz: "Asia/Bangkok" },
  sessionTarget: "isolated",
  payload: {
    kind: "agentTurn",
    message: `执行 DCS 健康检查。

技能上下文：
---
${fs.readFileSync('skills/dcs-opc-collector.md', 'utf8')}
---

步骤：
1. 检查 OPC Server 连接
2. 检查 InfluxDB 写入
3. 如有异常，发送告警到钉钉`,
    skills: ["dcs-opc-collector"]  // 声明依赖（未来支持）
  }
})
```

---

## Windows 计划任务方案（OpenClaw Cron 权限不足时的替代）

当 `cron add` 需要 `operator.admin` scope 而 session 没有权限时，用 Windows Task Scheduler 代替：

```powershell
# 创建计划任务，每15分钟执行一次
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument '-ExecutionPolicy Bypass -WindowStyle Hidden -File D:\OpenClaw\workspace\main\gateway-health-check.ps1'
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 365)
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
Register-ScheduledTask -TaskName 'OpenClaw Gateway Health Check' -Action $action -Trigger $trigger -Settings $settings -Description 'Every 15min: check Gateway health'
```

验证任务：
```powershell
Get-ScheduledTask -TaskName 'OpenClaw Gateway Health Check' | Get-ScheduledTaskInfo
```

删除任务：
```powershell
Unregister-ScheduledTask -TaskName 'OpenClaw Gateway Health Check' -Confirm:$false
```

## OpenClaw 当前支持

| 功能 | 状态 | 说明 |
|------|------|------|
| 技能声明 cron.schedule | ✅ 可用 | 需 agent 扫描注册 |
| cron job 自动创建 | ✅ 可用 | cron(action="add") |
| cron agentTurn 内联技能内容 | ✅ 可用 | payload.message 中内联 |
| cron 挂载 skills: 字段 | ❌ 不支持 | OpenClaw 不识别 skills 字段 |
| 技能自动删除关联 cron | ⚠️ 部分 | 需手动删除或 enabled=false |

---

## 常用 Cron 表达式

| 表达式 | 含义 |
|--------|------|
| `0 9 * * *` | 每天 9:00 |
| `0 */4 * * *` | 每 4 小时 |
| `*/30 * * * *` | 每 30 分钟 |
| `0 9,18 * * *` | 每天 9:00 和 18:00 |
| `0 8-18 * * 1-5` | 工作日 8:00-18:00 每小时 |
| `30 5 * * 0` | 每周日 5:30 |

---

## 实现步骤

### 1. 更新 HEARTBEAT.md 加入自注册检测

```markdown
### 6. Cron Skill 自注册检查
每次 heartbeat：
1. 扫描 skills/ 目录，检测 cron: 声明
2. 比对已有 cron jobs，缺失则创建
3. 如技能 enabled=false 但 cron 存在，删除 cron job
```

### 2. 扫描脚本实现

```javascript
// 检查 skills/ 中所有技能的 cron 声明
const { cron } = require('./tools');  // OpenClaw cron tool

async function scanSkillsAndRegisterCrons() {
  const fs = require('fs');
  const path = require('path');

  const existingJobs = await cron(action="list");
  const skillFiles = fs.readdirSync('skills/').filter(f => f.endsWith('.md'));

  for (const file of skillFiles) {
    const skillName = file.replace('.md', '');
    const content = fs.readFileSync(path.join('skills/', file), 'utf8');

    // 提取 cron.schedule
    const match = content.match(/schedule:\s*["']([^"']+)["']/);
    if (!match) continue;

    const schedule = match[1];
    const jobName = `SkillCron: ${skillName}`;

    const exists = existingJobs.jobs.some(j => j.name === jobName);

    if (!exists) {
      // 创建 cron job
      cron(action="add", job={
        name: jobName,
        schedule: { kind: "cron", expr: schedule },
        sessionTarget: "isolated",
        payload: {
          kind: "agentTurn",
          message: `执行技能：${skillName}\n\n${content}`
        }
      });
    }
  }
}
```

### 3. 示例：带 cron 的 DCS 检查技能

```yaml
---
name: dcs-daily-check
description: 每天检查 DCS 数据采集健康状态
version: 1.0.0
cron:
  schedule: "0 9 * * *"
  tz: "Asia/Bangkok"
  description: "每天9点 DCS 健康检查"
  enabled: true
---

# DCS Daily Check

## 检查步骤

1. 连接 InfluxDB 查询最新数据时间戳
2. 如超过 5 分钟无数据 → 告警
3. 检查 OPC Server 状态
4. 汇总结果写入日志

## 依赖

- InfluxDB 连接信息
- OPC Server 地址
- 钉钉告警 webhook
```

---

## 与 Hermes 的差异

| 功能 | Hermes | OpenClaw |
|------|--------|----------|
| 技能自声明 cron | 原生支持 | 需扫描注册 |
| cron 挂载 skills | 原生 `mount:` 字段 | 需内联到 message |
| 多技能组合 | `mount: [a, b]` | 手动内联多个 |
| cron 结果投递 | 任意 channel | 受限于 announce |
| 条件激活 | `requires_toolsets` | 不支持 |

---

## 验证

```bash
# 列出所有 cron jobs
cron(action="list")

# 验证技能 cron 已被注册
# 检查 jobs 列表中是否有 "SkillCron:" 前缀的 job
```
