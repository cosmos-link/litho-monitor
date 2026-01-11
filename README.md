# 光刻机数据监控系统 (Lithography Machine Monitor)

基于 OPC UA 协议的光刻机实时数据监控系统，支持完整的安全通信（传输层加密 + 用户认证）。

## 🚀 主要特性

- **完整安全支持**：Basic256Sha256 传输加密 + 用户名密码认证
- **实时数据监控**：光刻机状态、工艺参数、健康指标实时监控
- **双监控模式**：支持轮询 (Polling) 和订阅 (Subscription) 两种模式
- **证书管理**：自动生成 X.509 证书支持安全通信
- **生产就绪**：完整的错误处理、日志记录、状态机管理

## 📁 项目结构

```
├── opc-ua-server.py          # OPC UA 服务器（光刻机模拟器）
├── opc-ua-client.py          # OPC UA 客户端（监控端）
├── map_all_nodes.py          # 节点映射和扫描工具
├── requirements.txt          # Python 依赖
├── .env.asml                 # ASML 光刻机配置文件
├── certs/                    # X.509 证书目录
├── gen-certs-openssl.sh      # OpenSSL 证书生成脚本
└── docs/                     # 文档目录
    ├── DESIGN.md             # 设计文档
    └── INTEGRATION_MANUAL.md # 设备对接手册
```

## ⚡ 快速开始

### 1. 环境准备

```bash
# Python 3.9+ 环境
pip install -r requirements.txt
```

### 2. 生成证书

```bash
# 使用 OpenSSL 生成证书
chmod +x gen-certs-openssl.sh
./gen-certs-openssl.sh
```

### 3. 启动服务器

```bash
# 启动 OPC UA 服务器（模拟光刻机）
python3 opc-ua-server.py
```

### 4. 启动监控客户端

```bash
# 轮询模式（默认）
DOTENV_FILE=.env.asml python opc-ua-client.py

# 订阅模式（服务器推送，更实时）
MONITOR_MODE=subscription DOTENV_FILE=.env.asml python opc-ua-client.py

# 环境变量覆盖配置
OPC_ENDPOINT=opc.tcp://192.168.1.100:4840 \
LOG_LEVEL=DEBUG \
python opc-ua-client.py
```

### 5. 监控输出示例

```
🔐 传输层加密: Basic256Sha256 + SignAndEncrypt
🔐 应用层认证: monitor 用户（只读权限）

📋 光刻机身份信息:
   VendorID: ASML
   SerialNumber: LM-2024-001
   ModelName: TWINSCAN NXE:3400C

🔄 [状态] Execute (3)
📦 [工艺] 已处理晶圆数: 123
📊 [工艺] 剂量误差: 1.11%
📐 [工艺] 套刻精度: 1.19nm
📳 [健康] 工台振动: 0.049μm
🌡️  [健康] 温度: 22.9°C
```

## 🔒 安全配置

### 支持的安全策略

- **传输层加密**：Basic256Sha256 + SignAndEncrypt
- **用户认证**：用户名密码认证
- **证书验证**：X.509 证书双向认证

### 用户账户

| 用户名 | 密码 | 权限 |
|--------|------|------|
| admin | password123 | 读写 |
| monitor | monitor456 | 只读 |

### 网络配置

- **端口**：4840 (OPC UA 标准端口)
- **协议**：OPC UA Binary over TCP
- **加密**：TLS 1.2+ with Basic256Sha256

## 📊 监控数据

### 设备身份信息
- 厂商ID (VendorID)
- 设备序列号 (SerialNumber)  
- 型号名称 (ModelName)

### 设备状态
- 机器状态 (Offline/Initial/Idle/Execute)
- 选择状态 (IsSelected)

### 工艺参数
- 已处理晶圆数 (WaferCount)
- 曝光能量 (ExposureEnergy)
- 剂量误差 (DoseError)
- 套刻精度 (OverlayPrecision)

### 健康指标
- 激光脉冲计数 (LaserPulseCount)
- 工台振动 (StageVibration)
- 设备温度 (Temperature)
- 报警信息 (AlarmMessage)

## 🛠️ 技术实现

**核心库**：
- `asyncua`：现代异步 OPC UA 库，完整支持 OPC UA 规范
- `cryptography`：加密和证书处理
- `python-dotenv`：环境变量配置

**特性**：
- ✅ 完整的安全通信支持（传输层加密 + 应用层认证）
- ✅ 支持轮询 (poll) 和订阅 (subscription) 两种监控模式
- ✅ X.509 证书双向认证
- ✅ 异步架构，性能优异

## 🚨 注意事项

1. **必须配置安全通信，禁止无加密连接**
3. **定期更新证书，避免过期**
4. **监控网络连接，确保数据传输稳定**

## 🔧 故障排除

### 连接失败
```bash
# 检查服务器状态
netstat -an | grep 4840

# 检查证书有效期
openssl x509 -in certs/server-cert.pem -text -noout | grep "Not After"
```

### 证书问题
```bash
# 重新生成证书
rm -rf certs/*
./gen-certs-openssl.sh
```

### 数据读取失败
- 确认 NodeID 格式正确：`ns=2;i=<数字ID>`
- 检查用户权限：使用 `monitor` 用户只能读取数据

## 📝 开发说明

### 添加新的监控节点

1. 在服务器中添加新节点：
```python
# 在 LithoMachineServer._create_health_nodes() 中添加
await self._add_node(folder, "NewParameter", 0.0, VariantType.Double)
```

2. 在客户端中添加监控：
```python
# 在 opc-ua-client.py 的 NODES 字典中添加
'NewParameter': config.get_node_id('NEW_PARAMETER', '19', 'i'),
```

### 修改数据模拟

编辑 `LithoMachineServer._process_wafer()` 方法中的业务逻辑，模拟真实的设备数据变化。

## 📄 许可证

MIT License - 详见项目根目录 LICENSE 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request 来改进项目！

---

**推荐配置**：Python 3.9+ + asyncua 库 + OpenSSL 生成的证书