#!/usr/bin/env bash
# 一键引导：安装 AIoT-IDE 工具链 + 创建 212x520 手环 10 虚拟设备
# 克隆仓库后执行：  ./scripts/setup.sh
#
# 可配置环境变量：
#   VVD_NAME        虚拟设备名（默认 band10_miwear）
#   VELA_IMAGE_DIR  系统镜像目录（默认 <SDK>/system-images/vela-miwear-watch-5.0）
#   VELA_SDK_HOME   SDK 目录（默认 $HOME/.vela/sdk）
#   VELA_VVD_HOME   VVD 目录（默认 $HOME/.vela/vvd）
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> [1/3] 安装工具链 @aiot-toolkit/emulator（在仓库根目录，供脚本直接 require）"
if [ ! -f package.json ]; then npm init -y >/dev/null 2>&1; fi
npm i

echo "==> [2/3] 创建手环 10 规格 VVD（212x520，miwear 镜像）"
node "$REPO_ROOT/scripts/vvd/create-band10.js"

VVD_NAME="${VVD_NAME:-band10_miwear}"
SDK="${VELA_SDK_HOME:-$HOME/.vela/sdk}"

echo "==> [3/3] 完成。下一步："
cat <<EOF

  1) 首次运行会由工具链联网拉取系统镜像到：$SDK/system-images/
     （若已存在可跳过）

  2) 无界面启动模拟器：
     $SDK/emulator/linux-x86_64/emulator -vela -avd $VVD_NAME -show-kernel -no-window -grpc 8556

  3) 另开终端，用仓库自带 adb 连接 / 安装 / 启动 RPK：
     ./scripts/test-rpk.sh <app.rpk> <package> 8556

  adb 可执行文件位于：$REPO_ROOT/node_modules/@miwt/adb/bin/linux/adb
EOF
