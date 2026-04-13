# OpenClaw Skills — 技能库

> 基于 Hermes Agent 理念构建的自主学习闭环系统
> 自动从任务中学习，持续积累可复用技能

## 核心机制

```
任务完成 → 反思 → 判断是否技能化 → 写成 SKILL.md
    ↓
技能被调用 → 记录使用效果 → 持续改进
    ↓
效果好的 → 强化
效果差的 → 修正或删除
```

## 技能目录

| 技能 | 描述 | 状态 | 使用次数 |
|------|------|------|----------|
| `self-reflection.md` | 自主学习闭环（核心机制） | ✅ | - |
| `dcs-opc-collector.md` | 通用 DCS OPC UA 数据采集 | ✅ | - |
| `github-deploy.md` | GitHub 仓库创建 + 推送 | ✅ | - |
| `windows-cleanup.md` | Windows 自启动项彻底清理 | ✅ | - |
| `SKILL.md` | 技能创建模板 | ✅ | - |

## 技能使用追踪

每个技能底部有"使用反馈" section，记录：
```json
"effectiveness": "good"   // good / mixed / poor
"lastResult": "成功，Docker Compose 启动正常"
"notes": ["强化：步骤二可以合并到一步"]
```

追踪日志：`skills/usage-log.json`

## 效果评判

| 效果 | 评判标准 | 操作 |
|------|----------|------|
| **good** | 全部步骤正常，成功完成 | effectiveness = good |
| **mixed** | 部分步骤有问题 | effectiveness = mixed，附修正说明 |
| **poor** | 完全失败 | 删除或重写 |

## 触发条件

以下情况自动触发学习流程：
1. 复杂任务（超过5步骤）完成
2. 用户说"记住这个"
3. 同类任务第三次出现
4. 调研新框架/新技术后
5. **技能被调用后**（记录效果）

## 推送机制

学到新技能后，自动推送到所有 agent workspace

## 扩展方向

- [x] 效果追踪系统（已完成）
- [ ] 增加更多技能（目标：20+）
- [ ] 实现容量管理（限制 MEMORY.md 大小）
- [ ] 对接 agentskills.io 标准
