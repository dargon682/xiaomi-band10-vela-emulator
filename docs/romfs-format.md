# romfs 容器 / 分区格式（逆向说明）

> 适用于 Vela / openvela（NuttX）手环固件的资源分区，以及模拟器 `vela_system.bin` 外层容器。
> 以下结论由二进制逆向 + 实测重建验证得出。

## 1. 超级块（Superblock）

镜像起始处：

| 偏移 | 长度 | 含义 |
|------|------|------|
| `0x00` | 8 | magic `-rom1fs-` |
| `0x08` | 4 | 大端总大小（字节）|
| `0x0C` | 4 | 校验和（可忽略/重建时重算）|
| `0x10` | var | 卷名，NUL 结尾 |
| … | pad | `align16(16 + len(volname) + 1)` 对齐后即首个 inode 偏移 |

```python
assert data[:8] == b'-rom1fs-'
total = struct.unpack('>I', data[8:12])[0]
j = data.index(b'\x00', 16)
first_inode = (16 + (j-16) + 1 + 15) & ~15   # align16
```

## 2. inode 结构

每个 inode = **16 字节头** + **NUL 结尾文件名** + 对齐填充 + 数据。

头部为 4 个**大端** 32 位整数 `f1 f2 f3 f4`：

```
f1 = next_offset | type_bits      # next：下一个 inode 的绝对偏移；低 4 位 = 类型
f2 = spec                         # 文件/设备号等信息（普通文件可 0）
f3 = size                         # 数据长度（字节）
f4 = checksum                     # inode 校验和
```

**类型**（`f1 & 7`）：

| 值 | 类型 |
|----|------|
| 0 | hard link |
| 1 | **目录** |
| 2 | **普通文件** |
| 3 | 符号链接 |
| 4/5/6/7 | 块/字符设备/套接字/FIFO |

**遍历规则**：

- 目录链：从父目录 inode 头之后 `align16` 的位置开始，沿 `next` 逐条走。
- `next = f1 & ~0xF`，为**绝对偏移**；`next == 0` 表示链结束。
- 目录的数据区（`[16 + len(name) + 1]` 对齐后）即**子 inode 链的起点**。
- `.` 与 `..` 为前两条特殊条目。

## 3. inode 校验和（重建关键）

设校验和字段**置零**，取 `[头 16B + 文件名 + NUL]`，按 4 字节**大端**拆成 32 位字求和，
则：

```
checksum = (0 - Σ(words)) mod 2^32
```

实现（见 `scripts/romfs/build_container.py`）：

```python
def inode_checksum(hdr16):
    s = sum(be_words(hdr16)) & 0xffffffff
    return (0x100000000 - s) & 0xffffffff
```

> 说明：`be_words` 会先把输入补零到 4 字节整数倍再按大端解包；
> 该公式对 `.`、`..` 以及普通文件 inode 均已实测命中。

## 4. 模拟器外层容器

`vela_system.bin` 是**外层 romfs 容器**，根目录直接挂着 8 个文件
（对应真机 OTA 的 8 个分区，均为独立 romfs 镜像）：

```
vela_misc.bin  vela_quickapp.bin  vela_vendor.bin  vela_i18n.bin
vela_font.bin  vela_system.bin    vela_app.bin     vela_watchface.bin
```

布局：

```
0x00 : superblock(32) + '.' inode(32) + '..' inode(32)   # 共 0x60 字节
0x60 : 第 1 个文件 inode（16B 头 + 名 + 对齐）
       └─ 紧随其后是该文件数据
       之后 align16，接第 2 个文件 …
```

- 文件条目的 `next` 指向**下一个 inode 头**的绝对偏移，最后一个为 0。
- 重建时按顺序拼接 `(name, data)`，并回写超级块 `[8:12]` 的总大小字段。

重建函数签名：

```python
build_container.rebuild(template_path, files, out_path)
# files: [(name, data_bytes), ...]  顺序与容器内原顺序一致
```

## 5. 提取与重建脚本

| 脚本 | 作用 |
|------|------|
| `scan.py` | 快速定位 inode 头候选（前 1KB） |
| `romfs.py` | 打印目录树 / 文件清单 |
| `romfs_extract.py` | 把文件数据导出到磁盘 |
| `cksum.py` | 校验和算法逆向探针（多算法打分） |
| `extract_container.py` | 从 `vela_system.bin` 抽出 8 个子分区 |
| `build_container.py` | 由 8 个子分区重建外层容器 |
