// 创建「小米手环 10 普通版」规格的 VVD（212x520，miwear 镜像）
// 用法：NODE_PATH=<probe>/node_modules node create-band10.js
// 注意：density 传 326 时，生成 config.ini 后需手动改为标准值 320，否则启动报 "Bad LCD density: 326"。
const { VvdManager, VelaImageType, IVvdArchType } = require('@aiot-toolkit/emulator');

const sdkHome = '/root/.vela/sdk';
const vvdHome = '/root/.vela/vvd';
const imageDir = `${sdkHome}/system-images/vela-miwear-watch-5.0`;

const m = new VvdManager({ sdkHome, vvdHome });

const ok = m.createVvd({
  name: 'band10_miwear',
  arch: IVvdArchType.arm,
  width: '212',
  height: '520',
  density: '326',
  customLcdRadius: '90',
  imageType: VelaImageType.VELA_MIWEAR_WATCH_5,
  imageDir,
});

console.log('create band10_miwear =>', ok);
console.log(JSON.stringify(m.getVvdList(), null, 2));
