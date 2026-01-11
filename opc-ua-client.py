#!/usr/bin/env python3
"""
光刻机数据监控客户端 (OPC UA Client)
支持传输层加密 + 用户名密码认证
支持轮询和订阅两种监控模式
"""

import sys
import os
import asyncio
import logging
from dotenv import load_dotenv
from asyncua import Client
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from asyncua.ua import MessageSecurityMode

# ============================================================================
# 配置加载
# ============================================================================
class Config:
    """客户端配置"""
    
    def __init__(self):
        self._load_env()
        
        # 连接配置
        self.endpoint = os.getenv('OPC_ENDPOINT', 'opc.tcp://localhost:4840')
        self.username = os.getenv('OPC_USERNAME', 'monitor')
        self.password = os.getenv('OPC_PASSWORD', 'monitor456')
        self.client_cert = os.getenv('OPC_CLIENT_CERT')
        self.client_key = os.getenv('OPC_CLIENT_KEY')
        self.timeout = int(os.getenv('OPC_TIMEOUT', '10'))
        
        # 监控配置
        self.interval = int(os.getenv('MONITORING_INTERVAL', '2'))
        self.mode = os.getenv('MONITOR_MODE', 'poll')  # poll 或 subscription
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # 命名空间配置
        self.namespace = os.getenv('OPC_NAMESPACE', '2')
        self.node_id_type = os.getenv('DEFAULT_NODE_ID_TYPE', 'i')
    
    def _load_env(self):
        """加载环境变量配置文件"""
        dotenv_file = os.getenv('DOTENV_FILE', '.env')
        if os.path.exists(dotenv_file):
            load_dotenv(dotenv_file)
            print(f"📁 已加载配置文件: {dotenv_file}")
        else:
            print(f"⚠️  配置文件不存在: {dotenv_file}，使用默认配置")
    
    def get_node_id(self, node_key, default_value, default_type=None):
        """获取节点ID配置"""
        # 优先使用完整的节点ID
        full_id = os.getenv(f'NODE_{node_key}')
        if full_id:
            return full_id
        
        # 组合配置
        ns = os.getenv(f'{node_key}_NAMESPACE', self.namespace)
        id_type = os.getenv(f'{node_key}_TYPE', default_type or self.node_id_type)
        value = os.getenv(f'{node_key}_VALUE', default_value)
        
        return f'ns={ns};{id_type}={value}'
    
    @property
    def has_certificates(self):
        """检查证书是否存在"""
        return (self.client_cert and self.client_key and
                os.path.exists(self.client_cert) and 
                os.path.exists(self.client_key))

# ============================================================================
# 日志配置
# ============================================================================
config = Config()

logging.basicConfig(
    level=getattr(logging, config.log_level.upper()),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger("asyncua").setLevel(logging.WARNING)

# ============================================================================
# 节点定义
# ============================================================================
NODES = {
    # 身份信息
    'VendorID': config.get_node_id('VENDOR_ID', '3', 'i'),
    'SerialNumber': config.get_node_id('SERIAL_NUMBER', '4', 'i'),
    'ModelName': config.get_node_id('MODEL_NAME', '5', 'i'),
    
    # 运行状态
    'MachineStatus': config.get_node_id('MACHINE_STATUS', '7', 'i'),
    'IsSelected': config.get_node_id('IS_SELECTED', '8', 'i'),
    
    # 工艺数据
    'WaferCount': config.get_node_id('WAFER_COUNT', '10', 'i'),
    'ExposureEnergy': config.get_node_id('EXPOSURE_ENERGY', '11', 'i'),
    'DoseError': config.get_node_id('DOSE_ERROR', '12', 'i'),
    'OverlayPrecision': config.get_node_id('OVERLAY_PRECISION', '13', 'i'),
    
    # 健康状态
    'LaserPulseCount': config.get_node_id('LASER_PULSE_COUNT', '15', 'i'),
    'StageVibration': config.get_node_id('STAGE_VIBRATION', '16', 'i'),
    'Temperature': config.get_node_id('TEMPERATURE', '17', 'i'),
    'AlarmMessage': config.get_node_id('ALARM_MESSAGE', '18', 'i'),
}

# 动态监控的节点列表
DYNAMIC_NODES = [
    'MachineStatus', 'WaferCount', 'DoseError',
    'OverlayPrecision', 'StageVibration', 'Temperature', 'AlarmMessage'
]

# ============================================================================
# 数据格式化
# ============================================================================
class DataFormatter:
    """数据格式化和显示"""
    
    STATUS_MAP = {
        0: 'Offline',
        1: 'Initial', 
        2: 'Idle',
        3: 'Execute',
    }
    
    def __init__(self):
        self.last_alarm = ""
    
    @classmethod
    def status_text(cls, code):
        """状态码转文本"""
        return cls.STATUS_MAP.get(code, f'Unknown({code})')
    
    def print_data(self, data: dict):
        """打印监控数据"""
        if not data:
            return
        
        if 'MachineStatus' in data:
            text = self.status_text(data['MachineStatus'])
            logger.info(f"🔄 [状态] {text} ({data['MachineStatus']})")
        
        if 'WaferCount' in data:
            logger.info(f"📦 [工艺] 已处理晶圆数: {data['WaferCount']}")
        
        if 'DoseError' in data:
            logger.info(f"📊 [工艺] 剂量误差: {data['DoseError']:.2f}%")
        
        if 'OverlayPrecision' in data:
            logger.info(f"📐 [工艺] 套刻精度: {data['OverlayPrecision']:.2f}nm")
        
        if 'StageVibration' in data:
            logger.info(f"📳 [健康] 工台振动: {data['StageVibration']:.3f}μm")
        
        if 'Temperature' in data:
            logger.info(f"🌡️  [健康] 温度: {data['Temperature']:.1f}°C")
        
        if 'AlarmMessage' in data:
            self._handle_alarm(data['AlarmMessage'])
    
    def _handle_alarm(self, alarm):
        """处理报警信息"""
        alarm = str(alarm) if alarm else ""
        
        if alarm and alarm != self.last_alarm:
            logger.warning(f"🚨 [报警] {alarm}")
            self.last_alarm = alarm
        elif not alarm and self.last_alarm:
            logger.info("✅ [报警] 已清除")
            self.last_alarm = ""

# ============================================================================
# 订阅处理器
# ============================================================================
class SubscriptionHandler:
    """订阅模式数据处理器"""
    
    def __init__(self):
        self.data = {}
    
    def datachange_notification(self, node, val, data):
        """数据变化回调"""
        node_id = node.nodeid.to_string()
        
        # 查找节点名称
        for name, nid in NODES.items():
            if nid == node_id:
                self.data[name] = val
                break
    
    def get_and_clear(self):
        """获取数据并清空缓存"""
        data = self.data.copy()
        return data

# ============================================================================
# 监控客户端
# ============================================================================
class LithoMonitorClient:
    """光刻机监控客户端"""
    
    def __init__(self):
        self.client = None
        self.formatter = DataFormatter()
    
    # ------------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------------
    async def connect(self):
        """连接到服务器"""
        self._log_header("正在连接光刻机数据接收器")
        self._log_connection_info()
        
        self.client = Client(url=config.endpoint, timeout=config.timeout)
        
        # 配置安全
        if config.has_certificates:
            await self._configure_security()
        else:
            logger.warning("🔓 证书文件不存在，使用无安全模式连接（仅用于测试）")
        
        # 连接
        logger.info("🔗 正在连接到服务器...")
        await self.client.connect()
        
        self._log_connection_success()
    
    async def disconnect(self):
        """断开连接"""
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("🔌 已断开连接")
            except:
                pass
    
    async def _configure_security(self):
        """配置安全选项"""
        logger.info("🔐 配置传输层加密（Basic256Sha256）...")
        
        await self.client.set_security(
            SecurityPolicyBasic256Sha256,
            certificate=config.client_cert,
            private_key=config.client_key,
            mode=MessageSecurityMode.SignAndEncrypt
        )
        
        if not config.username or not config.password:
            logger.error("❌ 启用安全模式时必须配置用户名和密码")
            sys.exit(1)
        
        logger.info(f"🔐 配置用户名密码认证（用户: {config.username}）...")
        self.client.set_user(config.username)
        self.client.set_password(config.password)
    
    def _log_connection_info(self):
        """打印连接信息"""
        logger.info(f"📍 服务器地址: {config.endpoint}")
        logger.info(f"👤 用户名: {config.username}")
        logger.info(f"⏱️  连接超时: {config.timeout}秒")
        logger.info(f"🔄 监控间隔: {config.interval}秒")
        mode_text = "订阅 (Subscription)" if config.mode == 'subscription' else "轮询 (Polling)"
        logger.info(f"📡 监控模式: {mode_text}")
        self._log_separator()
    
    def _log_connection_success(self):
        """打印连接成功信息"""
        logger.info("✅ 成功连接至光刻机 OPC UA 服务器")
        if config.has_certificates:
            logger.info("🔐 传输层加密: Basic256Sha256 + SignAndEncrypt")
            logger.info(f"🔐 应用层认证: {config.username} 用户")
        else:
            logger.warning("🔓 连接模式: 无安全（测试模式）")
    
    # ------------------------------------------------------------------------
    # 数据读取
    # ------------------------------------------------------------------------
    async def read_identification(self):
        """读取设备身份信息"""
        self._log_separator()
        logger.info("📋 光刻机身份信息:")
        
        for name in ['VendorID', 'SerialNumber', 'ModelName']:
            try:
                node = self.client.get_node(NODES[name])
                value = await node.read_value()
                logger.info(f"   {name}: {value}")
            except Exception as e:
                logger.warning(f"   {name}: 读取失败 ({e})")
        
        self._log_separator()
    
    async def read_dynamic_data(self):
        """读取动态数据"""
        data = {}
        for name in DYNAMIC_NODES:
            try:
                node = self.client.get_node(NODES[name])
                data[name] = await node.read_value()
            except:
                pass
        return data
    
    # ------------------------------------------------------------------------
    # 监控模式
    # ------------------------------------------------------------------------
    async def monitor_polling(self):
        """轮询模式监控"""
        self._log_separator()
        logger.info("📡 开始轮询监控动态数据变化...")
        self._log_separator()
        
        try:
            while True:
                data = await self.read_dynamic_data()
                self.formatter.print_data(data)
                await asyncio.sleep(config.interval)
        except KeyboardInterrupt:
            logger.info("\n🛑 数据接收器已停止")
    
    async def monitor_subscription(self):
        """订阅模式监控"""
        self._log_separator()
        logger.info("📡 开始订阅监控动态数据变化...")
        self._log_separator()
        
        handler = SubscriptionHandler()
        
        # 创建订阅
        subscription = await self.client.create_subscription(
            period=config.interval * 1000,
            handler=handler
        )
        logger.info(f"✅ 订阅已创建 (发布间隔: {config.interval}秒)")
        
        # 订阅节点
        nodes = [self.client.get_node(NODES[name]) for name in DYNAMIC_NODES]
        await subscription.subscribe_data_change(nodes)
        logger.info(f"✅ 已订阅 {len(nodes)} 个数据节点")
        
        self._log_separator()
        logger.info("📡 等待数据变化推送... (按 Ctrl+C 停止)")
        
        try:
            while True:
                await asyncio.sleep(config.interval)
                data = handler.get_and_clear()
                self.formatter.print_data(data)
        except KeyboardInterrupt:
            logger.info("\n🛑 数据接收器已停止")
        finally:
            await subscription.delete()
            logger.info("✅ 订阅已清理")
    
    # ------------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------------
    @staticmethod
    def _log_header(title):
        logger.info("━" * 40)
        logger.info(f"🔌 {title}")
        logger.info("━" * 40)
    
    @staticmethod
    def _log_separator():
        logger.info("━" * 40)

# ============================================================================
# 主入口
# ============================================================================
async def main():
    client = LithoMonitorClient()
    
    try:
        await client.connect()
        await client.read_identification()
        
        if config.mode == 'subscription':
            await client.monitor_subscription()
        else:
            await client.monitor_polling()
    
    except Exception as e:
        logger.error(f"❌ 连接失败: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        sys.exit(1)
    
    finally:
        await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
