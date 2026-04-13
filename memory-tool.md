---
name: memory-tool
description: 记忆管理工具 — 结构化 add/replace/remove 操作，统一使用 § 分隔符格式
version: 1.0.0
platforms: [windows, linux, darwin]
author: hermes-inspired
created: 2026-04-13
tags: [memory, hermes, tool]
---

# Memory Tool — 记忆管理操作约定

基于 Hermes Agent 的 memory 工具设计，结构化操作，避免记忆文件凌乱。

## 核心原则

1. **不要直接编辑文件** — 用结构化操作代替直接编辑
2. **§ 分隔符** — 每个记忆条目用 `§` 开头
3. **会话结束时统一写入** — 避免频繁 IO
4. **容量优先** — 超过限制先压缩再添加

---

## 操作格式

### add — 添加新记忆
```
memory(
  action="add",
  target="memory",        // memory 或 user
  content="新记忆内容"
)
```

### replace — 替换已有记忆
```
memory(
  action="replace",
  target="memory",
  old_text="唯一识别字符串",   // 只要能唯一确定条目的子字符串
  content="新的完整内容"
)
```

### remove — 删除记忆
```
memory(
  action="remove",
  target="memory",
  old_text="唯一识别字符串"
)
```

---

## § 分隔符格式（必须遵循）

记忆文件使用以下格式（与 Hermes 兼容）：

```markdown
══════════════════════════════════════════════
MEMORY (personal notes) [1234/3000 chars] — 41%
══════════════════════════════════════════════

§
# 主题名称
记忆内容第一行

§
# 另一个主题
内容，可以多行

§
# 第三个主题
内容
```

**格式规则：**
- `══════════` 包围容量头部（只在文件顶部出现一次）
- 每条记忆以 `§` 开头（独立一行）
- `# 标题` 是可选的，建议加上
- 条目之间留空行更清晰
- 底部注释用 `<!-- 备注 -->` 而非 `§`

---

## 何时触发

| 场景 | 操作 | 示例 |
|------|------|------|
| 学到新框架 | add to memory | "DeerFlow: YAML Skills + Sandbox" |
| 用户纠正 | replace to memory | "ClawPanel 会重置 token → 已移除" |
| 项目完成 | add to memory | "Django API 已上线" |
| 偏好变化 | replace to user | "用户现在喜欢更简洁的回复" |
| 过时信息 | remove from memory | "删掉 2024年的过时配置" |

---

## 容量检查（每次操作前）

```bash
# 检查记忆文件大小
node -e "const fs=require('fs'); const m=fs.readFileSync('MEMORY.md','utf8'); const u=fs.readFileSync('USER.md','utf8'); console.log('MEMORY:', m.length, '/3000'); console.log('USER:', u.length, '/1500');"
```

| 状态 | MEMORY.md | USER.md | 操作 |
|------|-----------|---------|------|
| ✅ OK | < 2500 | < 1200 | 正常 add |
| ⚠️ 警告 | 2500-3000 | 1200-1500 | 先压缩再 add |
| 🔴 危险 | >= 3000 | >= 1500 | 强制压缩后再 add |

---

## 压缩流程

当需要压缩时：

1. **合并相似条目** — 同一个主题的多个小条目 → 合并成一个大条目
2. **删除低价值内容** — 过于详细的步骤 → 只保留结论
3. **删除过时内容** — 时间敏感的、一次性的
4. **重写文件** — 保持格式完整

**保留优先级：**
```
高：用户偏好 / GitHub项目 / 重要教训 / 系统配置
中：已学框架 / 技能清单
低：详细步骤 / 历史事件 / 待处理清单
```

---

## 实际执行示例

### 添加新记忆
```javascript
// 不要这样：
// "已学会 Hermes 框架" → 直接追加到文件末尾

// 要这样：
memory(action="add", target="memory",
  content="§\n# 已学框架\nHermes: 自改进闭环（反思→技能化→追踪）"
)
```

### 替换记忆
```javascript
// 不要这样：
// 直接修改文件中的某一行

// 要这样：
memory(action="replace", target="memory",
  old_text="ClawPanel: 已从注册表移除",   // 唯一的子字符串
  content="§\n# ClawPanel\n已从注册表移除自启动（会重置gateway token）"
)
```

### 删除记忆
```javascript
memory(action="remove", target="memory",
  old_text="过时的待处理事项"   // 唯一即可
)
```

---

## Frozen Snapshot 机制

**重要**：记忆在会话启动时注入，之后的修改在当前会话中不生效（保护 LLM 前缀缓存）。

```
会话启动 → 记忆快照注入（只读）
    ↓
会话中 add/replace/remove → 写入磁盘，但不在当前会话生效
    ↓
新会话启动 → 新的快照注入
```

工具调用返回的是**实时状态**，但系统提示中的记忆是**快照**。

---

## 与 Hermes 的差异

| 功能 | Hermes | OpenClaw |
|------|--------|----------|
| 工具名 | `memory` | 用 edit/write 代替 |
| 格式 | § 分隔 | 已统一（我们实现了） |
| 容量 | 2200/1375 | 3000/1500（更宽松） |
| Frozen snapshot | 完整实现 | 部分（会话启动时注入） |
| 自动压缩 | 是 | 半自动（heartbeat 检查） |

---

## 验证

```bash
# 检查格式是否正确
node -e "
const fs = require('fs');
const m = fs.readFileSync('MEMORY.md', 'utf8');
const count = (m.match(/\n§\n/g) || []).length + 1;
console.log('记忆条目数:', count);
console.log('格式正确:', m.includes('══════════════'));
"
```
