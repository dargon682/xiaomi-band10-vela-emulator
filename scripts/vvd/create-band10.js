// 创建「小米手环 10 普通版」规格的 VVD（默认 212x520，miwear 镜像）
// 用法：node create-band10.js
// 全部路径/参数均可用环境变量覆盖，便于他人克隆后直接使用：
//   VVD_NAME        虚拟设备名（默认 band10_miwear）
//   VELA_SDK_HOME   SDK 目录（默认 $HOME/.vela/sdk）
//   VELA_VVD_HOME   VVD 目录（默认 $HOME/.vela/vvd）
//   VELA_IMAGE_DIR  系统镜像目录（默认 <SDK>/system-images/vela-miwear-watch-5.0）
//   VVD_WIDTH/HEIGHT/DENSITY/RADIUS  尺寸参数
// 说明：density 传入 326 会被内核拒绝（Bad LCD density），脚本会自动把 config.ini 修正为标准值 320。
const { VvdManager, VelaImageType, IVvdArchType } = require('@aiot-toolkit/emulator');
const fs = require('fs');
const path = require('path');
const os = require('os');

const HOME = process.env.HOME || os.homedir();
const sdkHome = process.env.VELA_SDK_HOME || path.join(HOME, '.vela', 'sdk');
const vvdHome = process.env.VELA_VVD_HOME || path.join(HOME, '.vela', 'vvd');
const name = process.env.VVD_NAME || 'band10_miwear';
const width = process.env.VVD_WIDTH || '212';
const height = process.env.VVD_HEIGHT || '520';
const density = process.env.VVD_DENSITY || '326';   // 手环 10 物理密度
const radius = process.env.VVD_RADIUS || '90';
const lcdDensity = process.env.VVD_LCD_DENSITY || '320'; // 模拟器可接受的标准密度
const imageDir = process.env.VELA_IMAGE_DIR || path.join(sdkHome, 'system-images', 'vela-miwear-watch-5.0');

const m = new VvdManager({ sdkHome, vvdHome });

const ok = m.createVvd({
  name,
  arch: IVvdArchType.arm,
  width,
  height,
  density,
  customLcdRadius: radius,
  imageType: VelaImageType.VELA_MIWEAR_WATCH_5,
  imageDir,
});

console.log(`create ${name} (${width}x${height}, r=${radius}) =>`, ok);

// 修正 config.ini 中的 lcd 密度，避免启动报 "Bad LCD density"
const cfg = path.join(vvdHome, `${name}.vvd`, 'config.ini');
if (fs.existsSync(cfg)) {
  let s = fs.readFileSync(cfg, 'utf8');
  if (/^hw\.lcd\.density=.*$/m.test(s)) {
    s = s.replace(/^hw\.lcd\.density=.*$/m, `hw.lcd.density=${lcdDensity}`);
  } else {
    s += `\nhw.lcd.density=${lcdDensity}\n`;
  }
  fs.writeFileSync(cfg, s);
  console.log(`patched ${cfg}: hw.lcd.density=${lcdDensity}`);
}

console.log(JSON.stringify(m.getVvdList(), null, 2));
