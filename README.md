# 小米手环 10 普通版 Vela 模拟器 · 搭建与 RPK / 表盘测试指南

> 在 **无官方手环 10 镜像** 的前提下，用 AIoT-IDE（Vela / openvela）模拟器 + **真机固件分区替换** 的方式，
> 把小米手环 10 普通版（212×520）跑起来，并完成第三方 RPK 快应用与表盘的安装 / 启动 / 交互测试。
>
> 本文档为实机踩坑总结，所有命令与脚本均在 Linux x86_64 沙箱环境实测通过。

---

## 目录

- [0. 结论速览](#0-结论速览)
- [1. 环境准备](#1-环境准备)
- [2. Vela SDK 与镜像布局](#2-vela-sdk-与镜像布局)
- [3. 创建手环规格虚拟设备（VVD）](#3-创建手环规格虚拟设备vvd)
- [4. 启动无界面模拟器](#4-启动无界面模拟器)
- [5. gRPC 截图与触摸交互](#5-grpc-截图与触摸交互)
- [6. 用真机固件分区适配模拟器（进阶核心）](#6-用真机固件分区适配模拟器进阶核心)
- [7. RPK 快应用测试流程](#7-rpk-快应用测试流程)
- [8. 表盘（Watchface）测试与黑屏问题](#8-表盘watchface测试与黑屏问题)
- [9. 常见报错与解决（FAQ）](#9-常见报错与解决faq)
- [10. 脚本清单与仓库结构](#10-脚本清单与仓库结构)
- [11. 免责声明](#11-免责声明)

---

## 0. 结论速览

| 目标 | 可行性 | 关键手段 |
|------|--------|----------|
| 手环 10 规格虚拟设备（212×520） | ✅ | `VvdManager.createVvd()` 自定义宽高/圆角/密度 |
| 无界面运行 + 截图 | ✅ | `emulator -no-window -grpc <port>` + gRPC `getScreenshot()` |
| 触摸 / 滑动交互 | ✅ | gRPC `sendMouse()` 合成手势序列 |
| 安装并运行第三方 RPK | ✅ | `pm install` + `am start <package>` |
| 运行手环 10 真机固件分区 | ✅ | 解析并替换模拟器容器内嵌 romfs 分区 |
| 手环 10 真机表盘渲染 | ✅（需 hack） | 表盘目录 ID 别名到内核写死的默认 ID + 重算 inode 校验和 |

> 一句话：**模拟器内核是通用的，手环 10 的差异全在“资源分区”里**。
> 把真机 OTA 包里的 romfs 分区替换进模拟器容器，就能得到接近真机的手环 10 环境。

---

## 快速开始

克隆后三步即可用（路径已全部改为可配置，无需改脚本）：

```bash
git clone https://github.com/dargon682/xiaomi-band10-vela-emulator.git
cd xiaomi-band10-vela-emulator

# 1) 一键引导：安装工具链 + 创建 212x520 手环 10 虚拟设备
./scripts/setup.sh

# 2) 无界面启动模拟器（首次会联网拉取系统镜像）
$HOME/.vela/sdk/emulator/linux-x86_64/emulator \
  -vela -avd band10_miwear -show-kernel -no-window -grpc 8556

# 3) 另开终端，测试 RPK 快应用
./scripts/test-rpk.sh <your-app.rpk> <package> 8556
```

> 克隆仓库**只含脚本与文档**（不含工具链二进制 / 系统镜像 / 固件，也无版权风险）。
> 工具链与镜像由 `setup.sh` / 首次启动时联网获取。

### 环境变量（可选，用于覆盖默认路径）

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `VELA_SDK_HOME` | `$HOME/.vela/sdk` | SDK 目录 |
| `VELA_VVD_HOME` | `$HOME/.vela/vvd` | 虚拟设备目录 |
| `VELA_IMAGE_DIR` | `<SDK>/system-images/vela-miwear-watch-5.0` | 系统镜像目录 |
| `VVD_NAME` | `band10_miwear` | 虚拟设备名 |
| `VVD_WIDTH`/`HEIGHT`/`RADIUS` | `212`/`520`/`90` | 屏幕参数 |
| `PROBE` | 仓库根目录 | 工具链所在 npm 工程 |

---

## 1. 环境准备

- 操作系统：Linux x86_64
- Node.js ≥ 16（实测 v24）
- 具备访问镜像下载源的网络（沙箱内通过 `HTTP_PROXY/HTTPS_PROXY` 代理）
- Git

安装模拟器工具链（提供 VVD 管理、镜像下载、gRPC 客户端、内置 adb）：

```bash
# 在仓库根目录安装（推荐）：脚本即可直接 require，无需 NODE_PATH
npm i
```

> 也可单独建工程：`mkdir -p aiot-probe && cd aiot-probe && npm i @aiot-toolkit/emulator`，
> 此时运行脚本需指定 `PROBE=/path/to/aiot-probe` 或 `NODE_PATH=/path/to/aiot-probe/node_modules`。

`@aiot-toolkit/emulator` 内各模块的用途：

| 模块路径 | 用途 |
|----------|------|
| `@aiot-toolkit/emulator` | 导出 `VvdManager`、`VelaImageType`、`IVvdArchType` |
| `.../lib/vvd/grpc` | `createGrpcClient()`，用于截图 / 输入 |
| `.../lib/instance/miwear.js` | `MiwearInstance`，封装 `install` / `startApp` |
| `@miwt/adb/bin/linux/adb` | 随工具链分发的 adb 可执行文件 |

> 环境变量 `NODE_PATH=<probe>/node_modules` 可以让放在任意目录的脚本也能 `require` 到该包（见脚本示例）。

---

## 2. Vela SDK 与镜像布局

首次使用工具链后，SDK 落在 `~/.vela`：

```
~/.vela/
├── sdk/
│   ├── emulator/linux-x86_64/          # emulator 入口 + qemu 二进制
│   │   ├── emulator                    # 启动入口（wrapper）
│   │   └── qemu/linux-x86_64/          # qemu-system-armel(-headless) 等
│   └── system-images/
│       ├── vela-watch-5.0/             # 基础手表镜像
│       └── vela-miwear-watch-5.0/      # miwear 手表镜像（自带表盘/launcher）★推荐
└── vvd/                                # 虚拟设备（AVD）配置目录
    ├── <name>.ini                      # AVD 元数据
    └── <name>.vvd/                     # AVD 实体（config.ini、镜像、userdata…）
```

**关键选择**：使用 `vela-miwear-watch-5.0` 镜像。
`vela-watch-5.0` 启动后常见黑屏且无 launcher，`miwear` 版自带表盘与启动器，适合手环。

每个 system-image 目录核心文件：

```
vela_system.bin     # 系统镜像（外层 romfs 容器）
vela_data.bin       # 数据分区模板（首次启动用作 userdata）
nuttx/              # 内核等
advancedFeatures.ini
```

---

## 3. 创建手环规格虚拟设备（VVD）

工具链不区分设备型号，**手环 10 只是一个 212×520 的圆角屏设备**，用 `createVvd()` 自定义即可。

参考 [scripts/vvd/create-band10.js](scripts/vvd/create-band10.js)：

```js
const { VvdManager, VelaImageType, IVvdArchType } = require('@aiot-toolkit/emulator');
const m = new VvdManager({ sdkHome: '/root/.vela/sdk', vvdHome: '/root/.vela/vvd' });

m.createVvd({
  name: 'band10_miwear',
  arch: IVvdArchType.arm,
  width: '212', height: '520',
  density: '326',            // 手环 10 物理密度；见下方注意事项
  customLcdRadius: '90',     // 圆角半径（手环为长圆角矩形）
  imageType: VelaImageType.VELA_MIWEAR_WATCH_5,
  imageDir: '/root/.vela/sdk/system-images/vela-miwear-watch-5.0',
});
```

生成的 `~/.vela/vvd/band10_miwear.vvd/config.ini` 关键项：

```ini
hw.lcd.width=212
hw.lcd.height=520
hw.lcd.density=320            # ★ 326 会被内核拒绝，必须改成标准值 320
ide.lcd.radius=90
ide.image.type=vela-miwear-watch-5.0
image.sysdir.2=/root/.vela/sdk/system-images/vela-miwear-watch-5.0
fastboot.forceColdBoot=yes
```

> **注意**：`hw.lcd.density` 直接写 `326` 启动会报 `Bad LCD density: 326`，
> 模拟器只接受标准密度值（本环境验证 `320` 可用）。

---

## 4. 启动无界面模拟器

模拟器启动入口是 `~/.vela/sdk/emulator/linux-x86_64/emulator`。

**无界面 + gRPC 控制**（推荐，适合 CI / 沙箱）：

```bash
/root/.vela/sdk/emulator/linux-x86_64/emulator \
  -vela -avd band10_miwear \
  -show-kernel -no-window \
  -grpc 8556
```

完整的实测启动参数（`emu-launch-params.txt`）还包含音频与网络转发：

```
-qemu -device virtio-snd,bus=virtio-mmio-bus.2 -allow-host-audio -semihosting
-network-user-mode-options hostfwd=tcp:127.0.0.1:10057-10.0.2.15:101
```

启动后：

- NuttX 内核引导 → LVGL 帧缓冲初始化 → NSH 提示符 → `Boot completed`
- gRPC 监听 `8556`（截图 / 输入）
- adb 自动出现设备 `emulator-5554`

adb 连接与常用管理命令：

```bash
ADB=<probe>/node_modules/@miwt/adb/bin/linux/adb
$ADB devices                       # 应看到 emulator-5554  device
$ADB -s emulator-5554 shell "pm list"
$ADB -s emulator-5554 shell "am start <package>"
$ADB -s emulator-5554 shell "am stop  <package>"
```

> **首次启动报错 `Could not open userdata-qemu.img`**：
> 把镜像目录下的 `vela_data.bin` 复制为 AVD 目录下的 `userdata-qemu.img` 即可：
> `cp <imageDir>/vela_data.bin ~/.vela/vvd/<name>.vvd/userdata-qemu.img`

---

## 5. gRPC 截图与触摸交互

模拟器内置 gRPC 服务，无需窗口即可截图和注入输入事件。

### 截图 [scripts/vvd/shot.js](scripts/vvd/shot.js)

```js
const { createGrpcClient } = require('@aiot-toolkit/emulator/lib/vvd/grpc');
const client = createGrpcClient({ 'grpc.port': 8556, 'grpc.token': '' });
const status = await client.getStatus();          // { booted, version }
const png = await client.getScreenshot();          // RGBA 二进制，直接落盘为 PNG
```

### 触摸 / 滑动 [scripts/vvd/input.js](scripts/vvd/input.js)

`client.sendMouse({ x, y, buttons })`，`buttons=1` 按下、`0` 抬起。
连续点列即滑动；单点按下+抬起即点击：

```js
// 点击 (58,38)
client.sendMouse({ x: 58, y: 38, buttons: 1 });
client.sendMouse({ x: 58, y: 38, buttons: 0 });
```

脚本内置 `tap / swipeup / swipedown / left / right` 手势模式，坐标基于 212×520。

---

## 6. 用真机固件分区适配模拟器（进阶核心）

> 目标：让模拟器运行 **手环 10 真机固件**，从而获得一致的资源、应用与表盘。

### 6.1 固件包结构

手环 10 固件（本环境为 `o66` / 版本 3.1.16）是标准 **OTA 分区包**，
各分区（misc / quickapp / vendor / i18n / font / system / app / watchface）均为 **romfs** 格式。

### 6.2 模拟器容器镜像结构

`vela_system.bin` 本身是一个**外层 romfs 容器**，内部**内嵌 8 个 romfs 子分区**，
与真机 OTA 分区一一对应，因此**资源可互换**：

```
vela_system.bin (外层 romfs 容器)
├── vela_misc.bin
├── vela_quickapp.bin
├── vela_vendor.bin
├── vela_i18n.bin
├── vela_font.bin
├── vela_system.bin        # 系统分区
├── vela_app.bin
└── vela_watchface.bin     # 表盘分区
```

### 6.3 romfs 格式要点（逆向总结）

详见 [docs/romfs-format.md](docs/romfs-format.md)。核心：

- 超级块：magic `-rom1fs-`，`[8:12]` 为大端总大小，`[16:]` 为卷名（NUL 结尾），
  其后 `align16` 对齐即首个 inode 偏移。
- inode：16 字节头 `>IIII` = `next|type, spec, size, checksum`，
  - `next` 为**下一个 inode 的绝对偏移**，低 4 位是**类型**（1 目录 / 2 文件）；
  - 头后紧跟 NUL 结尾文件名，`align16` 后为数据。
- **inode 校验和**（重建必备）：
  令校验和字段置零，对 `[头16B + 文件名 + NUL]` 按 4 字节对齐后的大端 32 位字求和，
  则 `checksum = (0 - sum) mod 2^32`。

对应实现见 [scripts/romfs/build_container.py](scripts/romfs/build_container.py) 的
`inode_checksum()` 与 `build_inode()`。

### 6.4 操作流程

1. **提取模拟器容器内的 8 个子分区**
   `python3 scripts/romfs/extract_container.py <vela_system.bin> <outdir>`
2. **从真机固件中解出对应分区**（romfs 解析）
   `python3 scripts/romfs/romfs.py` / `romfs_extract.py` 查看与提取
3. **替换目标分区**（如 system / app / watchface 等）
4. **重建外层容器**
   `python3 scripts/romfs/build_container.py`（用 `rebuild(template, files, out)`，
   `files` 为按顺序的 `(name, bytes)`，脚本会写回超级块总大小字段）
5. 用新容器替换 AVD 目录下的 `vela_system.bin`，冷启动模拟器

> 校验和算法逆向用的探针脚本：[scripts/romfs/cksum.py](scripts/romfs/cksum.py)，
> 结构扫描：[scripts/romfs/scan.py](scripts/romfs/scan.py)。

### 6.5 分区替换后的黑屏陷阱

全量替换手环 10 分区后可能**黑屏**。原因：**模拟器内核写死了默认表盘 ID `120917345469`**，
而手环 10 真机表盘 ID 为 `12091735xxx`，内核找不到默认表盘 → 黑屏。

**解决**：把某个手环 10 表盘目录**重命名别名**成内核写死的 ID，并**重算该目录 inode 校验和**，
表盘即可正常渲染（见第 8 节）。

---

## 7. RPK 快应用测试流程

### 7.1 RPK 包结构

RPK 本质是 zip 归档：

```
manifest.json      # package / name / versionName / versionCode / deviceType / designWidth / router
pages/             # 页面（UX 文件）
app.jsc            # 编译后的 JS 字节码
common/ i18n/      # 资源、多语言
META-INF/          # 签名
```

手环应用关键字段（以实测电子书为例）：

```json
{
  "package": "com.bandbbs.ebook",
  "name": "电子书",
  "versionName": "3.1",
  "minPlatformVersion": 1100,
  "deviceTypeList": ["watch"],
  "config": { "designWidth": 212 }        // ★ 与手环 212px 宽度一致，布局才不错位
}
```

### 7.2 安装与启动

```bash
ADB=<probe>/node_modules/@miwt/adb/bin/linux/adb
$ADB -s emulator-5554 push com.bandbbs.ebook.release.3.1.rpk /tmp/ebook.rpk
$ADB -s emulator-5554 shell "pm install /tmp/ebook.rpk"      # 安装
$ADB -s emulator-5554 shell "am start com.bandbbs.ebook"     # 启动
$ADB -s emulator-5554 shell "am stop  com.bandbbs.ebook"     # 停止
```

`pm` / `am` 用法：

```
pm <install|uninstall> [packagename|rpkfile]
am <start|stop> packagename
```

安装后：

- 应用落在 `/data/app/<package>/`
- 注册进 `/data/quickapp/apps.json` 的 `InstalledApps`（供 launcher 展示图标）

### 7.3 一键测试脚本

[scripts/test-rpk.sh](scripts/test-rpk.sh)：

```bash
./scripts/test-rpk.sh <path/to/app.rpk> <package> [grpc_port]
# 例：
./scripts/test-rpk.sh ./com.bandbbs.ebook.release.3.1.rpk com.bandbbs.ebook 8556
```

脚本流程：push → `pm install` → `am start` → 等待 → gRPC 截图。

### 7.4 实测结果（电子书 com.bandbbs.ebook 3.1）

| 环节 | 结果 |
|------|------|
| 安装 | ✅ 落盘 `/data/app/com.bandbbs.ebook/`，含 manifest / pages / app.jsc |
| 清单兼容 | ✅ `designWidth: 212` 与手环 212px 匹配，`deviceType: watch` |
| 启动 | ✅ `am start` 拉起 JS 虚拟机，入口 `pages/index` 渲染「书架空空」 |
| 交互 | ✅ 点击「…」展开设置菜单 → 进入「字号」子页，路由跳转正常 |

截图见 [screenshots/](screenshots/)。

---

## 8. 表盘（Watchface）测试与黑屏问题

- 真机表盘位于外层容器的 `vela_watchface.bin` 子分区内，每条表盘是一个目录（以数字 ID 命名）。
- 模拟器内核**写死默认表盘 ID**，找不到即黑屏。
- 适配手法：
  1. 在表盘子分区内定位任意手环 10 表盘目录；
  2. 将该目录**重命名为内核默认 ID**（本环境为 `120917345469`）；
  3. **重算该目录 inode 的校验和**（`build_container.inode_checksum`），否则 romfs 校验失败；
  4. 重建外层容器 → 冷启动 → 表盘正常渲染。

---

## 9. 常见报错与解决（FAQ）

| 报错 / 现象 | 原因 | 解决 |
|-------------|------|------|
| `Could not open userdata-qemu.img: No such file or directory` | AVD 缺数据分区 | 复制 `vela_data.bin` → `userdata-qemu.img` |
| 启动后黑屏、无 launcher | 用了 `vela-watch-5.0` | 换 `vela-miwear-watch-5.0` 镜像 |
| `Bad LCD density: 326` | 内核拒绝非标准密度 | `hw.lcd.density` 改为 `320` |
| 全量替换手环 10 分区后黑屏 | 内核默认表盘 ID 与真机不符 | 表盘目录 ID 别名 + 重算校验和（第 8 节） |
| romfs 目录遍历异常 | inode 字段偏移/next 指针掩码理解错 | `next` 低 4 位为类型、高位为绝对偏移 |
| `require('@aiot-toolkit/emulator/...')` 找不到 | 未安装工具链或脚本不在工程内 | 在仓库根执行 `npm i`（或设 `PROBE` / `NODE_PATH`） |
| `find` / `cat /proc/...` 在 NSH 不可用 | NuttX NSH 命令子集有限 | 用 `ls` / 内置 `pm` / `am` |
| adb 未安装 | 环境无 system adb | 用工具链自带 `@miwt/adb/bin/linux/adb` |

---

## 10. 脚本清单与仓库结构

```
.
├── README.md
├── LICENSE
├── package.json                     # 依赖 @aiot-toolkit/emulator（供脚本 require）
├── docs/
│   └── romfs-format.md              # romfs 容器/分区格式与校验和逆向说明
├── scripts/
│   ├── setup.sh                     # 一键引导：装工具链 + 建 212x520 手环 VVD
│   ├── vvd/
│   │   ├── create-vvd.js            # 创建基础/手环规格 VVD
│   │   ├── create-band10.js         # 创建 212×520 手环 10 VVD
│   │   ├── shot.js                  # gRPC 截图
│   │   └── input.js                 # gRPC 触摸/滑动手势
│   ├── romfs/
│   │   ├── scan.py                  # romfs 结构扫描探针
│   │   ├── romfs.py                 # romfs 解析/列目录树
│   │   ├── romfs_extract.py         # romfs 内容提取
│   │   ├── cksum.py                 # inode 校验和算法逆向探针
│   │   ├── extract_container.py     # 从外层容器提取 8 个子分区
│   │   └── build_container.py       # 重建外层容器（含校验和）
│   └── test-rpk.sh                  # RPK 一键安装/启动/截图
└── screenshots/                     # 实测截图
```

---

## 11. 免责声明

- 本文档为**技术研究与学习**用途，涉及对官方固件/镜像格式的**逆向分析**，
  相关固件、镜像、RPK 的版权归各自权利人所有，**请勿分发固件本体**。
- 仓库内只包含**脚本与文档**，不包含任何厂商固件 / 镜像 / 应用二进制。
- 操作真机固件存在风险，请自行评估。
