#!/usr/bin/env python3
# 重建模拟器外层容器 vela_system.bin（含 inode 校验和）。
# 原理：romfs inode 校验和 = (0 - Σ(头16B(校验和置零)+文件名+NUL, 大端32位字)) mod 2^32
# 用法：作为库导入，调用 rebuild(template_path, files, out_path)
#   files: [(name, data_bytes), ...]，顺序与容器内原顺序一致（8 个 vela_*.bin）
import struct, sys, os

ALIGN = 16
def align16(n): return (n + 15) & ~15

def be_words(b):
    # 补零到 4 字节整数倍后按大端解包
    pad = (-len(b)) % 4
    b = b + b'\x00' * pad
    return list(struct.unpack('>%dI' % (len(b)//4), b))

def inode_checksum(hdr16):
    # hdr16: inode 头（校验和字段置零）+ 文件名 + NUL 填充
    s = sum(be_words(hdr16)) & 0xffffffff
    return (0x100000000 - s) & 0xffffffff

def build_inode(name, data_size, next_off, type_bits, spec=0):
    nb = name.encode('latin1') + b'\x00'
    hdr = struct.pack('>III', next_off | type_bits, spec, data_size) + b'\x00\x00\x00\x00'
    region = hdr + nb
    chk = inode_checksum(region)
    out = bytearray(struct.pack('>III', next_off | type_bits, spec, data_size) + struct.pack('>I', chk))
    out += nb
    out += b'\x00' * (align16(len(out)) - len(out))
    return bytes(out)

def rebuild(template_path, files, out_path):
    """template: 原始容器；files: 按顺序的 (name, data_bytes)。"""
    t = open(template_path, 'rb').read()
    dotblock = bytes(t[0x00:0x60])   # 前 96 字节：sb(32) + '.'(32) + '..'(32)

    out = bytearray()
    out += dotblock
    assert len(out) == 0x60

    n = len(files)
    for i, (name, data) in enumerate(files):
        nb = name.encode('latin1') + b'\x00'
        entsize = align16(16 + len(nb))
        dstart = len(out) + entsize
        next_off = dstart + len(data)
        type_bits = 2
        if i == n - 1:
            next_off = 0   # 链尾
        ent = build_inode(name, len(data), next_off, type_bits)
        assert len(ent) == entsize
        out += ent
        out += data
        if i != n - 1:
            out += b'\x00' * (align16(len(out)) - len(out))

    # 回写超级块总大小字段 [8:12]
    total = len(out)
    struct.pack_into('>I', out, 8, total)
    open(out_path, 'wb').write(out)
    print('wrote', out_path, 'size', total, hex(total))
    return total

if __name__ == '__main__':
    # 用法示例：读取 extract_container 的输出目录，按原顺序重建
    # python3 build_container.py <template.bin> <parts_dir> <out.bin>
    names = ['vela_misc.bin','vela_quickapp.bin','vela_vendor.bin','vela_i18n.bin',
             'vela_font.bin','vela_system.bin','vela_app.bin','vela_watchface.bin']
    template, partsdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
    files = [(n, open(os.path.join(partsdir, n),'rb').read()) for n in names]
    rebuild(template, files, out)
