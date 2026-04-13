---
name: dcs-opc-collector
description: 通用 DCS 系统 OPC UA 数据采集系统快速部署
version: 1.0.0
platforms: [windows, linux]
author: auto-learned
created: 2026-04-11
tags: [dcs, opc, industrial, iiot]
---

# DCS OPC UA 数据采集系统

通用模板，适用于浙大中控 JX-300XP、和利时 MACS、中控 WebField 等国产 DCS 系统。

## 何时使用

- 用户需要从 DCS 系统采集数据
- 需要通过 OPC UA 协议获取实时工艺参数
- 需要快速部署 MQTT + InfluxDB + Grafana 监控链路

## 标准流程

### 第一步：确认 OPC Server 信息
```
需要从用户获取：
1. DCS 型号（浙中控JX-300XP / 和利时MACS / 西门子PCS7 / ABB 800xA）
2. OPC Server 地址和端口（通常是 opc.tcp://IP:PORT）
3. 安全策略（None / Basic128 / Basic256）
4. 认证方式（匿名 / 用户名密码 / 证书）
```

### 第二步：生成采集配置
```
配置文件结构：
- config.json          → OPC UA 连接配置 + MQTT 输出
- mqtt_consumer.py     → Python 消费端（InfluxDB写入 + 告警）
- docker-compose.yml    → 中间件一键启动
```

### 第三步：典型点位映射
```
流量: FICxxx.PV → unit: m3/h
温度: TICxxx.PV → unit: °C
压力: PICxxx.PV → unit: MPa
液位: LICxxx.PV → unit: %
设备状态: PUMPxxx.STATUS → 0/1
阀开度: VALVExxx.POS → unit: %
转速: ELEMENTxxx.SPEED → unit: rpm
```

### 第四步：启动中间件
```bash
docker-compose up -d mosquitto influxdb grafana
```

### 第五步：验证数据流
```bash
# 订阅MQTT
docker exec supcon-mqtt mosquitto_sub -t "dcs/+/+" -u dcs_collector -P password

# 查询InfluxDB
curl -G "http://localhost:8086/query?db=jx300xp" --data-urlencode "q=SELECT * FROM dcs_tags LIMIT 5"
```

## 注意事项

- OPC Server 必须由DCS厂家提供或授权
- DCS 与采集层之间建议加工业防火墙
- JX-300XP 最大 20000 点
- 时钟必须 NTP 对时

## 验证方法

Grafana 看板有数据，趋势图正常显示，无告警红色

## 使用反馈（自动记录到 skills/usage-log.json）
```json
"effectiveness": "good",  // good / mixed / poor
"lastResult": "",
"notes": []
