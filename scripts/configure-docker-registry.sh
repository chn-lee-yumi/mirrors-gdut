#!/bin/bash
set -euo pipefail

# ANSI escape codes for colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否以root权限运行
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}请使用sudo运行此脚本${NC}"
    exit 1
fi

# 识别系统发行版
OS_ID=$(grep '^ID=' /etc/os-release | awk -F= '{print $2}' | tr -d '"' | tr '[:upper:]' '[:lower:]')
OS_ID_LIKE=$(grep '^ID_LIKE=' /etc/os-release | awk -F= '{print $2}' | tr -d '"' | tr '[:upper:]' '[:lower:]')

# 特殊处理OpenWrt
if [ -f /etc/openwrt_release ]; then
    OS_ID="openwrt"
fi

# 1. 下载并信任CA证书
echo -e "${GREEN}正在下载CA证书...${NC}"
CA_URL="https://mirrors.gdut.edu.cn/certs/mirrors-ca.crt"

case "$OS_ID" in
    debian|ubuntu)
        CA_DIR="/usr/local/share/ca-certificates/gdut-mirrors"
        UPDATE_CMD="update-ca-certificates"
        ;;
    centos|fedora|rhel|ol)
        CA_DIR="/etc/pki/ca-trust/source/anchors"
        UPDATE_CMD="update-ca-trust"
        ;;
    opensuse*|sles)
        CA_DIR="/etc/pki/trust/anchors"
        UPDATE_CMD="update-ca-trust"
        ;;
    arch|endeavouros|manjaro)
        CA_DIR="/etc/ca-certificates/trust-source/anchors"
        UPDATE_CMD="update-ca-trust"
        ;;
    alpine)
        CA_DIR="/usr/local/share/ca-certificates/gdut-mirrors"
        UPDATE_CMD="update-ca-certificates"
        ;;
    gentoo)
        CA_DIR="/usr/share/ca-certificates/gdut-mirrors"
        UPDATE_CMD="update-ca-certificates"
        ;;
    openwrt)
        CA_DIR="/etc/ssl/certs"
        UPDATE_CMD=""
        echo -e "${YELLOW}OpenWRT需要手动信任证书，请将证书复制到$CA_DIR后执行：${NC}"
        echo -e "ln -sf $CA_DIR/mirrors-ca.crt /etc/ssl/certs/\$(openssl x509 -hash -noout -in $CA_DIR/mirrors-ca.crt).0"
        ;;
    *)
        if [[ "$OS_ID_LIKE" == *"suse"* ]]; then
            CA_DIR="/etc/pki/trust/anchors"
            UPDATE_CMD="update-ca-trust"
        elif [[ "$OS_ID_LIKE" == *"rhel"* ]]; then
            CA_DIR="/etc/pki/ca-trust/source/anchors"
            UPDATE_CMD="update-ca-trust"
        else
            echo -e "${RED}不支持的发行版：$OS_ID${NC}"
            exit 1
        fi
        ;;
esac

mkdir -p "$CA_DIR"
curl -sSL --insecure "$CA_URL" -o "${CA_DIR}/mirrors-ca.crt" || {
    echo -e "${RED}证书下载失败，请检查网络连接${NC}"
    exit 1
}

if [ -n "$UPDATE_CMD" ]; then
    echo -e "${GREEN}正在更新证书信任列表...${NC}"
    $UPDATE_CMD
fi

# 2. 修改hosts文件（通用部分保持不变）
echo -e "${GREEN}正在更新hosts文件...${NC}"
HOSTS_ENTRY='
# GDUT Mirrors Registry
202.116.132.68 docker.registry.gdut.edu.cn
202.116.132.68 ghcr.registry.gdut.edu.cn
202.116.132.68 quay.registry.gdut.edu.cn
202.116.132.68 k8s.registry.gdut.edu.cn
202.116.132.68 mcr.registry.gdut.edu.cn
202.116.132.68 gcr.registry.gdut.edu.cn
202.116.132.68 nvcr.registry.gdut.edu.cn
202.116.132.68 elastic.registry.gdut.edu.cn
# GDUT Mirrors Registry END
'

if ! grep -q "GDUT Mirrors Registry" /etc/hosts; then
    echo "$HOSTS_ENTRY" >> /etc/hosts
    echo -e "${GREEN}hosts文件已更新${NC}"
else
    echo -e "${YELLOW}已存在相关hosts记录，跳过更新${NC}"
fi

# 3. 配置Docker镜像仓库
echo -e "${GREEN}正在配置Docker镜像仓库...${NC}"
DAEMON_CONFIG="/etc/docker/daemon.json"
MIRROR_URL="https://docker.registry.gdut.edu.cn"

# 安装依赖工具
install_deps() {
    case "$OS_ID" in
        debian|ubuntu)
            apt-get update && apt-get install -y curl jq
            ;;
        centos|fedora|rhel|ol)
            yum install -y curl jq
            ;;
        opensuse*|sles)
            zypper -n in curl jq
            ;;
        arch|endeavouros|manjaro)
            pacman -Sy --noconfirm curl jq
            ;;
        alpine)
            apk add curl jq
            ;;
        gentoo)
            emerge -q net-misc/curl app-misc/jq
            ;;
        openwrt)
            opkg update && opkg install curl jq
            if [ $? -ne 0 ]; then
                echo -e "${RED}OpenWRT可能需要手动安装jq，建议参考：${NC}"
                echo "https://openwrt.org/docs/guide-user/additional-software/packages"
                exit 1
            fi
            ;;
        *)
            echo -e "${YELLOW}未知发行版，尝试使用默认包管理器安装...${NC}"
            if command -v apt-get &> /dev/null; then
                apt-get install -y curl jq
            elif command -v yum &> /dev/null; then
                yum install -y curl jq
            elif command -v pacman &> /dev/null; then
                pacman -Sy --noconfirm curl jq
            else
                echo -e "${RED}无法自动安装依赖，请手动安装curl和jq${NC}"
                exit 1
            fi
            ;;
    esac
}

if ! command -v jq &> /dev/null || ! command -v curl &> /dev/null; then
    echo -e "${GREEN}正在安装依赖工具...${NC}"
    install_deps
fi

# 创建配置目录
mkdir -p "$(dirname "$DAEMON_CONFIG")"

# 备份原有配置
if [ -f "$DAEMON_CONFIG" ]; then
    cp "$DAEMON_CONFIG" "${DAEMON_CONFIG}.bak"
    echo -e "${GREEN}已备份原配置文件至 ${DAEMON_CONFIG}.bak${NC}"
fi

# 新版配置函数
configure_daemon() {
    local tmp_file="${DAEMON_CONFIG}.tmp"
    
    # 生成临时配置
    if [ -f "$DAEMON_CONFIG" ]; then
        jq --arg url "$MIRROR_URL" '
        .["registry-mirrors"] = (
            (.["registry-mirrors"] // [])
            | map(select(. != $url))
            | . + [$url]
            | unique
        )' "$DAEMON_CONFIG" > "$tmp_file"
    else
        jq -n --arg url "$MIRROR_URL" \
            '{ "registry-mirrors": [$url] }' > "$tmp_file"
    fi

    # 校验JSON格式
    if jq empty "$tmp_file" 2>/dev/null; then
        mv "$tmp_file" "$DAEMON_CONFIG"
        echo -e "${GREEN}Docker配置更新成功${NC}"
    else
        echo -e "${RED}JSON配置生成失败，保留原有配置${NC}"
        rm -f "$tmp_file"
        exit 1
    fi
}

# 执行配置更新
configure_daemon

# 4. 重启Docker服务
echo -e "${GREEN}正在重启Docker服务...${NC}"
restart_docker() {
    # 检测systemd
    if systemctl --version &> /dev/null; then
        if systemctl is-active docker &> /dev/null; then
            systemctl restart docker
            return $?
        fi
    fi

    # 检测OpenRC
    if rc-service --version &> /dev/null; then
        rc-service docker restart
        return $?
    fi

    # 传统service命令
    if command -v service &> /dev/null; then
        service docker restart
        return $?
    fi

    # OpenWRT特殊情况
    if [ "$OS_ID" == "openwrt" ]; then
        /etc/init.d/docker restart
        return $?
    fi

    echo -e "${RED}无法确定如何重启Docker，请手动执行重启操作${NC}"
    return 1
}

if ! restart_docker; then
    echo -e "${RED}Docker服务重启失败，请检查：${NC}"
    echo "1. Docker是否已安装"
    echo "2. 查看日志：journalctl -u docker.service"
    exit 1
fi

echo -e "${GREEN}所有操作已完成！${NC}"