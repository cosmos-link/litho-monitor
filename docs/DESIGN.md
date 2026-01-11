# 光刻机数据监控系统 - 技术设计文档

> **文档版本**: 1.0  
> **协议标准**: OPC UA 1.04  
> **安全级别**: Basic256Sha256 + SignAndEncrypt  
> **更新日期**: 2026-01

---

## 目录

1. [系统概述](#1-系统概述)
2. [系统架构](#2-系统架构)
3. [数据模型](#3-数据模型)
4. [通信协议](#4-通信协议)
5. [安全机制](#5-安全机制)
6. [监控模式](#6-监控模式)
7. [部署配置](#7-部署配置)

---

## 1. 系统概述

### 1.1 项目背景

本系统是面向半导体制造行业的光刻机实时数据监控解决方案，基于工业标准 **OPC UA** (OPC Unified Architecture) 协议实现设备数据的安全采集与传输。

### 1.2 设计目标

| 目标 | 说明 |
|:-----|:-----|
| **安全性** | 传输层加密 + 应用层认证，确保数据安全 |
| **实时性** | 支持轮询/订阅双模式，满足不同实时性需求 |
| **标准化** | 遵循 OPC UA 规范，确保跨厂商互操作性 |
| **可扩展** | 模块化设计，便于接入不同厂商设备 |

### 1.3 技术选型

| 组件 | 技术方案 | 说明 |
|:-----|:---------|:-----|
| 通信协议 | OPC UA 1.04 | 工业自动化标准协议 |
| 编程语言 | Python 3.9+ | 异步编程，高效稳定 |
| OPC UA 库 | asyncua | 现代异步 OPC UA 实现 |
| 加密库 | cryptography | X.509 证书和加密处理 |
| 配置管理 | python-dotenv | 环境变量配置 |

---

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│              宇酷通WEB4.0生态链操作系统 (智能预警、修复、上链)         │
└─────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ 数据上报
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                         OPC UA Client                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 连接管理     │  │ 数据采集     │  │ 订阅处理     │              │
│  │ • 安全握手   │  │ • 节点读取   │  │ • 变化通知   │              │
│  │ • 会话维护   │  │ • 批量读取   │  │ • 数据缓存   │              │
│  │ • 断线重连   │  │ • 数据格式化  │  │ • 事件触发   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 │ OPC UA over TLS
                                 │ Basic256Sha256 + SignAndEncrypt
                                 │ 用户名密码认证
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         OPC UA Server                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ 安全模块     │  │ 数据模型     │  │ 模拟引擎     │              │
│  │ • 证书验证   │  │ • 地址空间   │  │ • 状态机     │              │
│  │ • 用户认证   │  │ • 节点管理   │  │ • 数据生成   │              │
│  │ • 权限控制   │  │ • 类型定义   │  │ • 报警触发   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ 数据采集
                                 │
┌─────────────────────────────────────────────────────────────────┐
│                      光刻机设备 (PLC/传感器)                      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

| 组件 | 文件 | 职责 |
|:-----|:-----|:-----|
| OPC UA 服务器 | `opc-ua-server.py` | 设备数据模拟、安全控制、数据发布 |
| OPC UA 客户端 | `opc-ua-client.py` | 数据采集、实时监控、状态展示 |
| 证书生成器 | `gen-certs-openssl.sh` | X.509 证书生成 |
| 配置文件 | `.env.asml` | 设备连接参数配置 |

---

## 3. 数据模型

### 3.1 OPC UA 地址空间

OPC UA 地址空间采用层次化组织，将光刻机数据分为 4 个功能域：

```
Objects/
└── LithographyMachine (ns=2;i=1)
    │
    ├── Identification/          ◄─── 身份信息 (静态数据)
    │   ├── VendorID                  ns=2;i=3    String
    │   ├── SerialNumber              ns=2;i=4    String
    │   └── ModelName                 ns=2;i=5    String
    │
    ├── State/                   ◄─── 运行状态 (动态数据)
    │   ├── MachineStatus             ns=2;i=7    Int32
    │   └── IsSelected                ns=2;i=8    Boolean
    │
    ├── Process/                 ◄─── 工艺参数 (实时数据)
    │   ├── WaferCount                ns=2;i=10   UInt32
    │   ├── ExposureEnergy            ns=2;i=11   Double
    │   ├── DoseError                 ns=2;i=12   Double
    │   └── OverlayPrecision          ns=2;i=13   Double
    │
    └── Health/                  ◄─── 健康监控 (诊断数据)
        ├── LaserPulseCount           ns=2;i=15   UInt64
        ├── StageVibration            ns=2;i=16   Double
        ├── Temperature               ns=2;i=17   Double
        └── AlarmMessage              ns=2;i=18   String
```

### 3.2 数据节点详细定义

#### 3.2.1 身份信息 (Identification)

| NodeID | 名称 | 类型 | 描述 | 示例值 |
|:-------|:-----|:-----|:-----|:-------|
| `ns=2;i=3` | VendorID | String | 设备制造商标识 | "ASML" |
| `ns=2;i=4` | SerialNumber | String | 设备唯一序列号 | "LM-2024-001" |
| `ns=2;i=5` | ModelName | String | 设备型号名称 | "TWINSCAN NXE:3400C" |

#### 3.2.2 运行状态 (State)

| NodeID | 名称 | 类型 | 描述 | 取值范围 |
|:-------|:-----|:-----|:-----|:---------|
| `ns=2;i=7` | MachineStatus | Int32 | 设备运行状态码 | 0-3 |
| `ns=2;i=8` | IsSelected | Boolean | 设备选中状态 | true/false |

**状态码定义 (MachineStatus)**:

| 值 | 状态 | 说明 | 转换条件 |
|:---|:-----|:-----|:---------|
| 0 | Offline | 离线/关机 | 设备断电或通信中断 |
| 1 | Initial | 初始化中 | 设备启动自检 |
| 2 | Idle | 空闲待机 | 就绪等待任务 |
| 3 | Execute | 运行中 | 正在处理晶圆 |

#### 3.2.3 工艺参数 (Process)

| NodeID | 名称 | 类型 | 单位 | 描述 | 典型范围 |
|:-------|:-----|:-----|:-----|:-----|:---------|
| `ns=2;i=10` | WaferCount | UInt32 | 片 | 已处理晶圆数 | 0 ~ 999999 |
| `ns=2;i=11` | ExposureEnergy | Double | mJ/cm² | 曝光能量密度 | 20.0 ~ 30.0 |
| `ns=2;i=12` | DoseError | Double | % | 剂量误差百分比 | 0.0 ~ 5.0 |
| `ns=2;i=13` | OverlayPrecision | Double | nm | 套刻对准精度 | 0.5 ~ 2.0 |

#### 3.2.4 健康监控 (Health)

| NodeID | 名称 | 类型 | 单位 | 描述 | 监控阈值 |
|:-------|:-----|:-----|:-----|:-----|:---------|
| `ns=2;i=15` | LaserPulseCount | UInt64 | 次 | 激光脉冲计数 | < 10⁹ |
| `ns=2;i=16` | StageVibration | Double | μm | 工台振动幅度 | < 0.1 |
| `ns=2;i=17` | Temperature | Double | °C | 设备温度 | 18 ~ 25 |
| `ns=2;i=18` | AlarmMessage | String | — | 报警信息 | 空=正常 |

### 3.3 NodeID 格式规范

```
ns=<namespace>;<type>=<identifier>
```

| 类型标识 | 说明 | 格式示例 |
|:---------|:-----|:---------|
| `i` | 数字标识符 (Integer) | `ns=2;i=3` |
| `s` | 字符串标识符 (String) | `ns=2;s="Temperature"` |
| `g` | GUID 标识符 | `ns=2;g=12345678-1234-5678-90AB-...` |
| `b` | 字节标识符 (Base64) | `ns=2;b=QWxhcm1EYXRh` |

---

## 4. 通信协议

### 4.1 网络配置

| 配置项 | 值 | 说明 |
|:-------|:---|:-----|
| 协议 | OPC UA Binary / TCP | 二进制编码，高效传输 |
| 端口 | 4840 | OPC UA 标准端口 |
| 端点格式 | `opc.tcp://<host>:4840` | 连接地址模板 |

### 4.2 连接流程

```
┌────────┐                                    ┌────────┐
│ Client │                                    │ Server │
└───┬────┘                                    └───┬────┘
    │                                             │
    │ 1. GetEndpoints Request                     │
    │────────────────────────────────────────────►│
    │                                             │
    │ 2. GetEndpoints Response (安全端点列表)      │
    │◄────────────────────────────────────────────│
    │                                             │
    │ 3. OpenSecureChannel (Basic256Sha256)       │
    │────────────────────────────────────────────►│
    │                                             │
    │ 4. SecureChannel Established                │
    │◄────────────────────────────────────────────│
    │                                             │
    │ 5. CreateSession Request                    │
    │────────────────────────────────────────────►│
    │                                             │
    │ 6. CreateSession Response                   │
    │◄────────────────────────────────────────────│
    │                                             │
    │ 7. ActivateSession (用户名+密码)             │
    │────────────────────────────────────────────►│
    │                                             │
    │ 8. ActivateSession Response                 │
    │◄────────────────────────────────────────────│
    │                                             │
    │ 9. Read/Subscribe 数据操作                   │
    │◄───────────────────────────────────────────►│
    │                                             │
```

### 4.3 数据访问服务

| 服务 | 说明 | 使用场景 |
|:-----|:-----|:---------|
| Read | 同步读取节点值 | 单次/批量数据读取 |
| Write | 写入节点值 | 参数设置 (需写权限) |
| CreateSubscription | 创建数据订阅 | 实时数据推送 |
| CreateMonitoredItems | 添加监控项 | 指定监控节点 |

---

## 5. 安全机制

### 5.1 安全架构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层安全                            │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │   用户认证       │    │   权限控制       │            │
│  │ Username/Password│    │ Read/Write ACL  │            │
│  └─────────────────┘    └─────────────────┘            │
├─────────────────────────────────────────────────────────┤
│                    传输层安全                            │
│  ┌─────────────────┐    ┌─────────────────┐            │
│  │   消息签名       │    │   消息加密       │            │
│  │   RSA-SHA256    │    │   AES-256-CBC   │            │
│  └─────────────────┘    └─────────────────┘            │
├─────────────────────────────────────────────────────────┤
│                    证书体系                              │
│  ┌─────────────────────────────────────────┐           │
│  │        X.509v3 证书 (RSA-2048)           │           │
│  │   Server Cert ◄──────► Client Cert      │           │
│  └─────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────┘
```

### 5.2 安全配置

| 配置项 | 值 | 说明 |
|:-------|:---|:-----|
| 安全策略 | Basic256Sha256 | OPC UA 推荐安全策略 |
| 消息模式 | SignAndEncrypt | 签名 + 加密 |
| 证书规格 | X.509v3 / RSA-2048 | 双向证书认证 |
| 签名算法 | RSA-SHA256 | 消息完整性保护 |
| 加密算法 | AES-256-CBC | 消息机密性保护 |

### 5.3 用户权限

| 用户 | 密码 | 权限级别 | 说明 |
|:-----|:-----|:---------|:-----|
| `admin` | `password123` | 读写 | 管理员权限 |
| `monitor` | `monitor456` | 只读 | 监控权限 |

### 5.4 证书文件

| 文件 | 用途 | 路径 |
|:-----|:-----|:-----|
| server-cert.pem | 服务器证书 | `certs/server-cert.pem` |
| server-key.pem | 服务器私钥 | `certs/server-key.pem` |
| client-cert.pem | 客户端证书 | `certs/client-cert.pem` |
| client-key.pem | 客户端私钥 | `certs/client-key.pem` |

---

## 6. 监控模式

### 6.1 模式对比

| 特性 | 轮询模式 (Poll) | 订阅模式 (Subscription) |
|:-----|:----------------|:------------------------|
| 工作方式 | 客户端定时读取 | 服务器主动推送 |
| 实时性 | 取决于轮询间隔 | 近实时 |
| 网络效率 | 较低 (固定请求) | 较高 (仅变化时传输) |
| 实现复杂度 | 简单 | 较复杂 |
| 适用场景 | 数据变化频率固定 | 数据变化不规律 |

### 6.2 轮询模式 (Poll)

```
┌────────┐                        ┌────────┐
│ Client │                        │ Server │
└───┬────┘                        └───┬────┘
    │                                 │
    │──── Read Request ──────────────►│  t=0
    │◄─── Read Response ──────────────│
    │                                 │
    │         (等待 interval)          │
    │                                 │
    │──── Read Request ──────────────►│  t=interval
    │◄─── Read Response ──────────────│
    │                                 │
    │              ...                │
```

**启动命令**:
```bash
MONITOR_MODE=poll DOTENV_FILE=.env.asml python opc-ua-client.py
```

### 6.3 订阅模式 (Subscription)

```
┌────────┐                        ┌────────┐
│ Client │                        │ Server │
└───┬────┘                        └───┬────┘
    │                                 │
    │── CreateSubscription ──────────►│
    │◄─ Subscription Created ─────────│
    │                                 │
    │── CreateMonitoredItems ────────►│
    │◄─ MonitoredItems Created ───────│
    │                                 │
    │   (服务器检测数据变化)            │
    │                                 │
    │◄──── DataChangeNotification ────│  数据变化时
    │                                 │
    │◄──── DataChangeNotification ────│  数据变化时
    │                                 │
```

**启动命令**:
```bash
MONITOR_MODE=subscription DOTENV_FILE=.env.asml python opc-ua-client.py
```

---

## 7. 部署配置

### 7.1 环境要求

| 组件 | 要求 |
|:-----|:-----|
| Python | 3.9+ |
| 操作系统 | Linux / macOS / Windows |
| 网络 | TCP 4840 端口可访问 |

### 7.2 依赖安装

```bash
pip install -r requirements.txt
```

**核心依赖**:
- `asyncua` - OPC UA 异步库
- `cryptography` - 加密和证书处理
- `python-dotenv` - 环境变量配置

### 7.3 证书生成

```bash
chmod +x gen-certs-openssl.sh
./gen-certs-openssl.sh
```

### 7.4 配置文件

配置文件 `.env.asml` 示例：

```ini
# 连接配置
OPC_ENDPOINT=opc.tcp://localhost:4840
OPC_USERNAME=monitor
OPC_PASSWORD=monitor456
OPC_CLIENT_CERT=certs/client-cert.pem
OPC_CLIENT_KEY=certs/client-key.pem
OPC_TIMEOUT=30
MONITORING_INTERVAL=2

# 命名空间配置
OPC_NAMESPACE=2
DEFAULT_NODE_ID_TYPE=i

# 监控模式
MONITOR_MODE=poll
LOG_LEVEL=INFO
```

### 7.5 启动服务

**启动服务器**:
```bash
python opc-ua-server.py
```

**启动客户端**:
```bash
DOTENV_FILE=.env.asml python opc-ua-client.py
```

---

## 附录

### A. 错误码参考

| 错误码 | 说明 | 处理建议 |
|:-------|:-----|:---------|
| Bad_NodeIdUnknown | 节点不存在 | 检查 NodeID 配置 |
| Bad_NotConnected | 连接断开 | 检查网络，等待重连 |
| Bad_SecurityChecksFailed | 安全验证失败 | 检查证书和密钥 |
| Bad_UserAccessDenied | 用户权限不足 | 检查用户名密码 |

### B. 相关标准

- OPC UA Specification Part 1-14
- SEMI E30 (GEM Standard)
- IEC 62541 (OPC UA)

