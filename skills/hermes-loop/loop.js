#!/usr/bin/env node
/**
 * hermes-loop: 观察→决策→行动→反思
 * v1.0.0
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ============ 配置 ============
const CONFIG = {
  workspace: process.env.WORKSPACE || 'D:/OpenClaw/workspace',
  maxReflections: 100,
  priorityOrder: ['fix', 'clean', 'learn', 'optimize']
};

// ============ 工具函数 ============
const log = (msg, type = 'info') => {
  const colors = {
    info: '\x1b[36m',
    success: '\x1b[32m',
    warning: '\x1b[33m',
    error: '\x1b[31m',
    reset: '\x1b[0m'
  };
  console.log(`${colors[type] || colors.info}[${type.toUpperCase()}]${colors.reset} ${msg}`);
};

const now = () => new Date().toISOString();
const today = () => new Date().toISOString().split('T')[0];

// ============ 阶段 1: 观察 (OBSERVE) ============
async function observe() {
  log('🔍 开始观察工作区...', 'info');
  
  const observations = {
    timestamp: now(),
    signals: []
  };

  // 1. 检查 Git 状态
  try {
    const gitStatus = execSync('git status --porcelain', { 
      cwd: CONFIG.workspace,
      encoding: 'utf8',
      timeout: 5000
    });
    if (gitStatus.trim()) {
      const lines = gitStatus.trim().split('\n').length;
      observations.signals.push({
        type: 'git_pending',
        priority: 'high',
        message: `有 ${lines} 个未提交的文件更改`,
        action: 'commit_pending_changes'
      });
      log(`发现 ${lines} 个未提交的文件更改`, 'warning');
    } else {
      log('Git 工作区干净', 'success');
    }
  } catch (e) {
    log('Git 检查失败: ' + e.message, 'error');
  }

  // 2. 检查技能目录
  try {
    const skillsDir = path.join(CONFIG.workspace, 'skills');
    const skills = fs.readdirSync(skillsDir).filter(d => {
      const stat = fs.statSync(path.join(skillsDir, d));
      return stat.isDirectory() && fs.existsSync(path.join(skillsDir, d, 'SKILL.md'));
    });
    observations.signals.push({
      type: 'skills_count',
      priority: 'low',
      message: `检测到 ${skills.length} 个有效技能`,
      data: skills
    });
    log(`检测到 ${skills.length} 个有效技能`, 'info');
  } catch (e) {
    log('技能检查失败: ' + e.message, 'error');
  }

  // 3. 检查 MEMORY.md 容量
  try {
    const memPath = path.join(CONFIG.workspace, 'MEMORY.md');
    const memContent = fs.readFileSync(memPath, 'utf8');
    const memLen = memContent.length;
    if (memLen > 2500) {
      observations.signals.push({
        type: 'memory_capacity',
        priority: 'medium',
        message: `MEMORY.md 接近上限 (${memLen}/3000)`
      });
      log(`MEMORY.md 接近上限: ${memLen}/3000`, 'warning');
    } else {
      log(`MEMORY.md 容量正常: ${memLen}/3000`, 'success');
    }
  } catch (e) {
    log('容量检查失败: ' + e.message, 'error');
  }

  log('✅ 观察阶段完成', 'success');
  return observations;
}

// ============ 阶段 2: 决策 (DECIDE) ============
function decide(observations) {
  log('🧠 开始决策分析...', 'info');
  
  const decisions = {
    timestamp: now(),
    tasks: []
  };

  // 按优先级排序信号
  const priorityWeight = { high: 3, medium: 2, low: 1 };
  const sortedSignals = observations.signals
    .filter(s => s.priority)
    .sort((a, b) => priorityWeight[b.priority] - priorityWeight[a.priority]);

  for (const signal of sortedSignals) {
    switch (signal.type) {
      case 'git_pending':
        decisions.tasks.push({
          id: `git_commit_${Date.now()}`,
          action: 'commit_git_changes',
          priority: 'high',
          reason: signal.message,
          dryRun: false
        });
        log(`决策: 提交 Git 更改`, 'warning');
        break;
        
      case 'memory_capacity':
        decisions.tasks.push({
          id: `compress_memory_${Date.now()}`,
          action: 'compress_memory',
          priority: 'medium',
          reason: signal.message,
          dryRun: false
        });
        log(`决策: 压缩 MEMORY.md`, 'warning');
        break;
        
      default:
        log(`忽略信号: ${signal.type}`, 'info');
    }
  }

  if (decisions.tasks.length === 0) {
    decisions.tasks.push({
      id: `noop_${Date.now()}`,
      action: 'no_action_needed',
      priority: 'low',
      reason: '没有检测到需要处理的问题'
    });
    log('决策: 无需执行任何操作', 'success');
  }

  log('✅ 决策阶段完成', 'success');
  return decisions;
}

// ============ 阶段 3: 行动 (ACT) ============
async function act(decisions) {
  log('🚀 开始执行任务...', 'info');
  
  const results = {
    timestamp: now(),
    executed: [],
    failed: []
  };

  for (const task of decisions.tasks) {
    log(`执行任务: ${task.action}`, 'info');
    
    try {
      switch (task.action) {
        case 'commit_git_changes':
          // 在实际执行时，这里会调用 git commit
          // 当前仅记录意图
          log('[模拟] 执行: git add -A && git commit -m "auto: hermes-loop commit"', 'warning');
          results.executed.push({ task, status: 'simulated' });
          break;
          
        case 'compress_memory':
          log('[模拟] 执行: node compress.cjs memory', 'warning');
          results.executed.push({ task, status: 'simulated' });
          break;
          
        case 'no_action_needed':
          log('无需执行任何操作', 'success');
          results.executed.push({ task, status: 'skipped' });
          break;
          
        default:
          throw new Error(`未知任务类型: ${task.action}`);
      }
    } catch (error) {
      log(`任务失败: ${error.message}`, 'error');
      results.failed.push({ task, error: error.message });
    }
  }

  log('✅ 行动阶段完成', 'success');
  return results;
}

// ============ 阶段 4: 反思 (REFLECT) ============
function reflect(observations, decisions, results) {
  log('🤔 开始反思总结...', 'info');
  
  const reflection = {
    timestamp: now(),
    date: today(),
    cycle: {
      observe: observations.signals.length,
      decide: decisions.tasks.length,
      act: results.executed.length + results.failed.length,
      success: results.failed.length === 0
    },
    insights: [],
    improvements: []
  };

  // 分析洞察
  if (observations.signals.length === 0) {
    reflection.insights.push('工作区状态良好，没有检测到需要干预的问题');
  } else {
    const types = observations.signals.map(s => s.type);
    reflection.insights.push(`检测到 ${observations.signals.length} 个信号: ${types.join(', ')}`);
  }

  if (results.failed.length > 0) {
    reflection.insights.push(`${results.failed.length} 个任务执行失败，需要调查`);
    reflection.improvements.push('增强错误处理和重试机制');
  }

  // 记录到文件
  try {
    const reflectionDir = path.join(CONFIG.workspace, 'memory');
    if (!fs.existsSync(reflectionDir)) {
      fs.mkdirSync(reflectionDir, { recursive: true });
    }
    
    const reflectionFile = path.join(reflectionDir, `反思-${today()}-${new Date().toISOString().slice(11,16).replace(':','')}.md`);
    
    const content = `# 反思日志 - ${reflection.timestamp}

## 执行周期统计
- 观察信号数: ${reflection.cycle.observe}
- 决策任务数: ${reflection.cycle.decide}
- 执行任务数: ${reflection.cycle.act}
- 执行成功率: ${reflection.cycle.success ? '100%' : '存在失败'}

## 洞察
${reflection.insights.map(i => `- ${i}`).join('\n')}

## 改进建议
${reflection.improvements.map(i => `- ${i}`).join('\n') || '- 暂无改进建议'}

---
*由 hermes-loop 自动生成*
`;
    
    fs.writeFileSync(reflectionFile, content);
    log(`反思记录已保存: ${reflectionFile}`, 'success');
  } catch (e) {
    log(`保存反思失败: ${e.message}`, 'error');
  }

  log('✅ 反思阶段完成', 'success');
  return reflection;
}

// ============ 主循环 ============
async function main() {
  const mode = process.argv[2] || 'full';
  const dryRun = process.argv.includes('--dry-run');
  
  console.log(`
╔════════════════════════════════════════╗
║        HERMES-LOOP v1.0.0              ║
║  观察 → 决策 → 行动 → 反思             ║
╚════════════════════════════════════════╝
模式: ${mode} ${dryRun ? '(模拟模式)' : ''}
`);

  try {
    // 阶段 1: 观察
    const observations = await observe();
    
    // 阶段 2: 决策
    const decisions = decide(observations);
    
    // 阶段 3: 行动
    const results = await act(decisions);
    
    // 阶段 4: 反思
    const reflection = reflect(observations, decisions, results);
    
    console.log(`
╔════════════════════════════════════════╗
║     HERMES-LOOP 执行完成 ✅             ║
╚════════════════════════════════════════╝
`);
    
    process.exit(0);
  } catch (error) {
    console.error('\n❌ 执行失败:', error.message);
    process.exit(1);
  }
}

// 如果直接运行此文件
if (require.main === module) {
  main();
}

// 导出模块
module.exports = { observe, decide, act, reflect };
