# hermes-loop

## description

自驱动进化闭环：观察→决策→行动→反思。自动扫描工作区状态，执行优先级任务，记录学习。

## usage

```yaml
- skill: hermes-loop
  action: run          # 执行一轮闭环
  params:
    mode: auto         # auto|dry-run
    priority: all      # all|fix|clean|learn
  
- skill: hermes-loop
  action: schedule     # 设置定时执行
  params:
    cron: "0 */4 * * *"  # 每4小时
```

## requirements

- Node.js 18+
- 工作区目录可读写

## files

- `loop.js` - 核心执行引擎
- `rules.json` - 决策规则
- `LOG.md` - 执行日志

## author

Hermes Loop v1.0
