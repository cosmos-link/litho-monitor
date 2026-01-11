# 光刻机设备对接手册

> **文档用途**: 工厂设备接入指南  
> **适用对象**: 设备管理方 / IT 运维人员  
> **版本**: 1.0

---

## 目录

1. [对接概述](#1-对接概述)
2. [信息清单总览](#2-信息清单总览)
3. [网络连接信息](#3-网络连接信息)
4. [安全认证信息](#4-安全认证信息)
5. [数据节点映射](#5-数据节点映射)
6. [对接流程](#6-对接流程)
7. [常见问题](#7-常见问题)

---

## 1. 对接概述

### 1.1 对接目标

通过 OPC UA 协议实现光刻机设备数据的实时采集与监控：

| 功能 | 说明 |
|:-----|:-----|
| ✅ 实时状态监控 | 设备运行状态、工作模式 |
| ✅ 工艺数据采集 | 晶圆计数、曝光参数、质量指标 |
| ✅ 健康指标跟踪 | 温度、振动、激光寿命 |
| ✅ 报警信息获取 | 实时报警消息 |

### 1.2 技术要求

| 项目 | 要求 |
|:-----|:-----|
| 通信协议 | OPC UA (IEC 62541) |
| 安全策略 | Basic256Sha256 (推荐) |
| 消息模式 | SignAndEncrypt (推荐) |
| 网络端口 | TCP 4840 (默认) |

---

## 2. 信息清单总览

请按以下清单准备信息，**标记 ★ 的为必需项**：

### 必需信息

| 序号 | 信息类别 | 具体内容 |
|:----:|:---------|:---------|
| ★1 | 网络地址 | 设备 IP 地址或主机名 |
| ★2 | 服务端口 | OPC UA 服务端口 (默认 4840) |
| ★3 | 端点 URL | 完整的 OPC UA 端点地址 |
| ★4 | 用户账号 | 监控用户名和密码 (只读权限即可) |
| ★5 | 数据节点 | 各监控数据点的 NodeID |

### 可选信息

| 序号 | 信息类别 | 具体内容 |
|:----:|:---------|:---------|
| 6 | 安全策略 | 设备支持的安全策略列表 |
| 7 | 服务器证书 | 用于证书认证 |
| 8 | 状态码定义 | MachineStatus 各值含义 |
| 9 | 报警阈值 | 各参数的报警阈值设定 |

---

## 3. 网络连接信息

### 3.1 基础连接配置

请填写以下信息：

| 配置项 | 您的设备值 | 示例 |
|:-------|:-----------|:-----|
| 设备 IP 地址 | _________________ | `192.168.1.100` |
| OPC UA 端口 | _________________ | `4840` |
| 端点 URL | _________________ | `opc.tcp://192.168.1.100:4840` |

> **端点 URL 格式**: `opc.tcp://<IP地址>:<端口号>[/路径]`

### 3.2 网络要求

- [ ] 监控客户端可访问设备 IP
- [ ] TCP 端口已开放 (防火墙)
- [ ] 网络延迟 < 100ms (推荐)

---

## 4. 安全认证信息

### 4.1 用户账号 (必需)

请为我们的监控系统创建一个**只读权限**的用户账号：

| 配置项 | 您的设备值 | 说明 |
|:-------|:-----------|:-----|
| 用户名 | _________________ | 建议: `monitor` |
| 密码 | _________________ | 建议: 8位以上复杂密码 |
| 权限级别 | _________________ | 只读权限即可 |

### 4.2 安全策略配置

请确认您的设备支持以下安全配置（推荐配置已标记 ✓）：

**支持的安全策略**（请勾选）:
- [ ] None (无安全) - 不推荐
- [ ] Basic128Rsa15
- [ ] Basic256
- [✓] **Basic256Sha256** (推荐)
- [ ] Aes128_Sha256_RsaOaep
- [ ] Aes256_Sha256_RsaPss

**支持的消息模式**（请勾选）:
- [ ] None (无安全)
- [ ] Sign (仅签名)
- [✓] **SignAndEncrypt** (签名+加密，推荐)

### 4.3 证书文件 (如需要)

如使用证书认证，请提供：

| 文件 | 格式 | 说明 |
|:-----|:-----|:-----|
| 服务器证书 | .pem / .der | 用于客户端验证服务器 |
| CA 根证书 | .pem | 如使用自签名证书 |

---

## 5. 数据节点映射

### 5.1 NodeID 格式说明

OPC UA 节点标识格式：
```
ns=<命名空间索引>;<类型>=<标识符>
```

| 类型 | 说明 | 格式示例 |
|:-----|:-----|:---------|
| `i` | 数字标识符 | `ns=2;i=1001` |
| `s` | 字符串标识符 | `ns=3;s="Equipment.Temperature"` |
| `g` | GUID 标识符 | `ns=4;g=12345678-1234-5678-...` |

### 5.2 数据节点清单

请提供以下数据点的 **NodeID**：

#### 📋 身份信息 (静态数据)

| 数据项 | 您的 NodeID | 数据类型 | 示例值 |
|:-------|:------------|:---------|:-------|
| 制造商标识 (VendorID) | | String | "ASML" |
| 设备序列号 (SerialNumber) | | String | "LM-2024-001" |
| 型号名称 (ModelName) | | String | "TWINSCAN NXE:3400C" |

#### 📊 运行状态 (动态数据)

| 数据项 | 您的 NodeID | 数据类型 | 备注 |
|:-------|:------------|:---------|:-----|
| 设备状态 (MachineStatus) | | Int32 | 请填写状态码定义 |
| 选中状态 (IsSelected) | | Boolean | |

**状态码定义**（请填写您设备的状态码含义）:

| 状态值 | 含义 |
|:-------|:-----|
| 0 | _________________ |
| 1 | _________________ |
| 2 | _________________ |
| 3 | _________________ |

#### ⚙️ 工艺参数 (实时数据)

| 数据项 | 您的 NodeID | 数据类型 | 单位 | 典型范围 |
|:-------|:------------|:---------|:-----|:---------|
| 晶圆计数 (WaferCount) | | UInt32 | 片 | 0~999999 |
| 曝光能量 (ExposureEnergy) | | Double | mJ/cm² | 20~30 |
| 剂量误差 (DoseError) | | Double | % | 0~5 |
| 套刻精度 (OverlayPrecision) | | Double | nm | 0.5~2.0 |

#### 🔧 健康监控 (诊断数据)

| 数据项 | 您的 NodeID | 数据类型 | 单位 | 报警阈值 |
|:-------|:------------|:---------|:-----|:---------|
| 激光脉冲计数 (LaserPulseCount) | | UInt64 | 次 | _________ |
| 工台振动 (StageVibration) | | Double | μm | _________ |
| 设备温度 (Temperature) | | Double | °C | _________ |
| 报警信息 (AlarmMessage) | | String | — | — |

---

## 6. 对接流程

### 6.1 流程图

```
┌─────────────────┐
│  1. 信息收集     │  工厂提供网络、账号、节点映射信息
└────────┬────────┘
         ▼
┌─────────────────┐
│  2. 配置生成     │  我方根据信息生成 .env 配置文件
└────────┬────────┘
         ▼
┌─────────────────┐
│  3. 连接测试     │  测试网络连通性和认证
└────────┬────────┘
         ▼
┌─────────────────┐
│  4. 数据验证     │  验证各节点数据读取正常
└────────┬────────┘
         ▼
┌─────────────────┐
│  5. 正式上线     │  部署监控客户端
└─────────────────┘
```

### 6.2 配置文件示例

收到您的信息后，我们将生成如下配置文件：

```ini
# ========================================
# 光刻机 OPC UA 客户端配置文件
# 设备: [您的设备型号]
# ========================================

# === 连接配置 ===
OPC_ENDPOINT=opc.tcp://您的设备IP:4840
OPC_USERNAME=您的用户名
OPC_PASSWORD=您的密码
OPC_CLIENT_CERT=certs/client-cert.pem
OPC_CLIENT_KEY=certs/client-key.pem
OPC_TIMEOUT=30
MONITORING_INTERVAL=2

# === 命名空间配置 ===
OPC_NAMESPACE=2
DEFAULT_NODE_ID_TYPE=i

# === 身份信息节点 ===
VENDOR_ID_NAMESPACE=2
VENDOR_ID_TYPE=i
VENDOR_ID_VALUE=3

SERIAL_NUMBER_NAMESPACE=2
SERIAL_NUMBER_TYPE=i
SERIAL_NUMBER_VALUE=4

MODEL_NAME_NAMESPACE=2
MODEL_NAME_TYPE=i
MODEL_NAME_VALUE=5

# === 状态节点 ===
MACHINE_STATUS_NAMESPACE=2
MACHINE_STATUS_TYPE=i
MACHINE_STATUS_VALUE=7

IS_SELECTED_NAMESPACE=2
IS_SELECTED_TYPE=i
IS_SELECTED_VALUE=8

# === 工艺参数节点 ===
WAFER_COUNT_NAMESPACE=2
WAFER_COUNT_TYPE=i
WAFER_COUNT_VALUE=10

EXPOSURE_ENERGY_NAMESPACE=2
EXPOSURE_ENERGY_TYPE=i
EXPOSURE_ENERGY_VALUE=11

DOSE_ERROR_NAMESPACE=2
DOSE_ERROR_TYPE=i
DOSE_ERROR_VALUE=12

OVERLAY_PRECISION_NAMESPACE=2
OVERLAY_PRECISION_TYPE=i
OVERLAY_PRECISION_VALUE=13

# === 健康监控节点 ===
LASER_PULSE_COUNT_NAMESPACE=2
LASER_PULSE_COUNT_TYPE=i
LASER_PULSE_COUNT_VALUE=15

STAGE_VIBRATION_NAMESPACE=2
STAGE_VIBRATION_TYPE=i
STAGE_VIBRATION_VALUE=16

TEMPERATURE_NAMESPACE=2
TEMPERATURE_TYPE=i
TEMPERATURE_VALUE=17

ALARM_MESSAGE_NAMESPACE=2
ALARM_MESSAGE_TYPE=i
ALARM_MESSAGE_VALUE=18

# === 运行配置 ===
MONITOR_MODE=poll
LOG_LEVEL=INFO
```

### 6.3 验收标准

对接完成后，监控系统应能：

- [ ] 成功建立安全连接
- [ ] 读取设备身份信息
- [ ] 实时获取运行状态
- [ ] 采集工艺参数数据
- [ ] 监控健康指标
- [ ] 接收报警信息

---

## 7. 常见问题

### Q1: 如何获取设备的 NodeID？

**方法 1**: 查阅设备 OPC UA 文档
- 设备厂商通常会提供 OPC UA 地址空间说明文档

**方法 2**: 使用 OPC UA 浏览工具
- UaExpert (免费)
- Prosys OPC UA Browser
- 我方可提供节点扫描工具

### Q2: 不确定设备支持哪种安全策略？

请联系设备厂商获取 OPC UA 安全配置信息，或使用 OPC UA 客户端工具查询端点支持的安全策略。

### Q3: 是否支持其他数据点？

支持。请提供额外数据点的：
- 数据名称
- NodeID
- 数据类型
- 单位
- 说明

### Q4: 数据采集频率是多少？

| 模式 | 频率 | 说明 |
|:-----|:-----|:-----|
| 轮询模式 | 可配置 (默认 2秒) | 固定周期采集 |
| 订阅模式 | 实时 | 数据变化时推送 |

---

## 联系方式

| 事项 | 联系方式 |
|:-----|:---------|
| 技术支持 | 请联系项目负责人 |
| 对接咨询 | 请联系项目负责人 |

---

## 附录: 信息收集表

请复制以下表格填写后发送给我们：

```
========================================
光刻机设备对接信息收集表
========================================

【基本信息】
设备厂商: 
设备型号: 
设备序列号: 

【网络配置】
设备 IP: 
OPC UA 端口: 
端点 URL: 

【用户认证】
用户名: 
密码: 
权限级别: 

【安全配置】
安全策略: 
消息模式: 

【节点映射】
VendorID NodeID: 
SerialNumber NodeID: 
ModelName NodeID: 
MachineStatus NodeID: 
IsSelected NodeID: 
WaferCount NodeID: 
ExposureEnergy NodeID: 
DoseError NodeID: 
OverlayPrecision NodeID: 
LaserPulseCount NodeID: 
StageVibration NodeID: 
Temperature NodeID: 
AlarmMessage NodeID: 

【状态码定义】
0 = 
1 = 
2 = 
3 = 

【其他备注】

========================================
```

