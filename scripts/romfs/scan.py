#!/usr/bin/env python3
# romfs 结构快速扫描：在前 1KB 内定位 inode 头候选。
# 用法：python3 scan.py <image.bin>
import struct, sys, string

path = sys.argv[1]
data = open(path, 'rb').read()
printable = set(bytes(string.printable, 'ascii')) - set(b'\t\n\r\x0b\x0c')

def is_name(o):
    if o+16 >= len(data): return None
    i = o+16
    j = i
    while j < len(data) and data[j] != 0 and (j-i) < 64:
        if data[j] not in printable: return None
        j += 1
    if j >= len(data) or data[j] != 0: return None
    if j == i: return None
    return data[i:j].decode('ascii')

count = 0
for o in range(0x20, min(len(data), 0x400), 16):
    nm = is_name(o)
    if nm is None: continue
    f = struct.unpack('>IIII', data[o:o+16])
    print(f'off=0x{o:06x}  f1=0x{f[0]:08x}  f2=0x{f[1]:08x}  f3=0x{f[2]:08x}  f4=0x{f[3]:08x}  name={nm!r}')
    count += 1
print('found', count, 'candidate headers in first 1KB')
