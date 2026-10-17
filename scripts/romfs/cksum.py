#!/usr/bin/env python3
# inode 校验和算法逆向探针：对已知 inode 多个候选算法打分，找出命中算法。
# 用法：修改下方 data 路径与 samples（off, namePadLen, targetChecksum）后运行。
# 结论：校验和 = (0 - Σ(大端32位字)) mod 2^32，覆盖范围 = 头16B（校验和字段置零）+ 文件名 + NUL。
import struct

data = open('/tmp/fw/emu_container/vela_system.bin','rb').read()
samples = [
    (0x20, 16, 0xd1ffff97),   # "."
    (0x40, 16, 0xd1d1ff80),   # ".."
    (0x60, 16, 0x153243e3),   # "whatsapp"
]

def rol(x,n): return ((x<<n)|(x>>(32-n)))&0xffffffff
def ror(x,n): return ((x>>n)|(x<<(32-n)))&0xffffffff

algos = {
 'ror_add': lambda s,w: (ror(s,1)+w)&0xffffffff,
 'rol_add': lambda s,w: (rol(s,1)+w)&0xffffffff,
 'add_ror': lambda s,w: ror((s+w)&0xffffffff,1),
 'add_rol': lambda s,w: rol((s+w)&0xffffffff,1),
 'xor_ror': lambda s,w: ror(s^w,1),
 'xor_rol': lambda s,w: rol(s^w,1),
 'sum_add': lambda s,w: (s+w)&0xffffffff,
 'xor':     lambda s,w: (s^w)&0xffffffff,
 'shl_add': lambda s,w: ((s<<1)+w)&0xffffffff,
 'shr_add': lambda s,w: ((s>>1)+w)&0xffffffff,
}

def calc(words, algo):
    s=0
    for w in words: s=algos[algo](s,w)
    return s

targets = []
for off,padlen,t in samples:
    targets.append((off,padlen,t,t))
    targets.append((off,padlen,t,struct.unpack('<I',struct.pack('>I',t))[0]))

hits=[]
for off,padlen,t_be,t in targets:
    for zero_from in (0,4,8,12):   # 从该字节起清零（校验和字段）
        blob=bytearray(data[off:off+16+padlen])
        if zero_from<=12<=zero_from+3:
            blob[12:16]=b'\x00\x00\x00\x00'
        for startb in range(0,17,4):
            for nbytes in range(4, 16+padlen+1-startb, 4):
                raw=bytes(blob[startb:startb+nbytes])
                if len(raw)<nbytes: continue
                for endian in ('>','<'):
                    words=list(struct.unpack(endian+('I'*(nbytes//4)), raw))
                    for a in algos:
                        if calc(words,a)==t:
                            hits.append((hex(off),hex(t),startb,nbytes,endian,a,zero_from))
seen=set()
for h in hits:
    key=(h[0],h[2],h[3],h[4],h[5])
    if key in seen: continue
    seen.add(key)
    print('MATCH off=%s target=%s startByte=%d nbytes=%d endian=%s algo=%s zeroFrom=%d'%h)
print('unique matches:', len(seen))
