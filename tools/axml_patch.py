#!/usr/bin/env python3
"""Edita el AndroidManifest.xml binario (AXML) de la APK oficial.

Uso: axml_patch.py entrada.xml salida.xml

Cambios:
  - versionName 1.2.3 -> 1.2.4 y versionCode 1002003 -> 1002011
  - permiso BLUETOOTH -> MANAGE_EXTERNAL_STORAGE (para exportar/importar partidas .sav)
  - OrientPortrait y OrientPortraitFlipped = 0 (el juego se fuerza en horizontal)
"""
import struct, sys

STR_REPLACE = {
    '1.2.3': '1.2.4',
    'android.permission.BLUETOOTH': 'android.permission.MANAGE_EXTERNAL_STORAGE',
}
VERSION_CODE = (0xf4a13, 0xf4a1b)
ZERO_METADATA = ('OrientPortrait', 'OrientPortraitFlipped')


def read_pool(d, sp=8):
    t, hs, sz, sc, stc, fl, ss, sts = struct.unpack('<HHIIIIII', d[sp:sp + 28])
    assert t == 1 and not fl & 0x100 and stc == 0, 'formato de manifiesto no esperado'
    offs = struct.unpack('<%dI' % sc, d[sp + 28:sp + 28 + 4 * sc])
    strs = []
    for o in offs:
        p = sp + ss + o
        l = struct.unpack('<H', d[p:p + 2])[0]
        assert l < 0x8000
        strs.append(d[p + 2:p + 2 + 2 * l].decode('utf-16le'))
    return strs, sz


def build(d, strs, sz, sp=8):
    data = b''
    noffs = []
    for s in strs:
        noffs.append(len(data))
        data += struct.pack('<H', len(s)) + s.encode('utf-16le') + b'\0\0'
    while len(data) % 4:
        data += b'\0'
    sc = len(strs)
    hdr = 28 + 4 * sc
    pool = struct.pack('<HHIIIIII', 1, 28, hdr + len(data), sc, 0, 0, hdr, 0) + struct.pack('<%dI' % sc, *noffs) + data
    rest = d[sp + sz:]
    return bytearray(struct.pack('<HHI', 3, 8, 8 + len(pool) + len(rest)) + pool + rest)


def main(src, dst):
    d = open(src, 'rb').read()
    strs, sz = read_pool(d)
    for a, b in STR_REPLACE.items():
        assert strs.count(a) == 1, (a, strs.count(a))
        strs[strs.index(a)] = b
    d = build(d, strs, sz)
    strs, sz = read_pool(bytes(d))
    pos = 8 + sz
    done = []
    while pos < len(d):
        ct, chs, csz = struct.unpack('<HHI', d[pos:pos + 8])
        if ct == 0x0102:
            ns, name, attrStart, attrSize, attrCount = struct.unpack('<iiHHH', d[pos + 16:pos + 30])
            ab = pos + 16 + attrStart
            attrs = {}
            for k in range(attrCount):
                a = ab + k * 20
                ans, aname, raw, sz2, res0, dtype, data = struct.unpack('<iiiHBBi', d[a:a + 20])
                attrs[strs[aname]] = (a, raw, dtype, data)
            tag = strs[name]
            if tag == 'manifest' and 'versionCode' in attrs:
                a, raw, dtype, data = attrs['versionCode']
                assert data == VERSION_CODE[0], 'versionCode inesperado: %x' % data
                struct.pack_into('<i', d, a + 16, VERSION_CODE[1]); done.append('versionCode')
            if tag == 'meta-data' and 'name' in attrs and attrs['name'][1] >= 0 and strs[attrs['name'][1]] in ZERO_METADATA:
                a = attrs['value'][0]
                struct.pack_into('<i', d, a + 16, 0); done.append(strs[attrs['name'][1]])
        pos += csz
    assert sorted(done) == sorted(['versionCode'] + list(ZERO_METADATA)), done
    open(dst, 'wb').write(d)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
