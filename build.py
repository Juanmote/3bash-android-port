#!/usr/bin/env python3
"""Tres-Bashers Android (Ported by Juanmote): parcheador.

Convierte TU copia de la APK oficial de Tres-Bashers (de ondydev) en la version con
traduccion al castellano, controles tactiles, exportar/importar partida, menu de cheats, etc.

Uso:
    python build.py ruta/a/Tres-Bashers.apk

No incluye nada del juego: solo aplica diferencias a tu archivo.
Necesita: Python 3.8+, Java (para firmar la APK) y conexion a internet la primera vez
(descarga UndertaleModCli y uber-apk-signer).
"""
import argparse, hashlib, io, json, os, platform, shutil, stat, subprocess, sys, urllib.request, zipfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
HERR = AQUI / 'herramientas'
TRAB = AQUI / 'trabajo'
UTMT_VER = '0.9.2.0'
UTMT_URL = 'https://github.com/UnderminersTeam/UndertaleModTool/releases/download/%s/UTMT_CLI_v%s-%%s.zip' % (UTMT_VER, UTMT_VER)
SIGNER_URL = 'https://github.com/patrickfav/uber-apk-signer/releases/download/v1.3.0/uber-apk-signer-1.3.0.jar'
# game.droid de la APK oficial sobre el que se hicieron los parches
GAME_DROID_SHA256 = '79734d1d0210e3d621821a51124a0ed4f9080f09e3db2586c044bbac3f2664aa'


def info(m): print('\n== ' + m, flush=True)
def fallo(m): sys.exit('\nERROR: ' + m)


def descargar(url, destino):
    print('   descargando', url)
    req = urllib.request.Request(url, headers={'User-Agent': 'tres-bashers-android'})
    with urllib.request.urlopen(req) as r, open(destino, 'wb') as f:
        shutil.copyfileobj(r, f)


def preparar_utmt():
    sis = platform.system()
    nombre = {'Windows': 'Windows', 'Darwin': 'macOS'}.get(sis, 'Ubuntu')
    exe = HERR / 'utmt' / ('UndertaleModCli.exe' if sis == 'Windows' else 'UndertaleModCli')
    if not exe.exists():
        info('Descargando UndertaleModCli %s' % UTMT_VER)
        (HERR / 'utmt').mkdir(parents=True, exist_ok=True)
        z = HERR / 'utmt.zip'
        descargar(UTMT_URL % nombre, z)
        with zipfile.ZipFile(z) as zf:
            zf.extractall(HERR / 'utmt')
        z.unlink()
        if sis != 'Windows':
            exe.chmod(exe.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    if not exe.exists():
        fallo('No encuentro %s tras descomprimir UndertaleModCli' % exe)
    return exe


def preparar_signer():
    jar = HERR / 'uber-apk-signer.jar'
    if not jar.exists():
        info('Descargando uber-apk-signer')
        HERR.mkdir(parents=True, exist_ok=True)
        descargar(SIGNER_URL, jar)
    return jar


def utmt(exe, *args):
    env = dict(os.environ, DOTNET_SYSTEM_GLOBALIZATION_INVARIANT='1', TB_WORK=str(TRAB))
    r = subprocess.run([str(exe)] + [str(a) for a in args], env=env, stdin=subprocess.DEVNULL,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0 or 'Error' in r.stdout and 'Exception' in r.stdout:
        print(r.stdout[-3000:])
        fallo('UndertaleModCli ha fallado (%s)' % ' '.join(map(str, args[:2])))
    return r.stdout


def aplicar_ops(texto, ops):
    lineas = texto.splitlines(True)
    i = 0
    out = []
    for o, v in ops:
        if o == '=': out += lineas[i:i + v]; i += v
        elif o == '-': i += v
        else: out.append(v)
    assert i == len(lineas)
    return ''.join(out)


def firmar(apk_in, apk_out, jar, ks, clave):
    if shutil.which('java') is None:
        fallo('Hace falta Java para firmar la APK (instala JRE/JDK 11 o superior).')
    carpeta = TRAB / 'firmada'
    if carpeta.exists(): shutil.rmtree(carpeta)
    carpeta.mkdir()
    subprocess.run(['java', '-jar', str(jar), '-a', str(apk_in), '--ks', str(ks), '--ksAlias', 'tbkey',
                    '--ksPass', clave, '--ksKeyPass', clave, '--out', str(carpeta), '--allowResign'], check=True)
    f = [p for p in carpeta.glob('*.apk') if 'Signed' in p.name or 'aligned' in p.name]
    f = sorted(f, key=lambda p: ('Signed' not in p.name, p.name))[0]
    shutil.copy(f, apk_out)


def clave_firma(ruta):
    """Devuelve (keystore, contrasena). Si no existe, crea una (tu propia clave de firma)."""
    ks = Path(ruta)
    pw = ks.with_suffix('.pass')
    if ks.exists() and pw.exists():
        return ks, pw.read_text().strip()
    if shutil.which('keytool') is None:
        fallo('Hace falta Java (keytool) para crear tu clave de firma.')
    clave = hashlib.sha256(os.urandom(32)).hexdigest()[:20]
    ks.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['keytool', '-genkeypair', '-keystore', str(ks), '-storetype', 'PKCS12', '-alias', 'tbkey',
                    '-keyalg', 'RSA', '-keysize', '2048', '-validity', '10000', '-storepass', clave,
                    '-keypass', clave, '-dname', 'CN=Tres-Bashers Android'], check=True, stdout=subprocess.DEVNULL)
    pw.write_text(clave)
    print('   clave de firma nueva creada en', ks, '(guardala: la necesitas para poder actualizar la app sin desinstalar)')
    return ks, clave


def main():
    ap = argparse.ArgumentParser(description='Parchea la APK oficial de Tres-Bashers.')
    ap.add_argument('apk', help='ruta a la APK oficial de Tres-Bashers (ondydev)')
    ap.add_argument('--salida', default=str(AQUI / 'Tres-Bashers_1.2.4_ES.apk'), help='APK final')
    ap.add_argument('--clave', default=str(AQUI / 'mi_clave' / 'clave.p12'), help='keystore (se crea si no existe)')
    ap.add_argument('--forzar', action='store_true', help='seguir aunque el game.droid no sea el esperado')
    a = ap.parse_args()
    apk = Path(a.apk)
    if not apk.exists(): fallo('No existe %s' % apk)

    if TRAB.exists(): shutil.rmtree(TRAB)
    TRAB.mkdir(parents=True)
    exe = preparar_utmt()
    jar = preparar_signer()
    try:
        from PIL import Image
    except ImportError:
        fallo('Falta Pillow: ejecuta  python -m pip install pillow numpy')
    try:
        import numpy  # noqa
    except ImportError:
        fallo('Falta numpy: ejecuta  python -m pip install pillow numpy')

    info('Leyendo la APK oficial')
    zin = zipfile.ZipFile(apk)
    if 'assets/game.droid' not in zin.namelist(): fallo('Esa APK no contiene assets/game.droid (no parece Tres-Bashers).')
    game = TRAB / 'game.droid'
    with zin.open('assets/game.droid') as fi, open(game, 'wb') as fo: shutil.copyfileobj(fi, fo)
    h = hashlib.sha256(game.read_bytes()).hexdigest()
    if h != GAME_DROID_SHA256:
        print('   AVISO: el game.droid no es el de la version esperada. (%s)' % h[:16])
        if not a.forzar:
            fallo('Los parches estan hechos para otra version de la APK. Descarga la APK oficial correcta, o usa --forzar bajo tu riesgo.')

    info('Volcando el codigo del juego (puede tardar un minuto)')
    utmt(exe, 'dump', game, '-o', TRAB / 'dump', '-c', 'UMT_DUMP_ALL')

    info('Aplicando parches al codigo')
    parches = json.load(open(AQUI / 'patch' / 'code.json', encoding='utf-8'))
    (TRAB / 'patched').mkdir()
    for nombre, p in parches.items():
        f = TRAB / 'dump' / 'CodeEntries' / (nombre + '.gml')
        if not f.exists(): fallo('Falta la entrada de codigo %s' % nombre)
        t = open(f, encoding='utf-8', newline='').read()
        if hashlib.sha256(t.encode('utf-8')).hexdigest()[:16] != p['sha']:
            fallo('El codigo original de %s no coincide: version distinta del juego.' % nombre)
        with open(TRAB / 'patched' / (nombre + '.gml'), 'w', encoding='utf-8', newline='') as fo:
            fo.write(aplicar_ops(t, p['ops']))
    print('   %d entradas de codigo modificadas' % len(parches))

    info('Exportando graficos necesarios')
    utmt(exe, 'load', game, '-s', AQUI / 'tools' / 'export.csx')

    info('Dibujando los sprites en castellano')
    subprocess.run([sys.executable, '-I', str(AQUI / 'tools' / 'mk_sprites.py'), str(TRAB)], check=True, stdout=subprocess.DEVNULL)

    info('Aplicando parches graficos (acentos en las fuentes)')
    pix = json.load(open(AQUI / 'patch' / 'pixels.json'))
    for pg, lista in pix.items():
        img = Image.open(TRAB / 'pages' / (pg + '.png')).convert('RGBA')
        px = img.load()
        for x, y, r, g, b, al in lista: px[x, y] = (r, g, b, al)
        img.save(TRAB / 'pages_out' / (pg + '.png'))
    fuentes = json.load(open(AQUI / 'patch' / 'fonts.json'))
    with open(TRAB / 'fonts_add.txt', 'w') as fo:
        for n, d in fuentes.items():
            fo.write('range\t%s\t%d\n' % (n, d['rangeEnd']))
            for g in d['glyphs']: fo.write('glyph\t%s\t%s\n' % (n, '\t'.join(map(str, g))))

    info('Construyendo el nuevo game.droid')
    (TRAB / 'out').mkdir()
    utmt(exe, 'load', game, '-s', AQUI / 'tools' / 'apply_all.csx', '-o', TRAB / 'out' / 'game.droid', '-f')
    if not (TRAB / 'out' / 'game.droid').exists(): fallo('No se genero el game.droid modificado.')

    info('Montando la APK')
    sys.path.insert(0, str(AQUI / 'tools'))
    import axml_patch
    manifest_in = TRAB / 'AndroidManifest.orig.xml'
    manifest_in.write_bytes(zin.read('AndroidManifest.xml'))
    manifest_out = TRAB / 'AndroidManifest.xml'
    axml_patch.main(str(manifest_in), str(manifest_out))
    iconos = {('res/' + p.name): p.read_bytes() for p in (AQUI / 'assets' / 'res').glob('*')}
    sin_firmar = TRAB / 'sin_firmar.apk'
    with zipfile.ZipFile(sin_firmar, 'w') as zo:
        for it in zin.infolist():
            n = it.filename
            if n.startswith('META-INF/'): continue
            if n == 'assets/game.droid':
                zo.write(TRAB / 'out' / 'game.droid', n, compress_type=zipfile.ZIP_STORED)
            elif n == 'AndroidManifest.xml':
                zo.writestr(n, manifest_out.read_bytes(), compress_type=it.compress_type)
            elif n in iconos:
                zo.writestr(n, iconos.pop(n), compress_type=it.compress_type)
            else:
                zo.writestr(zipfile.ZipInfo(n, date_time=(1981, 1, 1, 1, 1, 0)), zin.read(n), compress_type=it.compress_type)
    if iconos: fallo('Faltan estos iconos en la APK oficial: %s' % ', '.join(iconos))

    info('Firmando')
    ks, clave = clave_firma(a.clave)
    firmar(sin_firmar, a.salida, jar, ks, clave)
    print('\nLISTO: %s' % a.salida)
    print('Copia esa APK al movil/consola e instalala. Si ya tenias otra version firmada con otra clave, desinstalala antes.')


if __name__ == '__main__':
    main()
