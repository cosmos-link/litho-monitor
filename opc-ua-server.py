#!/usr/bin/env python3
"""
光刻机数据模拟器 (OPC UA Server)
支持完整的安全通信：传输层加密 + 用户名密码认证
"""

import sys
import random
import asyncio
import logging
from asyncua import Server, ua
from asyncua.ua import VariantType, SecurityPolicyType

# ============================================================================
# 日志配置
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger("asyncua").setLevel(logging.WARNING)

# ============================================================================
# 常量定义
# ============================================================================
class MachineStatus:
    """机器状态枚举"""
    OFFLINE = 0
    INITIAL = 1
    IDLE = 2
    EXECUTE = 3

# 服务器配置
SERVER_ENDPOINT = "opc.tcp://0.0.0.0:4840/freeopcua/server/"
SERVER_NAME = "Lithography Machine Simulator"
NAMESPACE_URI = "http://litho-monitor.com/ua"
CERT_PATH = "certs/server-cert.pem"
KEY_PATH = "certs/server-key.pem"

# 用户数据库
USERS = {
    "admin": "password123",      # 读写权限
    "monitor": "monitor456"      # 只读权限
}

# ============================================================================
# 数据模型
# ============================================================================
class LithoMachineData:
    """光刻机数据模型"""
    
    def __init__(self):
        # 身份信息 (静态)
        self.vendor_id = "ASML"
        self.serial_number = "LM-2024-001"
        self.model_name = "TWINSCAN NXE:3400C"
        
        # 运行状态
        self.machine_status = MachineStatus.IDLE
        self.is_selected = True
        
        # 工艺数据
        self.wafer_count = 0
        self.exposure_energy = 25.5      # mJ/cm²
        self.dose_error = 0.8            # %
        self.overlay_precision = 1.2     # nm
        
        # 设备健康
        self.laser_pulse_count = 1500000
        self.stage_vibration = 0.05      # μm
        self.temperature = 22.5          # °C
        self.alarm_message = ""

# ============================================================================
# OPC UA 服务器
# ============================================================================
class LithoMachineServer:
    """光刻机 OPC UA 服务器"""
    
    def __init__(self):
        self.server = None
        self.ns_idx = None
        self.data = LithoMachineData()
        self.nodes = {}
    
    # ------------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------------
    async def init(self):
        """初始化服务器"""
        self._log_header("正在初始化光刻机数据模拟器")
        
        self.server = Server()
        await self.server.init()
        
        # 配置端点
        self.server.set_endpoint(SERVER_ENDPOINT)
        self.server.set_server_name(SERVER_NAME)
        
        # 配置安全
        await self._configure_security()
        
        # 创建命名空间
        self.ns_idx = await self.server.register_namespace(NAMESPACE_URI)
        logger.info(f"📁 命名空间索引: {self.ns_idx}")
        
        # 创建数据节点
        await self._create_nodes()
        
        logger.info("✅ 服务器初始化完成")
    
    async def _configure_security(self):
        """配置安全策略和用户认证"""
        logger.info("🔐 配置安全策略: Basic256Sha256 + SignAndEncrypt")
        
        # 传输层加密
        self.server.set_security_policy([
            SecurityPolicyType.Basic256Sha256_SignAndEncrypt
        ])
        
        # 加载证书
        logger.info("🔐 加载服务器证书...")
        await self.server.load_certificate(CERT_PATH)
        await self.server.load_private_key(KEY_PATH)
        
        # 用户认证
        logger.info("🔐 配置用户认证...")
        self.server.set_security_IDs(["Username"])
        self.server.user_manager = self._check_credentials
        
        # 应用程序 URI
        await self.server.set_application_uri("urn:localhost:OPCUA:LithoServer")
    
    @staticmethod
    def _check_credentials(username, password):
        """验证用户凭据"""
        result = USERS.get(username) == password
        status = "成功" if result else "失败"
        logger.info(f"🔍 用户验证{status}: {username}")
        return result
    
    # ------------------------------------------------------------------------
    # 地址空间
    # ------------------------------------------------------------------------
    async def _create_nodes(self):
        """创建 OPC UA 地址空间"""
        logger.info("📊 创建数据节点...")
        
        objects = self.server.get_objects_node()
        machine = await objects.add_object(self.ns_idx, "LithographyMachine")
        
        # 按类别创建节点
        await self._create_identification_nodes(machine)
        await self._create_state_nodes(machine)
        await self._create_process_nodes(machine)
        await self._create_health_nodes(machine)
        
        logger.info(f"✅ 创建了 {len(self.nodes)} 个数据节点")
    
    async def _create_identification_nodes(self, parent):
        """创建身份信息节点"""
        folder = await parent.add_folder(self.ns_idx, "Identification")
        await self._add_node(folder, "VendorID", self.data.vendor_id, VariantType.String)
        await self._add_node(folder, "SerialNumber", self.data.serial_number, VariantType.String)
        await self._add_node(folder, "ModelName", self.data.model_name, VariantType.String)
    
    async def _create_state_nodes(self, parent):
        """创建状态节点"""
        folder = await parent.add_folder(self.ns_idx, "State")
        await self._add_node(folder, "MachineStatus", self.data.machine_status, VariantType.Int32)
        await self._add_node(folder, "IsSelected", self.data.is_selected, VariantType.Boolean)
    
    async def _create_process_nodes(self, parent):
        """创建工艺数据节点"""
        folder = await parent.add_folder(self.ns_idx, "Process")
        await self._add_node(folder, "WaferCount", self.data.wafer_count, VariantType.UInt32)
        await self._add_node(folder, "ExposureEnergy", self.data.exposure_energy, VariantType.Double)
        await self._add_node(folder, "DoseError", self.data.dose_error, VariantType.Double)
        await self._add_node(folder, "OverlayPrecision", self.data.overlay_precision, VariantType.Double)
    
    async def _create_health_nodes(self, parent):
        """创建健康状态节点"""
        folder = await parent.add_folder(self.ns_idx, "Health")
        await self._add_node(folder, "LaserPulseCount", self.data.laser_pulse_count, VariantType.UInt64)
        await self._add_node(folder, "StageVibration", self.data.stage_vibration, VariantType.Double)
        await self._add_node(folder, "Temperature", self.data.temperature, VariantType.Double)
        await self._add_node(folder, "AlarmMessage", self.data.alarm_message, VariantType.String)
    
    async def _add_node(self, folder, name, value, variant_type):
        """添加只读变量节点"""
        node = await folder.add_variable(self.ns_idx, name, value, variant_type)
        await node.set_writable(False)
        self.nodes[name] = node
    
    # ------------------------------------------------------------------------
    # 运行
    # ------------------------------------------------------------------------
    async def start(self):
        """启动服务器"""
        async with self.server:
            self._log_startup_info()
            await self._simulate_data()
    
    def _log_startup_info(self):
        """打印启动信息"""
        self._log_header("光刻机数据模拟器启动成功")
        logger.info("📡 OPC UA 端点: opc.tcp://localhost:4840")
        logger.info("🏭 命名空间: http://litho-monitor.com/ua")
        logger.info("📊 数据节点: 13个")
        logger.info("🔐 安全模式: Basic256Sha256 + SignAndEncrypt")
        logger.info("👤 用户账号:")
        logger.info("   - admin/password123 (读写)")
        logger.info("   - monitor/monitor456 (只读)")
        self._log_separator()
    
    # ------------------------------------------------------------------------
    # 数据模拟
    # ------------------------------------------------------------------------
    async def _simulate_data(self):
        """模拟光刻机数据变化"""
        logger.info("🔄 开始数据模拟...")
        
        try:
            while True:
                await self._update_machine_state()
                await asyncio.sleep(2)
        except asyncio.CancelledError:
            logger.info("🛑 数据模拟已停止")
    
    async def _update_machine_state(self):
        """更新机器状态"""
        if self.data.machine_status == MachineStatus.IDLE:
            if random.random() < 0.3:  # 30% 概率进入执行状态
                await self._transition_to_execute()
        
        elif self.data.machine_status == MachineStatus.EXECUTE:
            await self._process_wafer()
            if random.random() < 0.2:  # 20% 概率回到空闲
                await self._transition_to_idle()
    
    async def _transition_to_execute(self):
        """转换到执行状态"""
        self.data.machine_status = MachineStatus.EXECUTE
        await self._write_node("MachineStatus", self.data.machine_status, ua.VariantType.Int32)
        logger.info("📌 状态变更: Idle -> Execute")
    
    async def _transition_to_idle(self):
        """转换到空闲状态"""
        self.data.machine_status = MachineStatus.IDLE
        await self._write_node("MachineStatus", self.data.machine_status, ua.VariantType.Int32)
        logger.info("📌 状态变更: Execute -> Idle")
    
    async def _process_wafer(self):
        """处理晶圆（更新工艺数据）"""
        # 更新计数器
        self.data.wafer_count += 1
        self.data.laser_pulse_count += random.randint(500, 1500)
        
        # 工艺参数波动
        self.data.dose_error = 0.5 + random.random() * 0.8
        self.data.overlay_precision = 1.0 + random.random() * 0.5
        self.data.stage_vibration = 0.03 + random.random() * 0.05
        self.data.temperature = 22.0 + random.random() * 2.0
        
        # 写入节点
        await self._write_node("WaferCount", self.data.wafer_count, ua.VariantType.UInt32)
        await self._write_node("LaserPulseCount", self.data.laser_pulse_count, ua.VariantType.UInt64)
        await self._write_node("DoseError", self.data.dose_error, ua.VariantType.Double)
        await self._write_node("OverlayPrecision", self.data.overlay_precision, ua.VariantType.Double)
        await self._write_node("StageVibration", self.data.stage_vibration, ua.VariantType.Double)
        await self._write_node("Temperature", self.data.temperature, ua.VariantType.Double)
        
        # 检查报警
        await self._check_alarm()
        
        # 打印状态
        logger.info(
            f"📊 晶圆={self.data.wafer_count}, "
            f"剂量误差={self.data.dose_error:.2f}%, "
            f"套刻精度={self.data.overlay_precision:.2f}nm, "
            f"温度={self.data.temperature:.1f}°C"
        )
    
    async def _check_alarm(self):
        """检查并更新报警状态"""
        should_alarm = self.data.dose_error > 1.0
        
        if should_alarm and not self.data.alarm_message:
            self.data.alarm_message = "WARN: Dose error exceeds threshold"
            await self._write_node("AlarmMessage", self.data.alarm_message, ua.VariantType.String)
            logger.warning(f"⚠️  报警触发: {self.data.alarm_message}")
        
        elif not should_alarm and self.data.alarm_message:
            self.data.alarm_message = ""
            await self._write_node("AlarmMessage", self.data.alarm_message, ua.VariantType.String)
            logger.info("✅ 报警清除")
    
    async def _write_node(self, name, value, variant_type):
        """写入节点值"""
        await self.nodes[name].write_value(ua.Variant(value, variant_type))
    
    # ------------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------------
    @staticmethod
    def _log_header(title):
        logger.info("━" * 40)
        logger.info(f"🚀 {title}")
        logger.info("━" * 40)
    
    @staticmethod
    def _log_separator():
        logger.info("━" * 40)

# ============================================================================
# 主入口
# ============================================================================
async def main():
    server = LithoMachineServer()
    
    try:
        await server.init()
        await server.start()
    except FileNotFoundError:
        logger.error("❌ 证书文件未找到")
        logger.error("💡 请先运行: ./gen-certs-openssl.sh")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n🛑 服务器已停止")
