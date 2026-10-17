// 通过 gRPC 获取模拟器状态与截图（PNG）
// 用法：NODE_PATH=<probe>/node_modules node shot.js [grpc_port] [out.png]
// 例：  NODE_PATH=./node_modules node shot.js 8556 /tmp/vela/shot.png
const { createGrpcClient } = require('@aiot-toolkit/emulator/lib/vvd/grpc');
const fs = require('fs');

const port = Number(process.argv[2] || 8554);
const out = process.argv[3] || '/tmp/vela/shot.png';

const client = createGrpcClient({ 'grpc.port': port, 'grpc.token': '' });

(async () => {
  try {
    const status = await client.getStatus();
    console.log('booted=', status.booted, 'version=', status.version);
    const img = await client.getScreenshot(); // RGBA 帧缓冲二进制，落盘即为 PNG
    fs.writeFileSync(out, img);
    console.log('screenshot saved:', out, 'bytes=', img.length);
  } catch (e) {
    console.error('ERR:', e && e.message ? e.message : e);
  } finally {
    client.close();
  }
})();
