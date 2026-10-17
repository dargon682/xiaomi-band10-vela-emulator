#!/usr/bin/env python3
# romfs 解析：打印卷信息、文件/目录清单与目录树。
# 用法：python3 romfs.py <romfs1> [romfs2 ...]
import struct, sys

KIND = {0:'hard',1:'dir',2:'file',3:'sym',4:'blk',5:'chr',6:'sock',7:'fifo'}

def parse(path):
    data = open(path,'rb').read()
    assert data[:8]==b'-rom1fs-'
    total = struct.unpack('>I', data[8:12])[0]
    j = data.index(b'\x00', 16)
    vol = data[16:j].decode('latin1')
    start = (16 + (j-16) + 1 + 15) & ~15
    print(f'volume="{vol}" totalSize={total} fileSize={len(data)} firstInode=0x{start:x}')
    files = []
    dirs = []
    seen = set()

    def read_ino(off):
        f1,f2,f3,f4 = struct.unpack('>IIII', data[off:off+16])
        k = data.index(b'\x00', off+16)
        name = data[off+16:k].decode('latin1','replace')
        return (f1 & ~0xF, f1 & 7, f2, f3, name)

    def is_dir_type(t): return t == 1

    def walk(o, end, path):
        while o and o not in seen and 0 < o < len(data) and o < end:
            seen.add(o)
            nxt, typ, f2, size, name = read_ino(o)
            if name not in ('.','..'):
                full = path + '/' + name
                files.append((full, typ, size))
                if is_dir_type(typ):
                    dirs.append(full)
            nxt_off = nxt if nxt >= o else None
            if is_dir_type(typ) and name not in ('.','..'):
                child_start = (o + 16 + len(name) + 1 + 15) & ~15
                walk(child_start, nxt if nxt > o else end, path + '/' + name)
            if not nxt or nxt <= o or nxt >= len(data):
                break
            o = nxt

    walk(start, len(data), '')
    print(f'files={len(files)} dirs={len(dirs)}')
    for full, typ, size in files:
        if typ == 2 or size > 0:
            print(f'  [{KIND.get(typ,typ)}] {size:>10}  {full}')
    print('--- directories ---')
    for d in dirs:
        print('  ', d)

for p in sys.argv[1:]:
    print('==================', p, '==================')
    try: parse(p)
    except Exception as e:
        import traceback; traceback.print_exc()
