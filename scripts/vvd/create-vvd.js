// 创建 Vela 虚拟设备（VVD）
// 用法：NODE_PATH=<probe>/node_modules node create-vvd.js
// 说明：手环 10 只是一个 212x520 的圆角屏设备，工具链不区分型号，用 createVvd 自定义尺寸即可。
const { VvdManager, VelaImageType, IVvdArchType } = require('@aiot-toolkit/emulator');

const sdkHome = '/root/.vela/sdk';
const vvdHome = '/root/.vela/vvd';
const imageDir = `${sdkHome}/system-images/vela-watch-5.0`;

const m = new VvdManager({ sdkHome, vvdHome });

const make = (name, w, h, radius) =>
  m.createVvd({
    name,
    arch: IVvdArchType.arm,
    width: String(w),
    height: String(h),
    density: '420',
    customLcdRadius: String(radius),
    imageType: VelaImageType.VELA_WATCH_5,
    imageDir,
  });

console.log('create watch466 =>', make('vela_watch_466', 466, 466, 0));
console.log('create band212  =>', make('band10_212x520', 212, 520, 60));

console.log('--- vvd list ---');
console.log(JSON.stringify(m.getVvdList(), null, 2));
console.log('--- emulator bin ---');
console.log(m.getEmulatorBinPath(sdkHome));
