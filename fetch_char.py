#!/usr/bin/env python3
# ============================================================================
# PERSONAGEM LPC universal (13 col, 832x1344) — baixa CORPO + ROUPA + CABELO e
# COMPOE o heroi (assets/hero.png). Roda no GitHub Actions (internet liberada).
# Regra do Marcos: nada "no olho" — o CABELO é DESCOBERTO pela API do GitHub
# (acha o caminho real do arquivo), nunca chutado. Se o cabelo falhar, o heroi
# sai sem cabelo (nao quebra), e o log diz exatamente o que aconteceu.
# ============================================================================
import os, sys, json, urllib.request
from PIL import Image

RAIZ = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(RAIZ, 'assets', 'images')
os.makedirs(IMG, exist_ok=True)
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
REPO = 'sanderfrenken/Universal-LPC-Spritesheet-Character-Generator'
RAW = 'https://raw.githubusercontent.com/%s/master/spritesheets/' % REPO
API = 'https://api.github.com/repos/%s/contents/spritesheets/' % REPO

def http(u, t=120):
    return urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=t).read()

def baixa(nome, urls):
    for u in urls:
        try:
            d = http(u)
            if len(d) > 500:
                open(os.path.join(IMG, nome + '.png'), 'wb').write(d)
                print('OK %s <- %s (%d bytes)' % (nome, u.split('/spritesheets/')[-1], len(d))); return True
        except Exception as e:
            print('  falhou', u.split('/spritesheets/')[-1], str(e)[:80])
    return False

def api(path):
    return json.loads(http(API + path))

def descobre_png(path, prefere=('black', 'brown', 'male'), prof=0):
    """DFS na API ate achar um .png; prefere caminhos com 'male'/cor. Sem chute."""
    if prof > 5:
        return None
    try:
        itens = api(path)
    except Exception as e:
        print('  API falhou em', path, str(e)[:60]); return None
    pngs = [i for i in itens if i.get('type') == 'file' and i['name'].endswith('.png')]
    if pngs:
        for k in prefere:
            for p in pngs:
                if k in p['path'].lower():
                    return p['download_url']
        return pngs[0]['download_url']
    dirs = [i for i in itens if i.get('type') == 'dir']
    dirs.sort(key=lambda d: 0 if any(k in d['name'].lower() for k in ('plain', 'male', 'adult', 'black')) else 1)
    for d in dirs:
        u = descobre_png(d['path'], prefere, prof + 1)
        if u:
            return u
    return None

def main():
    # 1) CORPO (masculino, universal) — URLs conhecidas boas
    baixa('lpc_body', [
        RAW + 'body/bodies/male/universal.png',
        RAW + 'body/bodies/male/light.png',
    ])
    # 2) ROUPA (camisa longa branca)
    baixa('lpc_torso', [
        RAW + 'torso/clothes/longsleeve/longsleeve/male/white.png',
        RAW + 'torso/clothes/longsleeve/male/white.png',
    ])
    # 2b) CALCA (pra nao ficar de pernas de fora)
    baixa('lpc_legs', [
        RAW + 'legs/pants/male/blue.png',
        RAW + 'legs/pants/pants/male/blue.png',
    ])
    # 3) CABELO — DESCOBERTO pela API (nada chutado)
    print('== descobrindo o caminho do CABELO pela API ==')
    hair_url = None
    for base in ['hair/plain', 'hair/messy1', 'hair']:
        hair_url = descobre_png(base)
        if hair_url:
            print('  cabelo achado:', hair_url.split('/master/')[-1]); break
    if hair_url:
        baixa('lpc_hair', [hair_url])

    # 4) COMPOE o heroi: corpo -> calca -> roupa -> cabelo
    def carrega(n):
        p = os.path.join(IMG, n + '.png')
        return Image.open(p).convert('RGBA') if os.path.exists(p) else None
    corpo = carrega('lpc_body')
    if not corpo:
        print('::error::sem corpo, nao da pra compor'); sys.exit(1)
    heroi = corpo.copy()
    # As camadas LPC alinham no topo-esquerda (mesmas animacoes na mesma ordem).
    # Camada menor cobre so as 1as linhas (onde esta o ANDAR) — encaixa no (0,0).
    for camada in ['lpc_legs', 'lpc_torso', 'lpc_hair']:
        c = carrega(camada)
        if c and c.size[0] == heroi.size[0]:
            heroi.alpha_composite(c, (0, 0)); print('  + camada %s %s' % (camada, c.size))
        elif c:
            print('  ! %s largura %s != %s, pulei' % (camada, c.size[0], heroi.size[0]))
    saida = os.path.join(RAIZ, 'assets', 'hero.png')
    heroi.save(saida)
    print('== hero.png composto:', heroi.size, ('COM cabelo' if carrega('lpc_hair') else 'SEM cabelo'), '==')

if __name__ == '__main__':
    main()
