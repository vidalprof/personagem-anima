#!/usr/bin/env python3
# ============================================================================
# RECORTE AUTOMATICO dos sprites do mundo (base solida p/ a camada pedagogica).
# NAO "chuta" tamanho de celula: DETECTA cada objeto pela borda REAL do desenho
# (ilhas opacas separadas por linhas/colunas vazias) e recorta INTEIRO. Assim
# nunca sai "meia-arvore". Roda local (so corta PNG do kit ja baixado; sem net).
#   Entrada: _anim/assets/mundo/*.png (kit LPC Base Assets, CC0)
#   Saida:   _anim/assets/mundo/cut/*.png (grama, terra, lago, arvore, pinheiro, sombra)
# ============================================================================
import os, glob
import numpy as np
from PIL import Image

RAIZ = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(RAIZ, 'assets', 'mundo')
OUT = os.path.join(SRC, 'cut')
os.makedirs(OUT, exist_ok=True)
A = 20  # limiar de opacidade (alpha) p/ "tem desenho"

def carrega(sufixo):
    f = [x for x in glob.glob(os.path.join(SRC, '*.png')) if x.endswith(sufixo + '.png')]
    if not f:
        raise SystemExit('::error:: nao achei tiles_%s no kit' % sufixo)
    return Image.open(f[0]).convert('RGBA')

def faixas(vazio):
    """dado um vetor booleano 'vazio' por indice, devolve os intervalos NAO-vazios."""
    faixas, ini = [], None
    for i, v in enumerate(vazio):
        if not v and ini is None:
            ini = i
        elif v and ini is not None:
            faixas.append((ini, i)); ini = None
    if ini is not None:
        faixas.append((ini, len(vazio)))
    return faixas

def ilhas(img):
    """segmenta a imagem em ILHAS opacas (objetos), recorta cada uma na borda real."""
    a = np.array(img)[:, :, 3]
    col_vazia = a.max(axis=0) <= A
    out = []
    for x0, x1 in faixas(col_vazia):
        bloco = a[:, x0:x1]
        lin_vazia = bloco.max(axis=1) <= A
        for y0, y1 in faixas(lin_vazia):
            sub = img.crop((x0, y0, x1, y1))
            sub = sub.crop(sub.getbbox())  # aperta na borda exata
            if sub.size[0] > 6 and sub.size[1] > 6:
                out.append(((x0, y0), sub))
    return out

def salva(im, nome):
    im.save(os.path.join(OUT, nome)); print('  %-12s %sx%s' % (nome, im.size[0], im.size[1]))

def main():
    print('== recorte AUTOMATICO (detecta borda real) ==')
    grass = carrega('tiles_grass'); dirt = carrega('tiles_dirt'); water = carrega('tiles_water')
    top = carrega('tiles_treetop'); trunk = carrega('tiles_trunk'); shadow = carrega('UI_shadow')
    TS = 32

    # CHAO/TERRA: celula solida (opacidade cheia) — pega a mais opaca de cada
    def celula_solida(img):
        a = np.array(img)[:, :, 3]; melhor = None; mo = -1
        for cy in range(img.size[1] // TS):
            for cx in range(img.size[0] // TS):
                bloco = a[cy*TS:(cy+1)*TS, cx*TS:(cx+1)*TS]
                op = bloco.mean()
                if op > mo: mo = op; melhor = (cx, cy)
        cx, cy = melhor
        return img.crop((cx*TS, cy*TS, (cx+1)*TS, (cy+1)*TS))
    for i in range(3):  # 3 variantes de grama da linha de baixo (solidas)
        salva(grass.crop((i*TS, 5*TS, (i+1)*TS, 6*TS)), 'grass%d.png' % i)
    salva(celula_solida(dirt), 'dirt.png')

    # LAGO: maior ilha do tileset de agua (pond pronto com margem)
    ag = ilhas(water); ag.sort(key=lambda p: -p[1].size[0]*p[1].size[1])
    salva(ag[0][1], 'pond.png')

    # ARVORES: segmenta o treetop em ilhas; separa REDONDAS (mais largas que altas
    # ou ~quadradas) de PINHEIROS (mais altos que largos). Recorte sempre INTEIRO.
    objs = ilhas(top)
    meio = top.size[1] / 2
    redondas = [(pos, im) for (pos, im) in objs if pos[1] + im.size[1] / 2 < meio]   # copa em CIMA
    pinheiros = [(pos, im) for (pos, im) in objs if pos[1] + im.size[1] / 2 >= meio]  # pinheiro EMBAIXO
    canopy = max(redondas, key=lambda p: p[1].size[0]*p[1].size[1])[1] if redondas else objs[0][1]
    pine = max(pinheiros, key=lambda p: p[1].size[0]*p[1].size[1])[1] if pinheiros else None

    # TRONCO: 1a ilha do tileset de tronco (auto-detectada)
    tks = ilhas(trunk); tks.sort(key=lambda p: p[0][0]); tronco = tks[0][1]

    # compoe a arvore redonda: copa por cima do tronco (centralizado, base embaixo)
    lc, hc = canopy.size; lt, ht = tronco.size
    larg = max(lc, lt); alt = hc + int(ht * 0.7)
    arv = Image.new('RGBA', (larg, alt), (0, 0, 0, 0))
    arv.alpha_composite(tronco, ((larg - lt)//2, alt - ht))     # tronco na base
    arv.alpha_composite(canopy, ((larg - lc)//2, 0))            # copa por cima
    arv = arv.crop(arv.getbbox()); salva(arv, 'tree.png')
    if pine: salva(pine, 'pine.png')

    # SOMBRA: ilha do UI_shadow (a mais 'cheia')
    sh = ilhas(shadow)
    if sh:
        sh.sort(key=lambda p: -np.array(p[1])[:, :, 3].mean()); salva(sh[0][1], 'shadow.png')

    print('== recorte automatico OK ==')

if __name__ == '__main__':
    main()
