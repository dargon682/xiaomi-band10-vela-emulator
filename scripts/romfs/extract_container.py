#!/usr/bin/env python3
# 从模拟器外层容器 vela_system.bin 中提取内嵌的 8 个 romfs 子分区。
# 用法：python3 extract_container.py <vela_system.bin> <outdir>
# 输出：vela_misc.bin / vela_quickapp.bin / vela_vendor.bin / vela_i18n.bin /
#      vela_font.bin / vela_system.bin / vela_app.bin / vela_watchface.bin
import struct, os, sys

def align16(n): return (n + 15) & ~15

def read_root_chain(data):
    j = data.index(b'\x00', 16)
    start = align16(16 + (j - 16) + 1)
    out = []
    o = start
    seen = set()
    while o and o not in seen and o + 16 <= len(data):
        seen.add(o)
        f1, f2, f3, f4 = struct.unpack('>IIII', data[o:o+16])
        k = data.index(b'\x00', o+16)
        name = data[o+16:k].decode('latin1','replace')
        dstart = align16(o+16+len(name)+1)
        out.append((o, f1, f3, name, dstart))
        nxt = f1 & ~0xF
        if nxt == 0 or nxt <= o: break
        o = nxt
    return start, out

def extract(path, outdir):
    data = open(path, 'rb').read()
    os.makedirs(outdir, exist_ok=True)
    start, chain = read_root_chain(data)
    print(f'container vol root @0x{start:x}; entries={len(chain)}')
    for o, f1, size, name, dstart in chain:
        if name in ('.','..'): continue
        blob = data[dstart:dstart+size]
        open(os.path.join(outdir, name),'wb').write(blob)
        print(f'  {name:22s} size={size:>11} data@0x{dstart:08x} magic={blob[:8]!r}')

if __name__ == '__main__':
    extract(sys.argv[1], sys.argv[2])
