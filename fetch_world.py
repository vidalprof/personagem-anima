#!/usr/bin/env python3
# ============================================================================
# MUNDO (tileset SPRITE de verdade, estilo LPC) — roda no GitHub Actions.
# O Marcos NAO quer nada desenhado por codigo: chao, arvores, agua tem que ser
# SPRITE PROFISSIONAL. Baixa o "[LPC] Tile Atlas" (bluecarrot16 / Sharm, CC0/CC-BY)
# do OpenGameArt (raspando a pagina pelo link real do arquivo, adaptativo) e/ou
# fontes espelhadas. Salva PNGs em _anim/assets/mundo/ e escreve o manifest.
# ============================================================================
import os, re, io, sys, zipfile, urllib.request

RAIZ = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(RAIZ, 'assets', 'mundo')
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}

# Paginas do OpenGameArt com o tileset LPC (chao/arvores/agua) — raspa o link real.
PAGINAS = [
    'https://opengameart.org/content/lpc-tile-atlas',      # bluecarrot16 — atlas grande
    'https://opengameart.org/content/lpc-tile-atlas2',     # complemento
    'https://opengameart.org/content/liberated-pixel-cup-lpc-base-assets-sprites-map-tiles',  # Sharm base
    'https://opengameart.org/content/lpc-terrains',        # terrenos LPC (bluecarrot16)
]
# Fontes diretas conhecidas (fallback), tentadas se a raspagem nao achar.
DIRETOS = [
    'https://raw.githubusercontent.com/jrconway3/Universal-LPC-spritesheet/master/misc/tiles.png',
]

def http(url, t=180):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=t).read()

def links_de(pagina):
    html = http(pagina).decode('utf-8', 'ignore')
    achados = re.findall(r'href="([^"]+?\.(?:zip|png))"', html) + re.findall(r"href='([^']+?\.(?:zip|png))'", html)
    norm = []
    for u in achados:
        if u.startswith('//'): u = 'https:' + u
        elif u.startswith('/'): u = 'https://opengameart.org' + u
        if 'sites/default/files' in u and u not in norm:
            norm.append(u)
    return norm

def salva_png(nome, data):
    open(os.path.join(OUT, nome), 'wb').write(data)

def extrai_zip(data, prefixo):
    zf = zipfile.ZipFile(io.BytesIO(data)); n = 0
    for name in zf.namelist():
        if name.lower().endswith('.png') and not name.endswith('/'):
            with zf.open(name) as f:
                salva_png(prefixo + '__' + name.replace('/', '_'), f.read()); n += 1
    return n

def main():
    total = 0
    for pg in PAGINAS:
        nome = pg.rstrip('/').split('/')[-1]
        print('== pagina:', nome, '==')
        try:
            links = links_de(pg)
            print('  arquivos na pagina:', links[:6] if links else 'NENHUM')
            for u in links[:8]:
                try:
                    data = http(u)
                    if len(data) < 800: continue
                    base = u.split('/')[-1]
                    if base.lower().endswith('.zip'):
                        k = extrai_zip(data, nome); print('  zip %s -> %d png' % (base, k)); total += k
                    else:
                        salva_png(nome + '__' + base, data); print('  png %s (%d bytes)' % (base, len(data))); total += 1
                except Exception as e:
                    print('   falhou', u[-60:], str(e)[:80])
        except Exception as e:
            print('  ERRO pagina:', str(e)[:160])
    if total == 0:
        for u in DIRETOS:
            try:
                data = http(u)
                if len(data) > 800:
                    salva_png('direto__' + u.split('/')[-1], data); total += 1; print('  direto OK', u[-50:])
            except Exception as e:
                print('  direto falhou', str(e)[:80])
    arquivos = sorted(os.listdir(OUT))
    open(os.path.join(RAIZ, 'assets', 'manifest-mundo.txt'), 'w').write('total=%d\n' % len(arquivos) + '\n'.join(arquivos))
    print('== TOTAL %d PNG | %s ==' % (total, arquivos[:20]))
    if total == 0:
        print('::error::nenhum tileset baixado'); sys.exit(1)

if __name__ == '__main__':
    main()
