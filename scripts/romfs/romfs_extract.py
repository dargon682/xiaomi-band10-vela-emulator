#!/usr/bin/env python3
# romfs 内容提取：把普通文件数据导出到磁盘。
# 用法：python3 romfs_extract.py <romfs.bin> <outdir>
import struct, sys, os

KIND = {0:'hard',1:'dir',2:'file',3:'sym',4:'blk',5:'chr',6:'sock',7:'fifo'}

def parse_and_extract(path, outdir):
    data = open(path,'rb').read()
    assert data[:8]==b'-rom1fs-'
    j = data.index(b'\x00', 16)
    start = (16 + (j-16) + 1 + 15) & ~15
    seen=set(); out=[]
    def read_ino(off):
        f1,f2,f3,f4 = struct.unpack('>IIII', data[off:off+16])
        k = data.index(b'\x00', off+16)
        name = data[off+16:k].decode('latin1','replace')
        return (f1 & ~0xF, f1 & 7, f3, name)
    def walk(o, end, path):
        while o and o not in seen and 0 < o < len(data) and o < end:
            seen.add(o)
            nxt, typ, size, name = read_ino(o)
            if name not in ('.','..'):
                full = path + '/' + name
                out.append((full, typ, size))
                if typ==1:
                    cs = (o+16+len(name)+1+15) & ~15
                    walk(cs, nxt if nxt>o else end, full)
                elif typ==2 and size>0:
                    ds = (o+16+len(name)+1+15) & ~15
                    blob = data[ds:ds+size]
                    dest = outdir + full
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    open(dest,'wb').write(blob)
            if not nxt or nxt<=o or nxt>=len(data): break
            o = nxt
    walk(start, len(data), '')
    return out

if __name__ == '__main__':
    p = sys.argv[1]; o = sys.argv[2]
    os.makedirs(o, exist_ok=True)
    items = parse_and_extract(p, o)
    print(f'{p}: extracted {len(items)} entries to {o}')
    for full, typ, size in items[:20]:
        print(f'  [{KIND.get(typ,typ)}] {size:>10} {full}')
