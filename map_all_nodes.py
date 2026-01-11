#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
from asyncua import Client
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256
from asyncua.ua import MessageSecurityMode

async def main():
    # 加载 .env.asml 配置文件
    load_dotenv('.env.asml')
    
    # 从环境变量读取配置
    OPC_ENDPOINT = 'opc.tcp://127.0.0.1:4840/freeopcua/server/'  # 使用完整的端点URL
    OPC_CLIENT_CERT = os.getenv('OPC_CLIENT_CERT')
    OPC_CLIENT_KEY = os.getenv('OPC_CLIENT_KEY')
    OPC_USERNAME = os.getenv('OPC_USERNAME', 'monitor')
    OPC_PASSWORD = os.getenv('OPC_PASSWORD', 'monitor456')
    OPC_TIMEOUT = int(os.getenv('OPC_TIMEOUT', '30'))
    
    print(f"正在连接到: {OPC_ENDPOINT}")

    client = Client(url=OPC_ENDPOINT, timeout=OPC_TIMEOUT)
    
    try:
        # 服务器只支持Basic256Sha256安全策略，需要使用证书
        if OPC_CLIENT_CERT and OPC_CLIENT_KEY and os.path.exists(OPC_CLIENT_CERT) and os.path.exists(OPC_CLIENT_KEY):
            print("🔐 配置传输层加密...")
            await client.set_security(
                SecurityPolicyBasic256Sha256,
                certificate=OPC_CLIENT_CERT,
                private_key=OPC_CLIENT_KEY,
                mode=MessageSecurityMode.SignAndEncrypt
            )
            client.set_user(OPC_USERNAME)
            client.set_password(OPC_PASSWORD)
        else:
            print("❌ 服务器需要安全证书，但未找到证书文件")
            print("请确保证书文件存在，或者使用支持无安全模式的服务器")
            return
        
        await client.connect()
        print("✅ 成功连接到服务器")
    except Exception as e:
        print(f"连接失败: {e}")
        return
    
    print("🔍 映射所有命名空间2的数字节点...")
    
    # 从i=1扫描到i=20，找到所有节点
    for i in range(1, 21):
        node_id = f'ns=2;i={i}'
        try:
            node = client.get_node(node_id)
            value = await node.read_value()
            display_name = await node.read_display_name()
            data_type = await node.read_data_type()
            print(f"✅ {node_id}: {display_name.Text} = {value} ({data_type})")
        except Exception:
            pass  # 忽略不存在的节点
    
    await client.disconnect()

asyncio.run(main())