# HEARTBEAT.md

## 每次心跳检查（按顺序执行）

### 1. 每日自动记忆保存
对比 lastMemoryUpdate 和当前日期。如果日期变了，执行会话历史摘要，写入 memory/YYYY-MM-DD.md，记录最后更新时间。

### 2. 容量 + 格式检查

检查字符数和格式：
```
MEMORY.md 硬限制: 3000 chars  软限制: 2500 chars
USER.md  硬限制: 1500 chars  软限制: 1200 chars
```

**格式检查**：
- 必须使用 `§` 分隔符格式
- 每条记忆以 `§` 开头
- 包含容量头部 `══════════════`
- 格式错误 → 立即重写为标准格式

**超过软限制** → 执行压缩脚本：`exec(node compress.cjs [memory|user|both])`
**超过硬限制** → 强制压缩后再操作

**删除优先级（从低到高）：**
1. 过期待处理事项
2. 过于详细的步骤
3. 重复描述
4. 一次性事件记录

**保留优先级（从高到低）：**
1. 用户核心信息（姓名、时区、偏好）
2. GitHub 项目地址
3. 重要决策和教训
4. 系统配置

### 3. 反思触发检查
满足以下条件之一 → 立即生成反思：
- 过去1小时内完成了复杂任务（>5步骤）
- 学到了新的框架或工具
- 解决了之前未遇到过的问题
- 用户说了"记住这个"

### 4. 技能使用追踪检查
- 检查 skills/usage-log.json
- 超过30天未使用的技能 → 标记"可能过时"
- effectiveness=poor 超过2次 → 删除技能

### 5. Cron Skill 自注册检查
扫描 skills/ 目录，检测有 cron.schedule 声明但尚未创建 cron job 的技能：
```
skills/*.md 中匹配 cron.schedule="..."
    ↓
比对 cron(action="list") 的 jobs
    ↓
缺失 → cron(action="add") 创建
enabled=false → 删除已有 cron job
```

### 6. 待处理事项检查
memory/YYYY-MM-DD.md 中的待处理，有无超时或可推进的。

---

lastMemoryUpdate: 2026-04-17
