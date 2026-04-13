---
name: windows-cleanup
description: Windows 软件自启动项彻底清理（注册表 + 启动文件夹 + PM2）
version: 1.0.0
platforms: [windows]
author: auto-learned
created: 2026-04-11
tags: [windows, startup, registry, cleanup]
---

# Windows 自启动项彻底清理

## 何时使用

- 软件开机自启动干扰了 gateway 或其他服务
- 需要阻止某个软件（如 ClawPanel）自动运行
- ClawPanel 每次启动重置 gateway token 导致配置失效

## 标准流程

### 第一步：查找自启动位置
```powershell
# 注册表 Run key
Get-CimInstance Win32_StartupCommand

# 启动文件夹
Get-ChildItem "C:\Users\hh\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup"
```

### 第二步：删除注册表自启动
```powershell
# 找到确切的路径
Get-CimInstance Win32_StartupCommand | Where-Object { $_.Name -eq "软件名" }

# 删除（用完整路径）
Remove-ItemProperty -Path "HKU\S-1-5-21-xxx\...\Run" -Name "软件名" -Force
```

### 第三步：删除启动文件夹快捷方式
```powershell
Remove-Item "C:\Users\hh\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\xxx.bat" -Force
```

### 第四步：停止相关 PM2 进程
```powershell
# 查找占用目录的进程
Get-Process | Where-Object { $_.Path -like "*软件名*" }

# 强制终止
Stop-Process -Id PID -Force
```

### 第五步：删除 PM2 进程和 resurrect 启动项
```bash
node node_modules\pm2\bin\pm2 kill
Remove-Item "C:\Users\hh\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\PM2 Resurrect.bat" -Force
```

## 注意事项

- PM2 daemon 会锁定目录，必须先 `pm2 kill` 才能删除目录
- 注册表修改需要用户确认（admin 权限）
- 删除前先确认是哪个软件导致的问题

## 验证方法

重启后软件不再自动启动，gateway config 不再被重置

## 使用反馈
```json
"effectiveness": "",  // good / mixed / poor
"lastResult": "",
"notes": []
