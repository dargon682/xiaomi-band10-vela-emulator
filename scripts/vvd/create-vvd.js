// 创建 Vela 虚拟设备（VVD）示例：演示用 createVvd() 自定义任意分辨率
// 用法：node create-vvd.js
// 环境变量：VELA_SDK_HOME、VELA_VVD_HOME、VELA_IMAGE_DIR（默认 vela-watch-5.0）
const { VvdManager, VelaImageType, IVvdArchType } = require('@aiot-toolkit/emulator');
const path = require('path');
const os = require('os');

const HOME = process.env.HOME || os.homedir();
const sdkHome = process.env.VELA_SDK_HOME || path.join(HOME, '.vela', 'sdk');
const vvdHome = process.env.VELA_VVD_HOME || path.join(HOME, '.vela', 'vvd');
const imageDir = process.env.VELA_IMAGE_DIR || path.join(sdkHome, 'system-images', 'vela-watch-5.0');

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
