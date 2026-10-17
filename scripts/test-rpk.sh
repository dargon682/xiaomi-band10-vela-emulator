#!/usr/bin/env bash
# RPK 快应用一键测试：push -> pm install -> am start -> gRPC 截图
#
# 用法：
#   ./test-rpk.sh <path/to/app.rpk> <package> [grpc_port] [adb_serial]
# 例：
#   ./test-rpk.sh ./com.bandbbs.ebook.release.3.1.rpk com.bandbbs.ebook 8556
#
# 依赖环境变量（可选）：
#   PROBE     @aiot-toolkit/emulator 所在 npm 工程目录（默认=仓库根目录，先跑 ./scripts/setup.sh）
#   SERIAL    adb 设备号（默认不指定，自动选择唯一设备）
set -euo pipefail

RPK="${1:?usage: test-rpk.sh <app.rpk> <package> [grpc_port] [serial]}"
PKG="${2:?usage: test-rpk.sh <app.rpk> <package> [grpc_port] [serial]}"
GRPC_PORT="${3:-8556}"
SERIAL="${4:-}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE="${PROBE:-$REPO_ROOT}"

ADB="${PROBE}/node_modules/@miwt/adb/bin/linux/adb"
SHOT_DIR="${REPO_ROOT}/scripts/vvd/shot.js"
if [ ! -x "$ADB" ]; then
  echo "错误：未找到工具链 adb（$ADB）。请先执行 ./scripts/setup.sh" >&2
  exit 1
fi

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
