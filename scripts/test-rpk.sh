#!/usr/bin/env bash
# RPK 快应用一键测试：push -> pm install -> am start -> gRPC 截图
#
# 用法：
#   ./test-rpk.sh <path/to/app.rpk> <package> [grpc_port] [adb_serial]
# 例：
#   ./test-rpk.sh ./com.bandbbs.ebook.release.3.1.rpk com.bandbbs.ebook 8556
#
# 依赖环境变量（可选，默认按本仓库约定）：
#   PROBE     @aiot-toolkit/emulator 所在 npm 工程目录（默认 /tmp/aiot-probe）
#   SDK_HOME  Vela SDK 目录（默认 /root/.vela/sdk）
set -euo pipefail

RPK="${1:?usage: test-rpk.sh <app.rpk> <package> [grpc_port] [serial]}"
PKG="${2:?usage: test-rpk.sh <app.rpk> <package> [grpc_port] [serial]}"
GRPC_PORT="${3:-8556}"
SERIAL="${4:-}"

PROBE="${PROBE:-/tmp/aiot-probe}"
SDK_HOME="${SDK_HOME:-/root/.vela/sdk}"

ADB="${PROBE}/node_modules/@miwt/adb/bin/linux/adb"
SHOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts/vvd" && pwd)/shot.js"

SERIAL_OPT=()
[ -n "$SERIAL" ] && SERIAL_OPT=(-s "$SERIAL")

echo "==> [1/4] adb push: $RPK"
"$ADB" "${SERIAL_OPT[@]}" push "$RPK" /tmp/app.rpk

echo "==> [2/4] pm install"
"$ADB" "${SERIAL_OPT[@]}" shell "pm install /tmp/app.rpk"

echo "==> [3/4] am start $PKG"
"$ADB" "${SERIAL_OPT[@]}" shell "am start $PKG"
sleep 4

echo "==> [4/4] gRPC screenshot"
OUT="/tmp/vela/${PKG}.png"
mkdir -p /tmp/vela
NODE_PATH="${PROBE}/node_modules" node "$SHOT_DIR" "$GRPC_PORT" "$OUT"

echo "done. screenshot: $OUT"
