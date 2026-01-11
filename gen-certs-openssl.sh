#!/bin/bash

# 生成符合OPC UA规范的证书（使用openssl）

set -e

# 创建certs目录
mkdir -p certs
cd certs

echo "🔐 生成服务器证书..."

# 创建服务器配置文件
cat > server.conf <<EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=CN
ST=Shanghai
L=Shanghai
O=ASML
CN=Lithography Machine Server

[v3_req]
keyUsage = keyEncipherment, digitalSignature, dataEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
URI.1 = urn:localhost:OPCUA:LithoServer
EOF

# 生成服务器私钥和证书
openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout server-key.pem \
    -out server-cert.pem \
    -days 365 \
    -config server.conf \
    -extensions v3_req

echo "🔐 生成客户端证书..."

# 创建客户端配置文件
cat > client.conf <<EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=CN
ST=Shanghai
L=Shanghai
O=ASML
CN=Lithography Machine Client

[v3_req]
keyUsage = keyEncipherment, digitalSignature, dataEncipherment
extendedKeyUsage = serverAuth, clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
IP.2 = ::1
URI.1 = urn:localhost:OPCUA:LithoClient
EOF

# 生成客户端私钥和证书
openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout client-key.pem \
    -out client-cert.pem \
    -days 365 \
    -config client.conf \
    -extensions v3_req

# 清理配置文件
rm server.conf client.conf

cd ..

echo "✅ 证书生成完成！"
echo "📁 证书位置:"
echo "   服务器: certs/server-cert.pem, certs/server-key.pem"
echo "   客户端: certs/client-cert.pem, certs/client-key.pem"
