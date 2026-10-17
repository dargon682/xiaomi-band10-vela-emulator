// 通过 gRPC 向模拟器注入鼠标事件（点击 / 滑动）
// 用法：NODE_PATH=<probe>/node_modules node input.js [grpc_port] <mode> [out.png] [x] [y]
//   mode: tap | swipeup | swipedown | left | right
//   例： node input.js 8556 tap /tmp/t.png 106 288
// 坐标基于 212x520（手环 10 分辨率）。
const { createGrpcClient } = require('@aiot-toolkit/emulator/lib/vvd/grpc');
const fs = require('fs');

const port = Number(process.argv[2] || 8556);
const mode = process.argv[3] || 'swipeup';
const out = process.argv[4] || '/tmp/vela/input_shot.png';

const client = createGrpcClient({ 'grpc.port': port, 'grpc.token': '' });
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  await client.waitForReady();
  const W = 212, H = 520;
  const seq = [];
  if (mode === 'swipeup') {
    // 从底部向上滑，打开应用列表
    for (let i = 0; i <= 20; i++) {
      const y = Math.round(H - 6 - (i / 20) * (H - 140));
      seq.push({ x: Math.round(W / 2), y, buttons: 1 });
    }
  } else if (mode === 'swipedown') {
    for (let i = 0; i <= 20; i++) {
      const y = Math.round(120 + (i / 20) * (H - 200));
      seq.push({ x: Math.round(W / 2), y, buttons: 1 });
    }
  } else if (mode === 'left') {
    for (let i = 0; i <= 20; i++) {
      const x = Math.round(W - 20 - (i / 20) * (W - 40));
      seq.push({ x, y: Math.round(H / 2), buttons: 1 });
    }
  } else if (mode === 'right') {
    for (let i = 0; i <= 20; i++) {
      const x = Math.round(20 + (i / 20) * (W - 40));
      seq.push({ x, y: Math.round(H / 2), buttons: 1 });
    }
  } else if (mode === 'tap') {
    const x = Number(process.argv[5] || W / 2), y = Number(process.argv[6] || H / 2);
    seq.push({ x, y, buttons: 1 });
    seq.push({ x, y, buttons: 0 });
  }
  for (const e of seq) {
    client.sendMouse(e);
    await sleep(30);
  }
  client.sendMouse({ x: seq[seq.length-1].x, y: seq[seq.length-1].y, buttons: 0 });
  await sleep(1200);
  const img = await client.getScreenshot();
  fs.writeFileSync(out, img);
  console.log('saved', out, img.length);
  client.close();
})().catch(e => { console.error('ERR', e.message || e); process.exit(1); });
